"""API v1 package."""

from fastapi import APIRouter

from app.api.v1.endpoints import tasks

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
