import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

class Config:
    """Centralized configuration management for the application.

    This class aggregates environment variables and constructs technical 
    parameters such as database connection strings. It provides safe 
    defaults for local development environments.

    Attributes:
        DB_USER (str): Database username.
        DB_PASSWORD (str): Database password.
        DB_HOST (str): Database host address (e.g., 'localhost' or an IP).
        DB_PORT (str): Port number for the database service.
        DB_NAME (str): Name of the target database schema.
        DATABASE_URL (str): Fully constructed SQLAlchemy connection URI.
    """

    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "alarm_db")

    # Construct the connection string once to be used across the application
    # This format is compatible with SQLAlchemy's create_engine
    DATABASE_URL = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )