"""
Main API v1 Router Registration.
"""

from fastapi import APIRouter
from backend.app.api.v1 import health
from backend.app.api.v1 import ml

api_router = APIRouter()

# Register endpoint routers
api_router.include_router(health.router, tags=["Health & System"])
api_router.include_router(ml.router, prefix="/ml", tags=["Machine Learning Engine"])
