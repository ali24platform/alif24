"""
PostgreSQL Configuration Module for Alif24 Platform

Mukammal PostgreSQL konfiguratsiyasi:
- Connection pooling
- SSL/TLS qo'llab-quvvatlash  
- Health check
- Automatic reconnection
- Migration support
"""

import os
import ssl
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse, urlunparse, quote_plus
from sqlalchemy import create_engine, text, event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import OperationalError, DisconnectionError

logger = logging.getLogger(__name__)


class PostgresConfig:
    """PostgreSQL Configuration Class"""
    
    # Default values
    DEFAULT_HOST = "localhost"
    DEFAULT_PORT = 5432
    DEFAULT_NAME = "alif24_db"
    DEFAULT_USER = "postgres"
    DEFAULT_PASSWORD = ""
    
    # Pool settings
    POOL_SIZE = 10
    MAX_OVERFLOW = 20
    POOL_TIMEOUT = 30
    POOL_RECYCLE = 1800  # 30 minutes
    POOL_PRE_PING = True
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        ssl_mode: str = "prefer",
        url: Optional[str] = None
    ):
        """
        Initialize PostgreSQL configuration
        
        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Database user
            password: Database password
            ssl_mode: SSL mode (disable, allow, prefer, require, verify-ca, verify-full)
            url: Full database URL (overrides other params if provided)
        """
        self._url = url
        self._host = host or os.getenv("DB_HOST", self.DEFAULT_HOST)
        self._port = port or int(os.getenv("DB_PORT", self.DEFAULT_PORT))
        self._database = database or os.getenv("DB_NAME", self.DEFAULT_NAME)
        self._user = user or os.getenv("DB_USER", self.DEFAULT_USER)
        self._password = password or os.getenv("DB_PASSWORD", self.DEFAULT_PASSWORD)
        self._ssl_mode = ssl_mode or os.getenv("DB_SSL_MODE", "prefer")
        
    @property
    def database_url(self) -> str:
        """Get PostgreSQL connection URL"""
        # If full URL is provided, use it
        if self._url:
            url = self._url
            # Fix postgres:// to postgresql://
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
            return url
        
        # Build URL from components
        password_encoded = quote_plus(self._password) if self._password else ""
        
        url = f"postgresql://{self._user}"
        if password_encoded:
            url += f":{password_encoded}"
        url += f"@{self._host}:{self._port}/{self._database}"
        
        # Add SSL mode
        if self._ssl_mode and self._ssl_mode != "disable":
            url += f"?sslmode={self._ssl_mode}"
            
        return url
    
    @property
    def async_database_url(self) -> str:
        """Get async PostgreSQL connection URL (for asyncpg)"""
        url = self.database_url
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    def get_engine_kwargs(self) -> Dict[str, Any]:
        """Get SQLAlchemy engine configuration"""
        return {
            "pool_size": self.POOL_SIZE,
            "max_overflow": self.MAX_OVERFLOW,
            "pool_timeout": self.POOL_TIMEOUT,
            "pool_recycle": self.POOL_RECYCLE,
            "pool_pre_ping": self.POOL_PRE_PING,
            "poolclass": QueuePool,
            "echo": os.getenv("DB_ECHO", "false").lower() == "true"
        }
    
    def create_engine(self) -> Engine:
        """
        Create SQLAlchemy engine with optimal settings
        
        Returns:
            SQLAlchemy Engine instance
        """
        engine = create_engine(
            self.database_url,
            **self.get_engine_kwargs()
        )
        
        # Add event listeners for connection handling
        self._setup_engine_events(engine)
        
        return engine
    
    def _setup_engine_events(self, engine: Engine):
        """Setup engine event listeners for better connection handling"""
        
        @event.listens_for(engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            """Called when a new connection is made"""
            logger.debug("New database connection established")
        
        @event.listens_for(engine, "checkout")
        def on_checkout(dbapi_connection, connection_record, connection_proxy):
            """Called when a connection is retrieved from the pool"""
            pass
        
        @event.listens_for(engine, "checkin")
        def on_checkin(dbapi_connection, connection_record):
            """Called when a connection is returned to the pool"""
            pass
        
        @event.listens_for(engine, "invalidate")
        def on_invalidate(dbapi_connection, connection_record, exception):
            """Called when a connection is invalidated"""
            if exception:
                logger.warning(f"Connection invalidated due to: {exception}")
    
    def test_connection(self) -> bool:
        """
        Test database connection
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            engine = self.create_engine()
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            logger.info("✅ PostgreSQL connection successful")
            return True
        except OperationalError as e:
            logger.error(f"❌ PostgreSQL connection failed: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error testing connection: {e}")
            return False
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information (without password)"""
        return {
            "host": self._host,
            "port": self._port,
            "database": self._database,
            "user": self._user,
            "ssl_mode": self._ssl_mode,
            "pool_size": self.POOL_SIZE,
            "max_overflow": self.MAX_OVERFLOW
        }


# ============================================================
# Predefined Configurations
# ============================================================

class LocalPostgresConfig(PostgresConfig):
    """Local development PostgreSQL configuration"""
    
    def __init__(self):
        super().__init__(
            host="localhost",
            port=5432,
            database="alif24_db",
            user="postgres",
            password=os.getenv("DB_PASSWORD", "postgres"),
            ssl_mode="disable"
        )


class DockerPostgresConfig(PostgresConfig):
    """Docker PostgreSQL configuration"""
    
    def __init__(self):
        super().__init__(
            host=os.getenv("DB_HOST", "db"),
            port=int(os.getenv("DB_PORT", 5432)),
            database=os.getenv("DB_NAME", "alif24"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
            ssl_mode="disable"
        )


class SupabasePostgresConfig(PostgresConfig):
    """Supabase PostgreSQL configuration"""
    
    def __init__(self):
        # Get from environment or use defaults
        url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
        
        if url:
            super().__init__(url=url)
        else:
            super().__init__(
                host=os.getenv("DB_HOST", "db.rvboscxljclteqvlxmeo.supabase.co"),
                port=int(os.getenv("DB_PORT", 5432)),
                database=os.getenv("DB_NAME", "postgres"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", ""),
                ssl_mode="require"
            )


class ProductionPostgresConfig(PostgresConfig):
    """Production PostgreSQL configuration with enhanced security"""
    
    POOL_SIZE = 20
    MAX_OVERFLOW = 40
    
    def __init__(self):
        url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
        
        if not url:
            raise ValueError("DATABASE_URL or POSTGRES_URL must be set in production")
        
        super().__init__(url=url)
        self._ssl_mode = "require"


# ============================================================
# Factory Function
# ============================================================

def get_postgres_config(environment: Optional[str] = None) -> PostgresConfig:
    """
    Get PostgreSQL configuration based on environment
    
    Args:
        environment: One of 'local', 'docker', 'supabase', 'production'
                    If None, will be determined from NODE_ENV
    
    Returns:
        PostgresConfig instance
    """
    if environment is None:
        environment = os.getenv("NODE_ENV", "development")
    
    configs = {
        "local": LocalPostgresConfig,
        "development": LocalPostgresConfig,
        "docker": DockerPostgresConfig,
        "supabase": SupabasePostgresConfig,
        "production": ProductionPostgresConfig,
    }
    
    config_class = configs.get(environment.lower(), LocalPostgresConfig)
    return config_class()


# ============================================================
# Environment Variable Template
# ============================================================

ENV_TEMPLATE = """
# PostgreSQL Configuration for Alif24 Platform
# Copy this to your .env file and update values

# Option 1: Full Database URL (recommended for Supabase/production)
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/alif24_db

# Option 2: Individual components (for local development)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=alif24_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_SSL_MODE=prefer

# Pool settings (optional)
DB_ECHO=false  # Set to true for SQL logging

# For Supabase:
# DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres?sslmode=require
"""


def print_env_template():
    """Print environment variable template"""
    print(ENV_TEMPLATE)


# ============================================================
# Migration Helpers
# ============================================================

def run_migrations(config: PostgresConfig):
    """
    Run Alembic migrations
    
    Args:
        config: PostgreSQL configuration
    """
    import subprocess
    import os
    
    # Set DATABASE_URL for Alembic
    os.environ["DATABASE_URL"] = config.database_url
    
    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        )
        
        if result.returncode == 0:
            logger.info("✅ Migrations completed successfully")
            print(result.stdout)
        else:
            logger.error(f"❌ Migration failed: {result.stderr}")
            
    except FileNotFoundError:
        logger.error("Alembic not found. Install with: pip install alembic")


def check_database_health(config: PostgresConfig) -> Dict[str, Any]:
    """
    Check database health and return statistics
    
    Args:
        config: PostgreSQL configuration
        
    Returns:
        Dictionary with health information
    """
    health = {
        "status": "unknown",
        "connection": False,
        "version": None,
        "database_size": None,
        "active_connections": None
    }
    
    try:
        engine = config.create_engine()
        with engine.connect() as conn:
            # Test connection
            health["connection"] = True
            
            # Get version
            result = conn.execute(text("SELECT version()"))
            health["version"] = result.fetchone()[0]
            
            # Get database size
            result = conn.execute(text(
                f"SELECT pg_size_pretty(pg_database_size('{config._database}'))"
            ))
            health["database_size"] = result.fetchone()[0]
            
            # Get active connections
            result = conn.execute(text(
                "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
            ))
            health["active_connections"] = result.fetchone()[0]
            
            health["status"] = "healthy"
            
    except Exception as e:
        health["status"] = "unhealthy"
        health["error"] = str(e)
    
    return health


# ============================================================
# CLI Entry Point
# ============================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "test":
            config = get_postgres_config()
            success = config.test_connection()
            sys.exit(0 if success else 1)
            
        elif command == "health":
            config = get_postgres_config()
            health = check_database_health(config)
            import json
            print(json.dumps(health, indent=2))
            
        elif command == "migrate":
            config = get_postgres_config()
            run_migrations(config)
            
        elif command == "env":
            print_env_template()
            
        elif command == "info":
            config = get_postgres_config()
            import json
            print(json.dumps(config.get_connection_info(), indent=2))
            
        else:
            print(f"Unknown command: {command}")
            print("Available commands: test, health, migrate, env, info")
            sys.exit(1)
    else:
        print("PostgreSQL Configuration for Alif24 Platform")
        print("\nUsage: python postgres_config.py <command>")
        print("\nCommands:")
        print("  test    - Test database connection")
        print("  health  - Check database health")
        print("  migrate - Run database migrations")
        print("  env     - Print environment variable template")
        print("  info    - Print current configuration")
