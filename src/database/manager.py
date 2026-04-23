import pandas as pd
import numpy as np
import logging
from datetime import datetime
from sqlalchemy import create_engine, func
from typing import Dict, Any, List
from src.database.models import Base, AlarmModel

class DatabaseManager:
    """Manages database connections and data persistence operations.

    This class handles the creation of database schemas and the ingestion
    of cleaned DataFrames into the SQL database using SQLAlchemy and 
    optimized batch processing.

    Attributes:
        engine (sqlalchemy.engine.Engine): The SQLAlchemy database engine.
    """

    def __init__(self, connection_string: str):
        """Initializes the database engine with connection-specific arguments.

        Args:
            connection_string (str): The database URI connection string.
        """
        # Configure engine arguments to prevent specific performance issues
        engine_args: Dict[str, Any] = {}
        if "mssql" in connection_string:
            # Enable fast execution for Microsoft SQL Server drivers
            engine_args["fast_executemany"] = True
            
        self.engine = create_engine(connection_string, **engine_args)

    def create_tables(self) -> None:
        """Creates the database schema based on the defined ORM models."""
        logging.info("Ensuring database tables exist...")
        Base.metadata.create_all(self.engine)

    def save_dataframe_to_sql(self, df: pd.DataFrame) -> None:
        """Validates and persists a DataFrame to the 'alarms' table.

        Performs a final deep cleaning to ensure data types match SQL 
        constraints (e.g., handling NULLs and string lengths) before 
        performing a batch insertion.

        Args:
            df (pd.DataFrame): The source DataFrame containing processed alarms.

        Raises:
            Exception: If the database insertion fails after validation.
        """
        logging.info("Starting final validation before SQL ingestion...")
        
        # 1. Identify model columns (excluding primary key ID)
        model_columns: List[str] = [
            column.name for column in AlarmModel.__table__.columns if column.name != 'id'
        ]
        
        # 2. Filter and create a shallow copy to avoid side effects on the original process
        data_to_load = df[model_columns].copy()

        # 3. Final Deep Cleaning
        # Convert NumPy NaN and Pandas NaT to Python None (SQL NULL)
        data_to_load = data_to_load.replace({np.nan: None, pd.NaT: None})
        
        # Ensure string columns comply with schema limits and NOT NULL constraints
        data_to_load['severity'] = data_to_load['severity'].fillna('UNKNOWN').str[:30]
        data_to_load['status'] = data_to_load['status'].fillna('UNKNOWN').str[:30]
        data_to_load['quality_flag'] = data_to_load['quality_flag'].fillna('OK').str[:255]
        
        # Enforce datetime type for the primary timestamp column
        data_to_load['timestamp'] = pd.to_datetime(data_to_load['timestamp'], errors='coerce')
        
        # Drop rows with invalid timestamps as many SQL dialects (e.g., MySQL) 
        # do not accept NULLs in indexed timestamp primary/secondary columns.
        if data_to_load['timestamp'].isna().any():
            invalid_records_count = data_to_load['timestamp'].isna().sum()
            logging.warning(
                "Dropping %d records with invalid timestamps to avoid SQL errors", 
                invalid_records_count
            )
            data_to_load = data_to_load.dropna(subset=['timestamp'])

        try:
            logging.info("Executing batch insert into table: %s", AlarmModel.__tablename__)
            data_to_load.to_sql(
                name=AlarmModel.__tablename__,
                con=self.engine,
                if_exists='append',
                index=False,
                chunksize=1000,
                method='multi'
            )
            logging.info("Bulk load to database completed successfully.")
        except Exception as error:
            logging.error("Critical database error encountered: %s", error)
            logging.debug("Data types of the attempted load:\n%s", data_to_load.dtypes)
            raise

    def get_filtered_alarms(self, db, start_date: datetime, end_date: datetime, 
                            severity: str = None, tag: str = None):
        query = db.query(AlarmModel).filter(AlarmModel.timestamp.between(start_date, end_date))
        
        if severity:
            query = query.filter(AlarmModel.severity == severity.upper())
        if tag:
            query = query.filter(AlarmModel.tag == tag)
            
        #return query.order_by(AlarmModel.timestamp.desc()).all()
        # Include Pagination
        
        return (
        query.order_by(AlarmModel.timestamp.desc())
        .limit(100)
        .offset(0)
        .all()
        )
        

    def get_top_tags(self, db, limit: int = 5):
        return db.query(
            AlarmModel.tag, 
            func.count(AlarmModel.id).label('count')
        ).group_by(AlarmModel.tag).order_by(func.count(AlarmModel.id).desc()).limit(limit).all()

if __name__ == "__main__":
    # Example usage:
    # db_manager = DatabaseManager("mysql+pymysql://user:pass@localhost/db_name")
    # db_manager.create_tables()
    # db_manager.save_dataframe_to_sql(cleaned_df)
    pass