"""
Debug Endpoints
Provides diagnostic information about the server and database.

SECURITY FIXES:
1. Only available when ENABLE_DEBUG_ENDPOINTS=true env var is set.
   In production on Vercel, this env var should NOT be set → endpoints return 404.
2. Requires X-Admin-Secret header (same as admin_router.py).
3. Masks ALL sensitive data — no raw URLs, no server IPs exposed.

If ENABLE_DEBUG_ENDPOINTS is not set, the router is effectively empty (no routes registered).
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config import settings
from app.core.database import get_db
import os

router = APIRouter()

# ============================================================
# SECURITY GATE
# ============================================================
DEBUG_ENABLED = os.getenv("ENABLE_DEBUG_ENDPOINTS", "false").lower() == "true"

# Same admin secret as admin_router.py — keeps auth consistent
ADMIN_SECRET = "alif24-admin-secret-2024"


async def verify_debug_access(
    x_admin_secret: str = Header(..., alias="X-Admin-Secret")
):
    """
    Double security check:
    1. ENABLE_DEBUG_ENDPOINTS must be true (checked at route level)
    2. X-Admin-Secret header must match
    """
    if not DEBUG_ENABLED:
        raise HTTPException(404, "Not found")
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(403, "Invalid admin secret key")
    return True


# ============================================================
# ROUTES — Only registered if DEBUG_ENABLED is true
# ============================================================
if DEBUG_ENABLED:
    @router.get("/db-info")
    def get_db_info(
        db: Session = Depends(get_db),
        _: bool = Depends(verify_debug_access)
    ):
        """
        DEBUG ENDPOINT: Check database connection health.
        Only available when ENABLE_DEBUG_ENDPOINTS=true AND admin secret is provided.
        
        Usage:
            curl -H "X-Admin-Secret: alif24-admin-secret-2024" \
                 https://yourdomain.com/api/v1/debug/db-info
        """
        # Test actual connection — only show safe info
        try:
            result = db.execute(text("SELECT current_database(), version()")).fetchone()
            current_db = result[0]
            pg_version = result[1].split(" ")[0:2]  # Only "PostgreSQL X.X"
            pg_version = " ".join(pg_version)
        except Exception as e:
            current_db = f"Connection error"
            pg_version = "Unknown"

        return {
            "status": "active",
            "database_name": current_db,
            "postgres_version": pg_version,
            "environment": {
                "POSTGRES_URL": "SET" if os.getenv("POSTGRES_URL") else "NOT SET",
                "DATABASE_URL": "SET" if os.getenv("DATABASE_URL") else "NOT SET",
                "VERCEL": "YES" if os.getenv("VERCEL") else "NO",
                "DEBUG_ENDPOINTS": "ENABLED"
            }
            # FIX: Removed — was exposing:
            # - configured_db_url (even masked, reconstructable)
            # - server_ip (inet_server_addr)
            # - Raw env var values
        }
