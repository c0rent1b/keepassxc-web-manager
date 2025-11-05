"""
FastAPI application entry point.

Main application setup with:
- CORS middleware
- Error handlers
- API routes
- Static files
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.error_handlers import register_exception_handlers
from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Load settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("=" * 80)
    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info("=" * 80)
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"KeePassXC CLI: {settings.KEEPASSXC_CLI_PATH}")
    logger.info(f"Cache backend: {settings.CACHE_BACKEND}")
    logger.info(f"API docs: {settings.API_DOCS_ENABLED}")
    logger.info("=" * 80)

    # Check KeePassXC CLI availability
    from app.infrastructure.keepassxc.cli_wrapper import KeePassXCCLIWrapper

    cli = KeePassXCCLIWrapper(settings.KEEPASSXC_CLI_PATH)
    is_available = await cli.check_cli_available()

    if is_available:
        version = await cli.get_version()
        logger.info(f"✓ KeePassXC CLI available: version {version}")
    else:
        logger.warning("✗ KeePassXC CLI NOT available - some features will not work")

    logger.info("Application started successfully")

    yield

    # Shutdown
    logger.info("Shutting down application...")


# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
    openapi_url=settings.openapi_url,
    lifespan=lifespan,
)

# =============================================================================
# Middleware
# =============================================================================

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page-Count"],
)

# GZip compression middleware
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,  # Only compress responses > 1KB
)

# =============================================================================
# Error Handlers
# =============================================================================

register_exception_handlers(app)

# =============================================================================
# Routes
# =============================================================================

# Import routers
from app.api.routes import auth, databases, entries, groups, health

# Register API routes
app.include_router(
    health.router,
    tags=["Health"],
)

app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_PREFIX}/auth",
    tags=["Authentication"],
)

app.include_router(
    databases.router,
    prefix=f"{settings.API_V1_PREFIX}/databases",
    tags=["Databases"],
)

app.include_router(
    entries.router,
    prefix=f"{settings.API_V1_PREFIX}/entries",
    tags=["Entries"],
)

app.include_router(
    groups.router,
    prefix=f"{settings.API_V1_PREFIX}/groups",
    tags=["Groups"],
)

# =============================================================================
# Static Files (Frontend)
# =============================================================================

# Mount static files if frontend directory exists
from pathlib import Path

frontend_dir = Path(settings.FRONTEND_DIR)
if frontend_dir.exists():
    app.mount(
        "/static",
        StaticFiles(directory=str(frontend_dir)),
        name="static",
    )
    logger.info(f"Static files mounted: {frontend_dir}")


# =============================================================================
# Root Endpoint
# =============================================================================


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint - API info."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": settings.APP_DESCRIPTION,
        "docs": settings.docs_url if settings.API_DOCS_ENABLED else None,
        "api": {
            "v1": settings.API_V1_PREFIX,
        },
    }


# =============================================================================
# Development server
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
