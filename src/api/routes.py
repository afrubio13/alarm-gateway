import logging
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, Query, HTTPException
from sqlalchemy.orm import Session, sessionmaker
from src.config import Config
from src.database.manager import DatabaseManager
from src.database.models import AlarmModel
from src.api.schemas import AlarmResponse, TagAggregation

# Initialize FastAPI application
app = FastAPI(
    title="Industrial Alarm Gateway",
    description="API for querying and analyzing standardized SCADA alarm data."
)

# Global database manager instance
db_manager = DatabaseManager(Config.DATABASE_URL)
SessionLocal = sessionmaker(
    bind=db_manager.engine, 
    autocommit=False, 
    autoflush=False
)


def get_db_session():
    """Dependency that provides a transactional database session.

    Ensures the session is properly closed after the request is processed 
    to prevent connection leaks.

    Yields:
        Session: An active SQLAlchemy database session.
    """
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()


@app.get("/alarms", response_model=List[AlarmResponse])
def read_alarms(
    start_date: datetime = Query(..., description="Start date for temporal filtering (ISO 8601)"),
    end_date: datetime = Query(default_factory=datetime.now, description="End date for temporal filtering"),
    severity: Optional[str] = Query(None, description="Filter by priority level (HIGH, MEDIUM, LOW)"),
    tag: Optional[str] = Query(None, description="Filter by specific industrial asset tag"),
    db: Session = Depends(get_db_session)
):
    """Retrieves filtered alarm records using optimized database indexes.

    This endpoint leverages a composite index on [timestamp, severity] 
    to provide high-performance results even with large datasets.

    Args:
        start_date (datetime): Beginning of the search range.
        end_date (datetime): End of the search range. Defaults to current time.
        severity (Optional[str]): Priority level filter.
        tag (Optional[str]): Hardware asset identifier filter.
        db (Session): Database session injected by dependency.

    Returns:
        List[AlarmResponse]: A list of matching alarm records.

    Raises:
        HTTPException: If the start_date is greater than the end_date.
    """
    if start_date > end_date:
        logging.error("Invalid date range requested: %s > %s", start_date, end_date)
        raise HTTPException(
            status_code=400, 
            detail="Start date cannot be greater than end date."
        )
    
    return db_manager.get_filtered_alarms(
        db=db, 
        start_date=start_date, 
        end_date=end_date, 
        severity=severity, 
        tag=tag
    )


@app.get("/analytics/top-tags", response_model=List[TagAggregation])
def read_top_tags_analytics(
    limit: int = Query(5, ge=1, le=50, description="Number of top assets to retrieve"),
    db: Session = Depends(get_db_session)
):
    """Aggregation endpoint to identify industrial assets with the highest error frequency.

    Useful for maintenance teams to prioritize interventions on faulty 
    sensors or critical hardware failures.

    Args:
        limit (int): The number of top tags to return.
        db (Session): Database session injected by dependency.

    Returns:
        List[TagAggregation]: A list of tags with their respective occurrence counts.
    """
    logging.info("Generating top tags analytics with limit: %d", limit)
    return db_manager.get_top_tags(db=db, limit=limit)