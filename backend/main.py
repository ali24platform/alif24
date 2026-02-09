import sys
import traceback
import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Add current directory to path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

try:
    from app.core.config import settings
    from app.core.database import init_db
    from app.api.v1 import router as api_router
    from app.letters.router import router as letters_router
    from app.middleware.error_handler import error_handler
    from app.core.errors import AppError

    # ============================================================
    # Rate Limiter Setup
    # 
    # FIX: In-memory rate limiting is USELESS on Vercel Serverless
    # because each request runs in an isolated process with no
    # shared memory. Every invocation starts fresh → rate limits
    # never accumulate → valid users can get randomly blocked/unblocked.
    #
    # Solution: Detect VERCEL env and disable rate limiting entirely.
    # When Redis is available, set REDIS_URL env var to enable real
    # distributed rate limiting across all serverless instances.
    # ============================================================
    IS_SERVERLESS = bool(os.getenv("VERCEL"))
    REDIS_URL = os.getenv("REDIS_URL")

    if REDIS_URL:
        # Best option: Redis-backed rate limiting (works across instances)
        limiter = Limiter(
            key_func=get_remote_address,
            default_limits=["100/minute"],
            storage_uri=REDIS_URL
        )
    elif IS_SERVERLESS:
        # Serverless without Redis: disable rate limiting entirely
        # A no-op limiter that never blocks anyone
        limiter = Limiter(
            key_func=get_remote_address,
            default_limits=[]  # Empty = no limits applied
        )
    else:
        # Local development: in-memory rate limiting works fine
        limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup: Initialize database connection
        await init_db()
        yield
        # Shutdown: Clean up resources if needed

    app = FastAPI(
        title="Alif24 Platform API",
        description="Backend API for Alif24 Platform",
        version="1.0.0",
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        lifespan=lifespan
    )

    # Rate Limiter State
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Global Error Handler
    app.add_exception_handler(AppError, error_handler)
    app.add_exception_handler(Exception, error_handler)

    # CORS Configuration
    origins = ["*"]
    allow_credentials = False
    if settings.CORS_ORIGINS:
        if isinstance(settings.CORS_ORIGINS, str):
            origins = [o.strip() for o in settings.CORS_ORIGINS.split(",")]
        else:
            origins = settings.CORS_ORIGINS
        # Only enable credentials if specific origins are set (not wildcard)
        allow_credentials = "*" not in origins

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include Routers
    app.include_router(api_router, prefix=settings.API_PREFIX)
    app.include_router(letters_router, prefix=f"{settings.API_PREFIX}/letters", tags=["letters"])
    
    from app.crm.router import router as crm_router
    app.include_router(crm_router, prefix=f"{settings.API_PREFIX}")

    from app.api.v1.admin_router import router as admin_router
    app.include_router(admin_router, prefix=f"{settings.API_PREFIX}")

    @app.get("/")
    async def root():
        return {
            "message": "Alif24 Platform API is running",
            "docs": f"{settings.API_PREFIX}/docs",
            "redoc": f"{settings.API_PREFIX}/redoc"
        }

except Exception as e:
    # If app fails to start, create a fallback app that shows the error
    error_msg = f"Failed to start FastAPI app: {str(e)}\n{traceback.format_exc()}"
    print(error_msg)  # Print to Vercel logs
    
    app = FastAPI(title="Startup Error")
    
    # Add CORS to fallback app so frontend can see the error
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.api_route("/{catchall:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"])
    async def fallback_route(request: Request):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Application failed to start",
                "detail": error_msg.split('\n')
            }
        )

if __name__ == "__main__":
    import uvicorn
    # Try to get settings if available, else default
    try:
        from app.core.config import settings
        port = settings.PORT
        debug = settings.DEBUG
    except:
        port = 5000
        debug = True
        
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=debug)
