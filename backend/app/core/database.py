from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import os
from app.core.config import settings
from app.core.logging import logger

url = settings.get_database_url
connect_args = {}
engine_args = {
    "echo": False
}

if "sqlite" in url:
    connect_args = {"check_same_thread": False}
elif os.getenv("VERCEL") or os.getenv("SERVERLESS"):
    # Serverless optimization: Disable pooling to prevent "too many clients" error
    # Supabase/Postgres has a hard limit on connections. Lambdas often exhaust this.
    engine_args["poolclass"] = NullPool
    # Remove pool settings that don't apply to NullPool
    engine_args.pop("pool_size", None)
    engine_args.pop("max_overflow", None)
    engine_args.pop("pool_pre_ping", None)
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
        logger.info("✅ Database tables created/verified")

        # Auto-migrate: add missing columns to existing tables
        # SQLAlchemy create_all() does NOT add new columns to existing tables
        _auto_migrate_columns()

        # Test connection with actual query
        with engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("SELECT 1"))
            logger.info("✅ Database connection verified successfully")
            
    except Exception as e:
        logger.error(f"❌ CRITICAL: Unable to connect to the database: {e}")
        logger.error("The Application will start, but database features will fail!")
        # Note: Not raising to allow Vercel deployment, but logged as critical


def _auto_migrate_columns():
    """
    Check for missing columns in existing tables and add them.
    Covers the case where model was updated but DB table already exists.
    Works on both SQLite and PostgreSQL (Supabase).
    """
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    
    # Define columns that MUST exist (table -> [(col_name, col_type)])
    required_columns = {
        "users": [
            ("refresh_token", "TEXT"),
        ],
    }
    
    is_postgres = "postgresql" in str(engine.url) or "postgres" in str(engine.url)
    
    with engine.connect() as conn:
        for table_name, columns in required_columns.items():
            if not inspector.has_table(table_name):
                continue
            existing_cols = {c["name"] for c in inspector.get_columns(table_name)}
            for col_name, col_type in columns:
                if col_name not in existing_cols:
                    if is_postgres:
                        sql = f'ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {col_name} {col_type}'
                    else:
                        sql = f'ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}'
                    try:
                        conn.execute(text(sql))
                        conn.commit()
                        logger.info(f"✅ Auto-migrated: {table_name}.{col_name} ({col_type})")
                    except Exception as e:
                        logger.warning(f"⚠️ Column migration skipped ({table_name}.{col_name}): {e}")

