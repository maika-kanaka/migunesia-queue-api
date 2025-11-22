from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import os
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.config.settings import settings
from src.config.database import init_database, close_database
from src.config.redis import close_redis
from src.app.middleware.middleware import setup_cors_middleware, setup_custom_middleware 

# Master data
from src.app.api.events import router as events_router
from src.app.api.lokets import router as lokets_router
from src.app.api.tickets import router as tickets_router

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events
    """
    # Startup
    logger.info("Starting up...")
    try:
        await init_database()
        logger.info("Database initialized")
    except Exception as e:
        logger.critical(f"Database initialization failed: {e}")

    yield

    # Shutdown
    logger.info("Shutting down...")
    try:
        await close_database()
        await close_redis()
        logger.info("Cleanup completed")
    except Exception as e:
        logger.critical(f"Cleanup failed: {e}")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="FastAPI Queue System",
    lifespan=lifespan
)

# Setup middleware
setup_cors_middleware(app)
setup_custom_middleware(app)


# Include routers
app.include_router(events_router, prefix="/api/v1")
app.include_router(lokets_router, prefix="/api/v1")
app.include_router(tickets_router, prefix="/api/v1")


@app.get("/")
async def root():
    """
    Root endpoint
    """
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "version": settings.app_version,
        "debug": settings.debug
    }


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request.state.log.warning(f"Validation error: {exc}")
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler
    """
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
