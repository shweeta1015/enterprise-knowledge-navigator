"""
Unit and API Integration Tests for Sprint 1 Foundation.
Tests configuration, database connectivity, health endpoints, and static mounts.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.core.database import Base, get_db

client = TestClient(app)


def test_root_endpoint():
    """Verify landing page endpoint returns valid project metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["project"] == settings.PROJECT_NAME
    assert data["version"] == settings.VERSION
    assert "api_docs" in data
    assert "api_v1_health" in data


def test_ping_endpoint():
    """Verify ping endpoint responds quickly with success status."""
    response = client.get(f"{settings.API_V1_STR}/ping")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "running" in data["message"].lower()


def test_health_check_endpoint():
    """Verify health endpoint validates database connectivity and directories."""
    response = client.get(f"{settings.API_V1_STR}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database_connected"] is True
    assert data["storage_directories_ready"] is True
    assert "active_providers" in data


def test_system_info_endpoint():
    """Verify system info endpoint reports configuration and storage directories."""
    response = client.get(f"{settings.API_V1_STR}/system/info")
    assert response.status_code == 200
    data = response.json()
    assert data["project_name"] == settings.PROJECT_NAME
    assert len(data["features_available"]) >= 5
    assert data["storage_status"]["raw_docs_dir"] is True
    assert data["storage_status"]["vector_store_dir"] is True
    assert data["storage_status"]["graph_store_dir"] is True


def test_frontend_mount():
    """Verify that frontend HTML assets are mounted and accessible."""
    response = client.get("/app/")
    assert response.status_code == 200
    assert "Enterprise Knowledge Navigator" in response.text


def test_refresh_button_endpoints():
    """Verify that all API endpoints invoked by the frontend Refresh buttons are healthy."""
    # 1. Dashboard metrics refresh endpoint
    res_metrics = client.get(f"{settings.API_V1_STR}/navigator/dashboard/metrics")
    assert res_metrics.status_code == 200
    metrics = res_metrics.json()
    assert "total_documents" in metrics
    assert "indexed_documents" in metrics

    # 2. System health refresh endpoint
    res_health = client.get(f"{settings.API_V1_STR}/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"

    # 3. Documents list refresh endpoint
    res_docs = client.get(f"{settings.API_V1_STR}/navigator/documents")
    assert res_docs.status_code == 200
    assert "documents" in res_docs.json()

    # 4. Knowledge graph refresh endpoint
    res_graph = client.get(f"{settings.API_V1_STR}/navigator/graph")
    assert res_graph.status_code == 200
    graph_data = res_graph.json()
    assert "nodes" in graph_data
    assert "edges" in graph_data

    # 5. Evaluation history refresh endpoint
    res_eval = client.get(f"{settings.API_V1_STR}/navigator/evaluate/history")
    assert res_eval.status_code == 200
    assert isinstance(res_eval.json(), list)
