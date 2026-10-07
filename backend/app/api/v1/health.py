"""
System and Health API Endpoints.
"""

import sys
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.logging import logger
from backend.app.schemas.health import HealthStatus, SystemInfoResponse, StandardResponse

router = APIRouter()


@router.get("/health", response_model=HealthStatus, summary="System Health Check")
def get_health_check(db: Session = Depends(get_db)):
    """
    Perform a live health check on backend services, including:
    - Application status
    - Database connectivity check
    - Filesystem directory readiness
    """
    db_connected = False
    try:
        db.execute(text("SELECT 1"))
        db_connected = True
    except Exception as e:
        logger.error(f"Health check database query failed: {e}")
        db_connected = False

    dirs_ready = (
        settings.DATA_DIR.exists()
        and settings.RAW_DOCS_DIR.exists()
        and settings.PROCESSED_DOCS_DIR.exists()
        and settings.VECTOR_STORE_DIR.exists()
        and settings.GRAPH_STORE_DIR.exists()
    )

    overall_status = "healthy" if (db_connected and dirs_ready) else "degraded"

    return HealthStatus(
        status=overall_status,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        database_connected=db_connected,
        storage_directories_ready=dirs_ready,
        active_providers={
            "llm_provider": settings.LLM_PROVIDER,
            "embedding_provider": settings.EMBEDDING_PROVIDER,
        }
    )


@router.get("/system/info", response_model=SystemInfoResponse, summary="Detailed System Information")
def get_system_info():
    """Returns general operational metadata for the running instance."""
    return SystemInfoResponse(
        project_name=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        python_version=sys.version.split()[0],
        database_url=settings.DATABASE_URL.split("///")[-1],
        features_available=[
            "Core FastAPI Application Engine",
            "Pydantic Validation & Configuration",
            "Relational Storage & Schema Verification (SQLite)",
            "Machine Learning TF-IDF Vectorization & Cosine Similarity (scikit-learn)",
            "Unsupervised K-Means Semantic Clustering (scikit-learn)",
            "Storage & Directory Readiness Verification",
            "Structured File & Console Event Logging",
            "Health & Diagnostics API Layer",
            "Operational Administration Interface"
        ],
        storage_status={
            "raw_docs_dir": settings.RAW_DOCS_DIR.exists(),
            "processed_docs_dir": settings.PROCESSED_DOCS_DIR.exists(),
            "vector_store_dir": settings.VECTOR_STORE_DIR.exists(),
            "graph_store_dir": settings.GRAPH_STORE_DIR.exists(),
            "logs_dir": settings.LOG_DIR.exists(),
        }
    )


@router.get("/ping", response_model=StandardResponse, summary="Fast Ping")
def ping():
    """Quick latency / uptime check."""
    return StandardResponse(
        success=True,
        message="Enterprise Knowledge Navigator Backend is running."
    )
