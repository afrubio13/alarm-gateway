import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os
from typing import Any, Union, List, Optional


def generate_timestamp(base_time:datetime) -> str:
    """Generates a timestamp in various formats to simulate inconsistent data.

    Arg:
        base_time: Date to generate a chronological timestamp. 
    
    Returns:
        str: A string representing a date in different formats (ISO, custom, 
            or a None placeholder).
    """
    formats = [
        base_time.strftime("%Y-%m-%d %H:%M:%S"),
        base_time.strftime("%d/%m/%Y %H:%M"),
        base_time.strftime("%b %d, %Y %I:%M %p"),
        base_time.isoformat()
    ]

    if random.random() < 0.02:
        return None
    
    return random.choice(formats)


def generate_value() -> Union[float, str, Any]:
    """Generates a numerical value or a data error placeholder.

    Returns:
        Union[float, str, Any]: A float measurement, a string with comma 
            decimal separators, a NumPy NaN, or an 'OFFLINE' status.
    """
    random_factor = random.random()

    if random_factor < 0.03:
        return round(random.uniform(-100, 0), 2)
    if random_factor < 0.75:
        return round(random.uniform(10, 100), 2)
    elif random_factor < 0.85:
        # Simulating European decimal format as a string
        return str(round(random.uniform(10, 100), 2)).replace('.', ',')
    elif random_factor < 0.95:
        return np.nan
    else:
        return "OFFLINE"
    

def select_with_noise(clean_list: List[Any], noisy_list: List[Any], clean_probability: float) -> Any:
    """Selects a value from a clean list or a noisy list based on probability.

    Args:
        clean_list (List[Any]): List containing standard/valid data.
        noisy_list (List[Any]): List containing non-standard or 'dirty' data.
        clean_probability (float): Probability (0 to 1) of choosing from the clean list.

    Returns:
        Any: A chosen value from either the clean or noisy source.
    """
    if random.random() < clean_probability:
        return random.choice(clean_list)
    else:
        return random.choice(noisy_list)


def generate_severity() -> Any:
    """Generates a severity level with a 70% chance of being standard.

    Returns:
        Any: A severity level string or noise.
    """
    return select_with_noise(SEVERITIES, SEVERITY_NOISE, 0.7)


def generate_status() -> Any:
    """Generates an alarm status with an 80% chance of being standard.

    Returns:
        Any: A status string or noise.
    """
    return select_with_noise(STATUSES, STATUS_NOISE, 0.8)


def generate_tag() -> Any:
    """Generates a hardware tag with a 90% chance of being standard.

    Returns:
        Any: A tag string or noise.
    """
    return select_with_noise(TAGS, TAGS_NOISE, 0.95)


def generate_unit() -> Any:
    """Generates a measurement unit with an 85% chance of being standard.

    Returns:
        Any: A unit string or noise.
    """
    return select_with_noise(UNITS, UNITS_NOISE, 0.85)
    

def generate_description(descriptions: List[Optional[str]]) -> Optional[str]:
    """Randomly selects an alarm description from a provided list.

    Args:
        descriptions (List[Optional[str]]): A list of possible alarm descriptions.

    Returns:
        Optional[str]: A selected description string or None.
    """
    return random.choice(descriptions)


def create_raw_alarm_dataset(num_records: int, output_path: str) -> None:
    """Generates and exports a synthetic dataset of alarms with intentional errors.

    The dataset is designed to test data cleaning pipelines. It includes 
    inconsistent timestamps, noisy categories, and duplicate records. 
    Outputs are saved as CSV and JSON.

    Args:
        num_records (int): Number of unique records to generate.
        output_path (str): Directory where the files will be stored.
    """
    os.makedirs(output_path, exist_ok=True)
    
    raw_records: List[dict] = []

    current_time = datetime.now() - timedelta(days=100)

    for _ in range(num_records):
        current_time = current_time + timedelta(minutes=random.randint(0, 30))
        alarm_entry = {
            "timestamp": generate_timestamp(current_time),
            "tag": generate_tag(),
            "description": generate_description(ALARM_DESCRIPTIONS),
            "severity": generate_severity(),
            "status": generate_status(),
            "value": generate_value(),
            "unit": generate_unit()
        }
        raw_records.append(alarm_entry)

    # Convert to DataFrame
    alarm_df = pd.DataFrame(raw_records)
    duplicate_sample = alarm_df.sample(n=random.randint(0,50), replace=False)
    
    # Introduce intentional duplicates (first N (random) records)
    alarm_df = pd.concat([alarm_df, duplicate_sample], ignore_index=True)

    # Export Files
    csv_file_path = os.path.join(output_path, "alarms_raw.csv")
    
    alarm_df.to_csv(csv_file_path, index=False)
    
    print(f"Dataset generation complete:")
    print(f"- CSV saved to: {csv_file_path}")
    print(f"Total records (including duplicates): {len(alarm_df)}")


# Constants and Configuration
NUM_RECORDS = 20000
OUTPUT_DIRECTORY = "../alarm_gateway/data/raw"

TAGS = [f"PUMP_{i}" for i in range(1, 6)] + [f"VALVE_{i}" for i in range(1, 6)]
TAGS_NOISE = [None, ""]

SEVERITIES = ["HIGH", "MEDIUM", "LOW"]
SEVERITY_NOISE = ["high", "h", "med", "low", None, ""]

STATUSES = ["ACTIVE", "CLEARED", "ACKNOWLEDGED"]
STATUS_NOISE = ["active", "cleared", "ack", "acknowledged", None, ""]

UNITS = ["bar", "°C", "psi"]
UNITS_NOISE = [None, ""]

ALARM_DESCRIPTIONS = [
    "High value detected",
    "Low value warning",
    "Sensor failure",
    "Communication lost",
    "Threshold exceeded",
    None,
    ""
]

if __name__ == "__main__":
    create_raw_alarm_dataset(NUM_RECORDS, OUTPUT_DIRECTORY)