import pandas as pd
import logging
import os
from typing import Optional, Dict, Any, List


# Logging configuration
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class AlarmCleaner:
    """A data cleansing engine for SCADA alarm datasets.

    This class provides a pipeline to handle duplicates, normalize timestamps 
    across multiple formats, sanitize categorical data, and validate 
    domain-specific logic for industrial alarms.

    Attributes:
        file_path (str): The path to the raw CSV data file.
        df (Optional[pd.DataFrame]): The internal container for the alarm data.
        severity_map (Dict[str, str]): Mapping for normalizing severity labels.
        status_map (Dict[str, str]): Mapping for normalizing alarm status labels.
    """

    def __init__(self, file_path: str):
        """Initializes the AlarmCleaner with file paths and normalization maps.

        Args:
            file_path (str): Path to the source CSV file.
        """
        self.file_path = file_path
        self.df: Optional[pd.DataFrame] = None

        self.severity_map = {
            'high': 'HIGH', 'h': 'HIGH',
            'med': 'MEDIUM', 'medium': 'MEDIUM',
            'low': 'LOW', 'l': 'LOW'
        }

        self.status_map = {
            'active': 'ACTIVE',
            'cleared': 'CLEARED',
            'ack': 'ACKNOWLEDGED',
            'acknowledged': 'ACKNOWLEDGED'
        }

    def _add_quality_flag(self, condition: pd.Series, flag_name: str) -> None:
        """Appends a quality flag to records that meet a specific condition.

        If a record already has an existing flag, the new flag is appended 
        with a pipe separator.

        Args:
            condition (pd.Series): A boolean mask identifying rows to flag.
            flag_name (str): The label to assign to the quality_flag column.
        """
        is_ok_mask = self.df['quality_flag'] == "OK"

        # Update records that were previously marked as 'OK'
        self.df.loc[condition & is_ok_mask, 'quality_flag'] = flag_name
        
        # Append flags to records that already had quality issues
        self.df.loc[condition & ~is_ok_mask, 'quality_flag'] = (
            self.df['quality_flag'] + '| ' + flag_name
        )

    def load_data(self) -> None:
        """Loads data from the source file and initializes the quality tracking column.

        Raises:
            FileNotFoundError: If the source CSV file does not exist.
        """
        logging.info("Loading data from %s", self.file_path)
        self.df = pd.read_csv(self.file_path)
        self.df['quality_flag'] = 'OK'

    def handle_duplicates(self) -> None:
        """Identifies duplicate records based on core alarm identity columns.

        Marks rows as 'DUPLICATE' if they share the same timestamp, tag, 
        and description.
        """
        logging.info("Detecting duplicate records...")

        duplicate_mask = self.df.duplicated(
            subset=["timestamp", "tag", "severity", "value", "status"],
            keep=False
        )

        self._add_quality_flag(duplicate_mask, 'DUPLICATE')
        logging.info("Duplicates detected: %d", duplicate_mask.sum())

    def clean_timestamps(self) -> None:
        """Normalizes timestamps using a multi-format parsing strategy.

        Attempts to parse date strings using several common industrial and 
        regional formats. Records that fail all parsing attempts are 
        flagged as 'INVALID_TIMESTAMP'.
        """
        logging.info("Normalizing timestamps with multi-format strategy...")

        self.df['timestamp_raw'] = self.df['timestamp']
        
        # Priority-ordered list of expected formats
        date_formats: List[Optional[str]] = [
            "%Y-%m-%d %H:%M:%S",   # ISO-like
            "%d/%m/%Y %H:%M",      # Latino / European
            "%b %d, %Y %I:%M %p",  # North American
            None                   # Pandas inference (ISO8601 fallback)
        ]

        cleaned_timestamps = pd.Series(pd.NaT, index=self.df.index)

        for fmt in date_formats:
            pending_mask = cleaned_timestamps.isna()
            if not pending_mask.any():
                break
                
            current_format_name = fmt if fmt else 'Auto-inference'
            logging.info(f"Attempting parsing with format: {current_format_name}")
            
            parsed_values = pd.to_datetime(
                self.df.loc[pending_mask, 'timestamp_raw'],
                format=fmt,
                errors='coerce'
            )
            cleaned_timestamps.update(parsed_values)

        self.df['timestamp'] = cleaned_timestamps

        invalid_ts_mask = self.df['timestamp'].isna()
        self._add_quality_flag(invalid_ts_mask, 'INVALID_TIMESTAMP')

        logging.info("Timestamp normalization completed. Invalid count: %d", 
                     invalid_ts_mask.sum())

    def clean_numeric_values(self) -> None:
        """Sanitizes numerical columns and validates physical constraints.

        Handles decimal formatting issues (commas vs points) and flags 
        out-of-range or non-numeric values.
        """
        logging.info("Cleaning numeric values...")

        # Convert strings to numeric, handling common decimal separator noise
        self.df['value'] = self.df['value'].astype(str).str.replace(',', '.', regex=True)
        self.df['value'] = pd.to_numeric(self.df['value'], errors='coerce')

        invalid_value_mask = self.df['value'].isna()
        self._add_quality_flag(invalid_value_mask, 'INVALID_VALUE')

        # Domain constraint: Value should not be negative in this context
        negative_value_mask = self.df['value'] < 0
        self._add_quality_flag(negative_value_mask, 'OUT_OF_RANGE')

        logging.info("Numeric cleaning completed. Invalids: %d", 
                     invalid_value_mask.sum())

    def normalize_categories(self) -> None:
        """Standardizes categorical columns based on internal mapping dictionaries.

        Processes 'severity', 'status', and 'tag' columns to ensure 
        consistency and handle missing labels.
        """
        logging.info("Normalizing categorical data...")

        # Severity normalization
        self.df['severity'] = (
            self.df['severity']
            .astype(str)
            .str.lower()
            .str.strip()
            .map(self.severity_map)
        )
        invalid_sev_mask = self.df['severity'].isna()
        self.df['severity'] = self.df['severity'].fillna('UNKNOWN')
        self._add_quality_flag(invalid_sev_mask, 'INVALID_SEVERITY')

        # Status normalization
        self.df['status'] = (
            self.df['status']
            .astype(str)
            .str.lower()
            .str.strip()
            .map(self.status_map)
        )
        invalid_status_mask = self.df['status'].isna()
        self.df['status'] = self.df['status'].fillna('UNKNOWN')
        self._add_quality_flag(invalid_status_mask, 'INVALID_STATUS')

        # Tag cleaning
        self.df['tag'] = (
            self.df['tag']
            .fillna('UNKNOWN_TAG')
            .replace('', 'UNKNOWN_TAG')
        )

    def clean_description(self) -> None:
        """Sanitizes the alarm description column.

        Handles nulls and trims whitespace to ensure uniform text data.
        """
        logging.info("Sanitizing alarm descriptions...")

        self.df['description'] = (
            self.df['description']
            .fillna('NO_DESCRIPTION')
            .replace('', 'NO_DESCRIPTION')
            .astype(str)
            .str.strip()
        )

    def validate_scada_logic(self) -> None:
        """Validates logical coherence between different alarm attributes.

        Flags inconsistencies such as active alarms missing a sensor value 
        or high-severity alarms with null data.
        """
        logging.info("Validating logical consistency...")

        # Case 1: Active status without a numeric reading
        active_no_value_mask = (
            (self.df['status'] == 'ACTIVE') &
            (self.df['value'].isna())
        )
        self._add_quality_flag(active_no_value_mask, 'INCONSISTENT_ACTIVE_NO_VALUE')

        # Case 2: High severity alarm without data (Critical issue)
        high_no_value_mask = (
            (self.df['severity'] == 'HIGH') &
            (self.df['value'].isna())
        )
        self._add_quality_flag(high_no_value_mask, 'CRITICAL_NO_VALUE')

    def generate_quality_report(self) -> Dict[str, Any]:
        """Calculates quality metrics for the processed dataset.

        Returns:
            Dict[str, Any]: A dictionary containing total rows, flag 
                distribution, and null counts per column.
        """
        logging.info("Generating data quality report...")

        return {
            "total_rows": len(self.df),
            "quality_distribution": self.df['quality_flag'].value_counts().to_dict(),
            "null_summary": self.df.isna().sum().to_dict()
        }

    def run_pipeline(self, output_path: Optional[str] = None) -> pd.DataFrame:
        """Executes the full cleaning and validation sequence.

        Args:
            output_path (str): The destination file path for the cleaned CSV.

        Returns:
            pd.DataFrame: The processed and flagged DataFrame.
        """
        self.load_data()

        # Step-by-step processing
        self.handle_duplicates()
        self.clean_timestamps()
        self.clean_numeric_values()
        self.normalize_categories()
        self.clean_description()
        self.validate_scada_logic()

        # Reporting and Persistence
        quality_report = self.generate_quality_report()
        logging.info("Quality Report: %s", quality_report)

        # Conditional persistence (Only if a path is provided)
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            self.df.to_csv(output_path, index=False)
            logging.info("Clean dataset exported to: %s", output_path)

        return self.df


if __name__ == "__main__":
    # Execution block
    INPUT_FILE = "../alarm_gateway/data/raw/alarms_raw.csv"
    OUTPUT_FILE = "../alarm_gateway/data/processed/alarms_cleaned.csv"

    cleaner_engine = AlarmCleaner(INPUT_FILE)
    processed_df = cleaner_engine.run_pipeline(OUTPUT_FILE)

    print("\nProcessed Data Preview:")
    print(processed_df.head())