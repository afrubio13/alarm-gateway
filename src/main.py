import logging
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
from src.modules.cleaner import AlarmCleaner
from src.database.manager import DatabaseManager
from src.config import Config

# Global Configuration
RAW_DATA_PATH = "../alarm_gateway/data/raw/alarms_raw.csv"

# Configure logging to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def run_etl_pipeline() -> None:
    """Orchestrates the Extract, Transform, and Load (ETL) process.

    This function instantiates the cleaning engine and database manager, 
    processes the raw data in memory to ensure high performance, and 
    persists the results into the target SQL database.

    The pipeline follows a sequential flow:
    1. Extraction & Transformation (Cleaning/Flagging).
    2. Infrastructure Validation (Schema creation).
    3. Loading (Batch SQL insertion).

    Raises:
        FileNotFoundError: If the raw data source is missing.
        Exception: For any critical failure during the pipeline execution.
    """
    logging.info("--- Initializing Industrial ETL Pipeline ---")    

    # 1. Component Initialization
    cleaner = AlarmCleaner(RAW_DATA_PATH)
    db_manager = DatabaseManager(Config.DATABASE_URL)

    try:
        # 2. TRANSFORM (Extraction + In-memory cleaning)
        logging.info("Starting data transformation...")
        cleaned_df: pd.DataFrame = cleaner.run_pipeline() 
        
        # Add metadata for auditing
        cleaned_df['processed_at'] = datetime.now()

        # 3. INFRASTRUCTURE (Ensure schema exists)
        db_manager.create_tables()

        # 4. LOAD (Bulk persistence)
        # Technical decision: Use 'Append' logic to maintain historical 
        # integrity for industrial auditing and root cause analysis.
        db_manager.save_dataframe_to_sql(cleaned_df)

        logging.info("--- Pipeline completed successfully ---")

    except FileNotFoundError:
        logging.error(
            "Source file not found at: %s. Please ensure the data generator was executed.",
            RAW_DATA_PATH
        )
    except Exception as error:
        logging.error("Critical failure in the ETL pipeline: %s", error)
        # In a production environment, you might re-raise the error or alert a monitoring service
        raise


if __name__ == "__main__":
    run_etl_pipeline()