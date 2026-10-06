"""
FastAPI Application Entrypoint for Enterprise Knowledge Navigator.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.database import engine, Base
from backend.app.api.v1 import api_router

# Import models so Base metadata is populated
import backend.app.models.document


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event handler for application initialization and shutdown."""
    logger.info("Initializing Enterprise Knowledge Navigator services...")
    settings.ensure_directories_exist()
    logger.info("Verifying/creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schemas verified.")
    yield
    logger.info("Enterprise Knowledge Navigator shutting down safely.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise Knowledge Navigator - Real-World GraphRAG & Semantic Retrieval Platform",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API v1 routes
app.include_router(api_router, prefix=settings.API_V1_STR)

# Serve Frontend static files if directory exists
frontend_path = settings.BASE_DIR / "frontend"
if frontend_path.exists():
    app.mount("/app", StaticFiles(directory=str(frontend_path), html=True), name="frontend")


@app.get("/", summary="Root Redirect / Landing")
def read_root():
    """Returns basic system status and links to interactive docs."""
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "api_docs": "/docs",
        "api_v1_health": f"{settings.API_V1_STR}/health",
        "web_interface": "/app/"
    }
