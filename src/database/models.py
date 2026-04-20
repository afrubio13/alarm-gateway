from sqlalchemy import Column, Integer, Float, String, DateTime, Index
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class AlarmModel(Base):
    """Database model representing the 'alarms' table for SCADA monitoring.

    This model stores standardized alarm data including hardware tags, 
    environmental measurements, and data quality indicators. It includes 
    optimized indexes for high-performance temporal and categorical queries.

    Attributes:
        id (int): Primary key, auto-incremented unique identifier.
        timestamp (datetime): Standardized date and time of the alarm event.
        tag (str): Identifier for the hardware source (e.g., PUMP_1).
        description (str): Detailed text description of the alarm event.
        severity (str): Alarm priority level (e.g., HIGH, MEDIUM, LOW).
        status (str): Current state of the alarm (e.g., ACTIVE, CLEARED).
        value (float): Numerical sensor reading at the time of the event.
        unit (str): Engineering units for the measurement (e.g., bar, °C).
        quality_flag (str): Flags indicating data integrity issues (e.g., DUPLICATE).
        timestamp_raw (str): The original unparsed date string for audit trails.
    """
    __tablename__ = 'alarms'

    # Column Definitions
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    tag = Column(String(100), nullable=False, index=True)
    description = Column(String(500))
    severity = Column(String(30), nullable=False)
    status = Column(String(30), nullable=False)
    value = Column(Float, nullable=True)
    unit = Column(String(20), nullable=True)
    quality_flag = Column(String(255), default='OK')
    timestamp_raw = Column(String(500), nullable=True)

    # Table Arguments
    # Composite index to optimize API queries involving both Time ranges and Severity.
    __table_args__ = (
        Index('idx_timestamp_severity', 'timestamp', 'severity'),
    )

    def __repr__(self) -> str:
        """Returns a string representation of the AlarmModel instance.

        Returns:
            str: Technical summary of the alarm record.
        """
        return f"<AlarmModel(tag='{self.tag}', timestamp='{self.timestamp}', severity='{self.severity}')>"