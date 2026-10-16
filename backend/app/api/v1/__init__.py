"""
Main API v1 Router Registration.
"""

from fastapi import APIRouter
from backend.app.api.v1 import health
from backend.app.api.v1 import ml
from backend.app.api.v1 import navigator
from backend.app.api.v1 import auth
from backend.app.api.v1 import workspace

api_router = APIRouter()

# Register endpoint routers
api_router.include_router(health.router, tags=["Health & System"])
api_router.include_router(ml.router, prefix="/ml", tags=["Machine Learning Engine"])
api_router.include_router(navigator.router, prefix="/navigator", tags=["Enterprise Navigator"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & User Management"])
api_router.include_router(workspace.router, prefix="/workspace", tags=["Workspace & Features"])
