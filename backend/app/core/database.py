from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.logging import logger

url = settings.get_database_url
connect_args = {}
engine_args = {
    "echo": False
}

if "sqlite" in url:
    connect_args = {"check_same_thread": False}
else:
    engine_args["pool_pre_ping"] = True
    engine_args["pool_size"] = 10
    engine_args["max_overflow"] = 20

engine = create_engine(
    url,
    connect_args=connect_args,
    **engine_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def init_db():
    """Initialize database"""
    try:
        # Import models to ensure they are registered with Base.metadata
        # Local import to avoid circular dependency
        from app import models  # noqa
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified")

        # Test connection
        with engine.connect() as conn:
            pass  # Connection test successful
    except Exception as e:
        logger.error(f"⚠️ WARNING: Unable to connect to the database: {e}")
        logger.error("The Application will start, but database features will fail until DATABASE_URL is configured.")
        # raise  <-- Commented out to prevent Vercel 500 crash on startup

