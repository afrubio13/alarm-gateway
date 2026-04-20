from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, List


class AlarmResponse(BaseModel):
    """Schema for a detailed industrial alarm response.

    This model represents a standardized alarm record as retrieved from the 
    database, including data quality flags and primary identifiers.

    Attributes:
        id (int): Unique database identifier for the alarm record.
        timestamp (datetime): Standardized event date and time.
        tag (str): Unique identifier for the industrial asset or sensor.
        severity (str): Priority level of the alarm (e.g., HIGH, MEDIUM, LOW).
        status (str): Operational state of the alarm (e.g., ACTIVE, CLEARED).
        value (Optional[float]): Numerical sensor reading at the time of event.
        quality_flag (str): Integrity status assigned during the ETL process.
    """
    id: int
    timestamp: datetime
    tag: str
    severity: str
    status: str
    value: Optional[float] = None
    quality_flag: str

    # Configuration to allow compatibility with SQLAlchemy ORM objects
    model_config = ConfigDict(from_attributes=True)


class AlarmSummary(BaseModel):
    """Schema for aggregated reports and high-level frequency summaries.

    Optimized for performance by focusing exclusively on occurrence metrics 
    per asset tag.

    Attributes:
        tag (str): The hardware tag associated with the alarms.
        count (int): The total number of occurrences in the requested period.
    """
    tag: str
    count: int


class TagAggregation(BaseModel):
    """Schema representing the frequency of alarms grouped by hardware tag.

    Attributes:
        tag (str): The unique identifier of the industrial asset.
        count (int): Total count of alarms linked to this specific tag.
    """
    tag: str
    count: int


class ErrorResponse(BaseModel):
    """Standardized schema for API error messages.

    Attributes:
        detail (str): A descriptive message explaining the error encountered.
    """
    detail: str