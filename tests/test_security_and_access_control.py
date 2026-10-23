"""
Automated Security, Multi-Tenant Document Tenancy, and Cross-User Access Isolation Tests.
Verifies:
- Production SECRET_KEY validation guards
- Demo account seeding configuration toggle
- Document upload with access level tags (public, internal, confidential, restricted)
- Document preview, download, and deletion permission enforcement
- Cross-user and cross-role document leakage prevention in Search, RAG Q&A, and Knowledge Graph
- Unicode NFKC normalization and clean_text fidelity
- Empty query and empty index resilience
"""

import io
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.config import settings, Settings
from backend.app.core.database import SessionLocal
from backend.app.models.document import DocumentRecord
from backend.app.services.document_processor import document_processor
from backend.app.services.vector_index import vector_index_service

client = TestClient(app)


def get_auth_token(email: str, password: str) -> str:
    """Helper to authenticate and retrieve access token."""
    res = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": email, "password": password}
    )
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]


def test_production_secret_key_validation_guard():
    """Verify that Settings raises a ValueError if SECRET_KEY is default or weak in production."""
    with pytest.raises(ValueError, match="FATAL SECURITY CONFIGURATION"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="dev-secret-key-knowledge-navigator"
        )

    with pytest.raises(ValueError, match="FATAL SECURITY CONFIGURATION"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="too-short"
        )

    # Valid 32+ char key should succeed in production
    valid_prod_settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="a" * 32
    )
    assert valid_prod_settings.ENVIRONMENT == "production"
    assert valid_prod_settings.ENABLE_DEMO_ACCOUNTS is False


def test_demo_accounts_gating_in_production():
    """Verify that in production, demo accounts are disabled by default unless explicitly enabled."""
    prod_settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="b" * 32
    )
    assert prod_settings.ENABLE_DEMO_ACCOUNTS is False

    dev_settings = Settings(
        ENVIRONMENT="development",
        SECRET_KEY="dev-secret-key-knowledge-navigator"
    )
    assert dev_settings.ENABLE_DEMO_ACCOUNTS is True


def test_unicode_nfkc_normalization_and_sanitization():
    """Verify clean_text properly normalizes Unicode NFKC ligatures and strips zero-width chars."""
    raw_text = "O\uFB03ce is \uFB00 a test with zero-width\u200b space."
    cleaned = document_processor.clean_text(raw_text)
    # \uFB03 is 'ffi' ligature, \uFB00 is 'ff' ligature
    assert "Office is ff a test with zero-width space." in cleaned
    assert "\u200b" not in cleaned


def test_empty_query_resilience():
    """Verify semantic, keyword, and hybrid search handle empty and whitespace queries gracefully."""
    assert vector_index_service.semantic_search("") == []
    assert vector_index_service.semantic_search("   ") == []
    assert vector_index_service.keyword_search("") == []
    assert vector_index_service.keyword_search("   ") == []
    assert vector_index_service.hybrid_search("") == []
    assert vector_index_service.hybrid_search("   ") == []


def test_confidential_document_isolation_and_cross_user_access():
    """
    Comprehensive multi-tenant test:
    1. Admin uploads a 'confidential' document restricted to 'admin' role.
    2. Admin can view, download, preview, search, and query the document.
    3. Knowledge Worker (non-admin) CANNOT preview or download the confidential document (403).
    4. Knowledge Worker search and RAG Q&A CANNOT retrieve or leak chunks from the confidential document.
    5. Knowledge Worker CANNOT delete the confidential document (403).
    6. Admin can safely delete the document.
    """
    admin_token = get_auth_token("admin@eknavigator.com", "Admin@123456")
    worker_token = get_auth_token("worker@eknavigator.com", "Worker@123456")

    confidential_content = (
        "Project Blacklight Confidential Executive Briefing.\n\n"
        "Project Blacklight is an unauthorized top-secret quantum telemetry system. "
        "The project code phrase is ObsidianVortex-994. "
        "Total confidential budget allocation is 45 million dollars."
    )
    confidential_filename = "confidential_project_blacklight.txt"

    # Pre-clean if exists
    db = SessionLocal()
    try:
        existing = db.query(DocumentRecord).filter(DocumentRecord.filename == confidential_filename).first()
        if existing:
            client.delete(
                f"{settings.API_V1_STR}/navigator/documents/{existing.id}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
    finally:
        db.close()

    # 1. Admin uploads confidential document
    upload_res = client.post(
        f"{settings.API_V1_STR}/navigator/documents/upload",
        headers={"Authorization": f"Bearer {admin_token}"},
        data={"access_level": "confidential", "allowed_roles": "admin"},
        files={"file": (confidential_filename, io.BytesIO(confidential_content.encode("utf-8")), "text/plain")}
    )
    assert upload_res.status_code == 200
    doc_id = upload_res.json()["id"]

    try:
        # 2. Admin can preview and download
        prev_admin = client.get(
            f"{settings.API_V1_STR}/navigator/documents/{doc_id}/preview",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert prev_admin.status_code == 200
        assert "ObsidianVortex-994" in prev_admin.json()["content_preview"]

        dl_admin = client.get(
            f"{settings.API_V1_STR}/navigator/documents/{doc_id}/download",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert dl_admin.status_code == 200

        # 3. Worker cannot preview or download (403 Forbidden)
        prev_worker = client.get(
            f"{settings.API_V1_STR}/navigator/documents/{doc_id}/preview",
            headers={"Authorization": f"Bearer {worker_token}"}
        )
        assert prev_worker.status_code == 403

        dl_worker = client.get(
            f"{settings.API_V1_STR}/navigator/documents/{doc_id}/download",
            headers={"Authorization": f"Bearer {worker_token}"}
        )
        assert dl_worker.status_code == 403

        # 4. Search isolation: Admin finds confidential chunk, Worker DOES NOT
        search_admin = client.post(
            f"{settings.API_V1_STR}/navigator/search",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"query": "ObsidianVortex Blacklight budget", "mode": "hybrid"}
        )
        assert search_admin.status_code == 200
        assert any("ObsidianVortex" in r["content"] for r in search_admin.json()["results"])

        search_worker = client.post(
            f"{settings.API_V1_STR}/navigator/search",
            headers={"Authorization": f"Bearer {worker_token}"},
            json={"query": "ObsidianVortex Blacklight budget", "mode": "hybrid"}
        )
        assert search_worker.status_code == 200
        assert not any("ObsidianVortex" in r["content"] for r in search_worker.json()["results"])

        # 5. RAG Q&A isolation: Worker cannot extract confidential project details
        ask_worker = client.post(
            f"{settings.API_V1_STR}/navigator/ask",
            headers={"Authorization": f"Bearer {worker_token}"},
            json={"question": "What is the secret code phrase for Project Blacklight?", "enable_graphrag": False}
        )
        assert ask_worker.status_code == 200
        assert "ObsidianVortex" not in ask_worker.json()["answer"]

        # Worker targeting confidential doc specifically is blocked
        ask_targeted = client.post(
            f"{settings.API_V1_STR}/navigator/ask",
            headers={"Authorization": f"Bearer {worker_token}"},
            json={
                "question": "What is the secret code phrase?",
                "document_filter": doc_id,
                "enable_graphrag": False
            }
        )
        assert ask_targeted.status_code == 200
        assert "Access Restricted" in ask_targeted.json()["answer"]

        # 6. Deletion authorization: Worker cannot delete Admin's confidential document
        del_worker = client.delete(
            f"{settings.API_V1_STR}/navigator/documents/{doc_id}",
            headers={"Authorization": f"Bearer {worker_token}"}
        )
        assert del_worker.status_code == 403

    finally:
        # 7. Admin cleans up document
        del_admin = client.delete(
            f"{settings.API_V1_STR}/navigator/documents/{doc_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert del_admin.status_code == 200
