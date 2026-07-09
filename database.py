from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    logger.warning("DATABASE_URL not found in environment. Falling back to local SQLite database (safeway.db).")
    DATABASE_URL = "sqlite:///./safeway.db"

# Create engine, using special configuration for SQLite
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

try:
    engine = create_engine(DATABASE_URL, connect_args=connect_args)
    # Verify connection works
    with engine.connect() as conn:
        pass
    logger.info(f"Connected to database successfully: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")
except Exception as e:
    logger.error(f"Failed to connect to database {DATABASE_URL}: {e}")
    logger.warning("Falling back to local SQLite database (safeway.db) due to connection failure.")
    DATABASE_URL = "sqlite:///./safeway.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

from models import Base
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified/created successfully.")
except Exception as e:
    logger.error(f"Error creating database tables: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()