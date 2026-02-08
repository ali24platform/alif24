from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config import settings
from app.core.database import get_db
import os

router = APIRouter()

@router.get("/db-info")
def get_db_info(db: Session = Depends(get_db)):
    """
    DEBUG ENDPOINT: Check active database connection details.
    """
    db_url = settings.get_database_url
    masked_url = db_url
    
    try:
        # Mask password safely
        if "@" in db_url:
            # protocol://user:pass@host:port/db
            prefix = db_url.split("@")[0]
            suffix = db_url.split("@")[1]
            
            if ":" in prefix:
                # Handle postgresql://user:pass format
                parts = prefix.split(":")
                # logic: parts[-1] is password
                # But 'postgresql://' has a colon too.
                # simpler: find identifying info directly?
                # Let's just return host and DB name
                pass
            
            # Simple approach: hide everything between : and @ if it exists
            import re
            masked_url = re.sub(r':([^:@]+)@', ':******@', db_url)
    except:
        masked_url = "Error masking URL"

    # Test actual connection
    try:
        result = db.execute(text("SELECT current_database(), inet_server_addr()")).fetchone()
        current_db = result[0]
        server_ip = result[1]
    except Exception as e:
        current_db = f"Error: {e}"
        server_ip = "Unknown"

    return {
        "status": "active",
        "configured_db_url": masked_url,
        "active_database_name": current_db,
        "server_ip": str(server_ip),
        "environment_variables": {
            "POSTGRES_URL": "SET" if os.getenv("POSTGRES_URL") else "NOT SET",
            "DATABASE_URL": "SET" if os.getenv("DATABASE_URL") else "NOT SET",
            "VERCEL": os.getenv("VERCEL", "Not set")
        }
    }
