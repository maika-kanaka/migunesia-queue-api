from fastapi import APIRouter
from .events import router as events_router
from .lokets import router as lokets_router
from .tickets import router as tickets_router

# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Include all routers
api_router.include_router(events_router)
api_router.include_router(lokets_router)
api_router.include_router(tickets_router)
