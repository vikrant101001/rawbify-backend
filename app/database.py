from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

logger = logging.getLogger(__name__)

try:
    from .config import settings
    
    # Create engine with database-specific configuration
    if settings.DATABASE_URL.startswith("sqlite"):
        # SQLite configuration (for local development only)
        engine = create_engine(
            settings.DATABASE_URL, 
            connect_args={"check_same_thread": False}
        )
        logger.info("✅ Using SQLite database")
    else:
        # PostgreSQL configuration (for production)
        engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=300,
            connect_args={"sslmode": "require"} if "localhost" not in settings.DATABASE_URL else {}
        )
        logger.info("✅ Using PostgreSQL database")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    
    logger.info("✅ Database configuration successful")
    
except Exception as e:
    logger.error(f"❌ Database configuration failed: {e}")
    # Create a dummy setup for debugging
    engine = None
    SessionLocal = None
    Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 