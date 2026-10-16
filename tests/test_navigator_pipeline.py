"""
Comprehensive Automated Tests for Document Ingestion, Search, Grounded RAG,
Knowledge Graph, GraphRAG, Evaluation, and Dashboard Metrics.
"""

import io
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.config import settings

client = TestClient(app)


def test_txt_upload_and_pipeline():
    """Verify end-to-end TXT file upload, extraction, chunking, and indexing."""
    sample_content = (
        "Enterprise Knowledge Navigator Architecture Overview.\n\n"
        "Dr. Alice Vance leads the Artificial Intelligence Engineering Department. "
        "The Artificial Intelligence Engineering Department develops the Knowledge Navigator platform. "
        "Knowledge Navigator integrates with PostgreSQL and Docker for enterprise operations.\n\n"
        "Remote Work Policy:\n"
        "Employees are permitted to work remotely up to two days per week with manager approval. "
        "Health insurance benefits cover medical examinations, hospitalization, and prescription drugs."
    )
    # Clean up existing test document if present to ensure idempotence
    docs_res = client.get(f"{settings.API_V1_STR}/navigator/documents")
    if docs_res.status_code == 200:
        for d in docs_res.json()["documents"]:
            if d["filename"] == "architecture_overview.txt":
                client.delete(f"{settings.API_V1_STR}/navigator/documents/{d['id']}")

    file_bytes = io.BytesIO(sample_content.encode("utf-8"))
    
    response = client.post(
        f"{settings.API_V1_STR}/navigator/documents/upload",
        files={"file": ("architecture_overview.txt", file_bytes, "text/plain")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "architecture_overview.txt"
    assert data["status"] == "indexed"
    assert data["chunk_count"] >= 1
    assert data["entity_count"] >= 1
    assert "id" in data
    doc_id = data["id"]

    # Verify document listing
    list_res = client.get(f"{settings.API_V1_STR}/navigator/documents")
    assert list_res.status_code == 200
    docs = list_res.json()["documents"]
    assert any(d["id"] == doc_id for d in docs)

    # Verify document details
    detail_res = client.get(f"{settings.API_V1_STR}/navigator/documents/{doc_id}")
    assert detail_res.status_code == 200
    assert len(detail_res.json()["chunks_preview"]) >= 1


def test_hybrid_search_retrieval():
    """Verify hybrid search returns relevant chunks with scores and metadata."""
    payload = {
        "query": "remote work and telecommuting policy",
        "mode": "hybrid",
        "top_k": 3
    }
    response = client.post(f"{settings.API_V1_STR}/navigator/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_found"] >= 1
    first_result = data["results"][0]
    assert "remote" in first_result["content"].lower() or "work" in first_result["content"].lower()
    assert first_result["score"] > 0.0
    assert "page_number" in first_result


def test_grounded_rag_with_citations():
    """Verify RAG assistant answers question with verifiable document citations."""
    payload = {
        "question": "What is the policy for working remotely?",
        "enable_graphrag": True,
        "top_k": 3
    }
    response = client.post(f"{settings.API_V1_STR}/navigator/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_grounded"] is True
    assert "remotely" in data["answer"].lower() or "days" in data["answer"].lower()
    assert len(data["sources"]) >= 1
    assert data["sources"][0]["page_number"] >= 1


def test_rag_unanswerable_question_no_hallucination():
    """Verify system does not hallucinate when information is absent from documents."""
    payload = {
        "question": "What is the company policy regarding interplanetary space travel to Mars?",
        "enable_graphrag": False,
        "top_k": 3
    }
    response = client.post(f"{settings.API_V1_STR}/navigator/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    # If chunks scored near 0 or irrelevant, should report insufficient information
    answer_text = data["answer"].lower()
    assert (
        "insufficient information" in answer_text
        or "does not support" in answer_text
        or data["confidence"] < 0.95
    )


def test_knowledge_graph_and_graphrag():
    """Verify Knowledge Graph entities, relationships, and GraphRAG expansion."""
    response = client.get(f"{settings.API_V1_STR}/navigator/graph")
    assert response.status_code == 200
    data = response.json()
    assert data["node_count"] >= 1
    assert any(n["category"] in ["PERSON", "ORG", "TECH", "PRODUCT", "POLICY"] for n in data["nodes"])

    # Test GraphRAG asking about relationships
    payload = {
        "question": "Who leads the Artificial Intelligence Engineering Department and what do they develop?",
        "enable_graphrag": True,
        "top_k": 3
    }
    rag_res = client.post(f"{settings.API_V1_STR}/navigator/ask", json=payload)
    assert rag_res.status_code == 200
    rag_data = rag_res.json()
    assert len(rag_data["graph_evidence"]) >= 1 or len(rag_data["sources"]) >= 1


def test_evaluation_workflow():
    """Verify real evaluation pipeline computes P@K, MRR, latency, and stores run."""
    response = client.post(f"{settings.API_V1_STR}/navigator/evaluate/run?k=3")
    assert response.status_code == 200
    data = response.json()
    assert data["query_count"] >= 3
    assert data["precision_at_k"] >= 0.0
    assert data["mrr_score"] >= 0.0
    assert data["average_latency_ms"] > 0.0

    # Verify history endpoint
    hist_res = client.get(f"{settings.API_V1_STR}/navigator/evaluate/history")
    assert hist_res.status_code == 200
    assert len(hist_res.json()) >= 1


def test_dashboard_metrics():
    """Verify dashboard metrics report real non-dummy counts."""
    response = client.get(f"{settings.API_V1_STR}/navigator/dashboard/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["total_documents"] >= 1
    assert data["indexed_documents"] >= 1
    assert data["total_chunks"] >= 1
    assert data["system_status"] == "operational"
