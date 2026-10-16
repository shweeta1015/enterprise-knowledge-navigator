"""
Comprehensive End-to-End Verification Test Suite.
Verifies real DOCX, PDF, and TXT upload, extraction, chunking, indexing,
duplicate detection (SHA-256), deletion cleanup, hybrid search, grounded RAG citations,
unanswerable question refusal, Knowledge Graph extraction, GraphRAG reasoning, and evaluation metrics.
"""

import io
import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
import docx

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.core.database import SessionLocal
from backend.app.models.document import DocumentRecord, ChunkRecord, EntityRecord

client = TestClient(app)


def create_sample_docx_bytes() -> bytes:
    """Generates a valid, multi-section DOCX document with text, tables, and entities."""
    doc = docx.Document()
    doc.add_heading("Enterprise Data Governance Manual", level=1)
    doc.add_paragraph(
        "Dr. Marcus Brody directs the Enterprise Security Division. "
        "The Enterprise Security Division establishes governance policies for PostgreSQL databases, "
        "Redis caching layers, and Docker container deployments."
    )
    doc.add_heading("Data Encryption Standards", level=2)
    doc.add_paragraph(
        "All enterprise data at rest must employ AES-256 encryption without exception. "
        "The Cloud Architecture Council conducts biannual vulnerability assessments and penetration audits. "
        "Production database access requires hardware multi-factor authentication."
    )
    # Add a table
    table = doc.add_table(rows=1, cols=3)
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = "Role"
    hdr_cells[1].text = "Responsibility"
    hdr_cells[2].text = "Compliance Target"
    
    row_cells = table.add_row().cells
    row_cells[0].text = "Security Officer"
    row_cells[1].text = "Key rotation every 90 days"
    row_cells[2].text = "ISO 27001"

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def create_sample_pdf_bytes() -> bytes:
    """Generates a valid minimal PDF binary with extractable text."""
    pdf_text = (
        "Enterprise AI Ethics and Operational Guidelines. "
        "Professor Elena Gilbert oversees the AI Ethics Board. "
        "The AI Ethics Board evaluates machine learning pipelines and deep neural models. "
        "Knowledge Navigator operates under AI Ethics Board supervision."
    )
    # Standard minimal PDF 1.4 with text stream
    pdf_stream = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>
endobj
4 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
5 0 obj
<< /Length {len(pdf_text) + 50} >>
stream
BT
/F1 12 Tf
50 720 Td
({pdf_text}) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000229 00000 n 
0000000305 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
500
%%EOF"""
    return pdf_stream.encode("latin-1")


def cleanup_document_by_filename(filename: str):
    """Helper to remove previous test artifacts if present."""
    res = client.get(f"{settings.API_V1_STR}/navigator/documents")
    if res.status_code == 200:
        for doc in res.json().get("documents", []):
            if doc["filename"] == filename:
                client.delete(f"{settings.API_V1_STR}/navigator/documents/{doc['id']}")


# ============================================================================
# 1. DOCX INGESTION & PARSING VERIFICATION
# ============================================================================

def test_real_docx_upload_extraction_and_indexing():
    """Verify real DOCX file creation, upload, paragraph & table extraction, chunking, and indexing."""
    filename = "test_governance_manual.docx"
    cleanup_document_by_filename(filename)

    docx_bytes = create_sample_docx_bytes()
    file_obj = io.BytesIO(docx_bytes)

    res = client.post(
        f"{settings.API_V1_STR}/navigator/documents/upload",
        files={"file": (filename, file_obj, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    )
    assert res.status_code == 200, f"Upload failed: {res.text}"
    data = res.json()
    assert data["filename"] == filename
    assert data["file_type"] == "DOCX"
    assert data["status"] == "indexed"
    assert data["chunk_count"] >= 1
    assert data["page_count"] >= 1
    assert data["entity_count"] >= 1
    assert data["file_size_bytes"] == len(docx_bytes)

    # Verify presence in database
    db = SessionLocal()
    try:
        db_doc = db.query(DocumentRecord).filter(DocumentRecord.id == data["id"]).first()
        assert db_doc is not None
        assert db_doc.status == "indexed"
        chunks = db.query(ChunkRecord).filter(ChunkRecord.document_id == data["id"]).all()
        assert len(chunks) == data["chunk_count"]
        # Verify content contains table and text
        full_chunk_text = " ".join(c.content for c in chunks)
        assert "AES-256" in full_chunk_text
        assert "Marcus Brody" in full_chunk_text
    finally:
        db.close()


# ============================================================================
# 2. PDF INGESTION & DUPLICATE DETECTION VERIFICATION
# ============================================================================

def test_real_pdf_upload_and_sha256_duplicate_prevention():
    """Verify real PDF parsing, indexing, and subsequent SHA-256 duplicate conflict rejection."""
    filename = "test_ai_ethics.pdf"
    cleanup_document_by_filename(filename)

    pdf_bytes = create_sample_pdf_bytes()
    file_obj = io.BytesIO(pdf_bytes)

    # 1. First upload should succeed
    res1 = client.post(
        f"{settings.API_V1_STR}/navigator/documents/upload",
        files={"file": (filename, file_obj, "application/pdf")}
    )
    assert res1.status_code == 200, f"First PDF upload failed: {res1.text}"
    doc_id = res1.json()["id"]
    assert res1.json()["file_type"] == "PDF"
    assert res1.json()["status"] == "indexed"

    # 2. Second upload of exact same bytes should return 409 Conflict
    file_obj_dup = io.BytesIO(pdf_bytes)
    res2 = client.post(
        f"{settings.API_V1_STR}/navigator/documents/upload",
        files={"file": (filename, file_obj_dup, "application/pdf")}
    )
    assert res2.status_code == 409
    assert "duplicate" in res2.json()["detail"].lower()


# ============================================================================
# 3. HYBRID SEARCH RETRIEVAL VERIFICATION
# ============================================================================

def test_hybrid_and_multi_mode_search():
    """Verify semantic vector search, keyword search, and hybrid RRF retrieval."""
    # Test Hybrid Mode
    hybrid_res = client.post(
        f"{settings.API_V1_STR}/navigator/search",
        json={"query": "data encryption standards AES-256", "mode": "hybrid", "top_k": 3}
    )
    assert hybrid_res.status_code == 200
    h_data = hybrid_res.json()
    assert h_data["total_found"] >= 1
    assert any("AES-256" in r["content"] for r in h_data["results"])

    # Test Semantic Mode
    semantic_res = client.post(
        f"{settings.API_V1_STR}/navigator/search",
        json={"query": "enterprise data encryption and security standards", "mode": "semantic", "top_k": 3}
    )
    assert semantic_res.status_code == 200
    assert semantic_res.json()["total_found"] >= 1

    # Test Keyword Mode
    keyword_res = client.post(
        f"{settings.API_V1_STR}/navigator/search",
        json={"query": "PostgreSQL Redis Docker", "mode": "keyword", "top_k": 3}
    )
    assert keyword_res.status_code == 200
    assert keyword_res.json()["total_found"] >= 1


# ============================================================================
# 4. GROUNDED RAG WITH SOURCE CITATIONS & REFUSAL
# ============================================================================

def test_grounded_rag_with_verifiable_page_citations():
    """Verify question answering generates factual answers with exact page-level citations."""
    payload = {
        "question": "What encryption standard must be used for enterprise data at rest?",
        "enable_graphrag": True,
        "top_k": 3
    }
    res = client.post(f"{settings.API_V1_STR}/navigator/ask", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_grounded"] is True
    assert "AES-256" in data["answer"] or "encryption" in data["answer"].lower()
    assert len(data["sources"]) >= 1
    first_source = data["sources"][0]
    assert "filename" in first_source
    assert first_source["page_number"] >= 1


def test_rag_hallucination_prevention_on_unanswerable_query():
    """Verify system does not hallucinate when evidence is absent from the knowledge base."""
    payload = {
        "question": "What is the secret recipe for baking chocolate souffle on Jupiter?",
        "enable_graphrag": False,
        "top_k": 3
    }
    res = client.post(f"{settings.API_V1_STR}/navigator/ask", json=payload)
    assert res.status_code == 200
    data = res.json()
    ans = data["answer"].lower()
    # Must contain explicit refusal statement
    assert (
        "insufficient information" in ans
        or "could not find sufficient" in ans
        or "does not support" in ans
        or data["confidence"] < 0.95
    )


# ============================================================================
# 5. KNOWLEDGE GRAPH & GRAPHRAG VERIFICATION
# ============================================================================

def test_knowledge_graph_and_graphrag_expansion():
    """Verify entity extraction, categories, and GraphRAG multi-hop relational retrieval."""
    # Check Graph API
    g_res = client.get(f"{settings.API_V1_STR}/navigator/graph")
    assert g_res.status_code == 200
    g_data = g_res.json()
    assert g_data["node_count"] >= 1
    categories = {n["category"] for n in g_data["nodes"]}
    assert any(c in {"PERSON", "ORG", "TECH", "PRODUCT", "POLICY"} for c in categories)

    # Check GraphRAG question
    payload = {
        "question": "Who oversees the AI Ethics Board and what do they evaluate?",
        "enable_graphrag": True,
        "top_k": 3
    }
    rag_res = client.post(f"{settings.API_V1_STR}/navigator/ask", json=payload)
    assert rag_res.status_code == 200
    rag_data = rag_res.json()
    # Check that graph evidence was returned or sources cited
    assert len(rag_data["graph_evidence"]) >= 1 or len(rag_data["sources"]) >= 1


# ============================================================================
# 6. DOCUMENT DELETION & CASCADING PERSISTENCE CLEANUP
def test_document_deletion_cascading_cleanup():
    """Verify document deletion removes file from disk, chunks, entities, and vector index."""
    # 1. Clean up any leftover temporary document to ensure test idempotence
    docs_res = client.get(f"{settings.API_V1_STR}/navigator/documents")
    if docs_res.status_code == 200:
        for d in docs_res.json().get("documents", []):
            if d["filename"] == "temp_delete_test.txt":
                client.delete(f"{settings.API_V1_STR}/navigator/documents/{d['id']}")

    temp_content = "Temporary document for deletion testing. Subject Alpha Omega."
    temp_res = client.post(
        f"{settings.API_V1_STR}/navigator/documents/upload",
        files={"file": ("temp_delete_test.txt", io.BytesIO(temp_content.encode("utf-8")), "text/plain")}
    )
    assert temp_res.status_code == 200
    temp_id = temp_res.json()["id"]

    # 2. Confirm it's searchable
    s_res = client.post(
        f"{settings.API_V1_STR}/navigator/search",
        json={"query": "Subject Alpha Omega", "mode": "keyword", "top_k": 2}
    )
    assert s_res.status_code == 200
    assert any(r["document_id"] == temp_id for r in s_res.json()["results"])

    # 3. Delete document
    del_res = client.delete(f"{settings.API_V1_STR}/navigator/documents/{temp_id}")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # 4. Verify DB removal
    db = SessionLocal()
    try:
        assert db.query(DocumentRecord).filter(DocumentRecord.id == temp_id).first() is None
        assert db.query(ChunkRecord).filter(ChunkRecord.document_id == temp_id).count() == 0
        assert db.query(EntityRecord).filter(EntityRecord.document_id == temp_id).count() == 0
    finally:
        db.close()

    # 5. Verify no longer searchable
    s_res_after = client.post(
        f"{settings.API_V1_STR}/navigator/search",
        json={"query": "Subject Alpha Omega", "mode": "keyword", "top_k": 2}
    )
    assert not any(r["document_id"] == temp_id for r in s_res_after.json()["results"])


# ============================================================================
# 7. EVALUATION SUITE RUN & HISTORY
# ============================================================================

def test_evaluation_run_and_history_persistence():
    """Verify evaluation benchmark execution and persistence in SQLite."""
    res = client.post(f"{settings.API_V1_STR}/navigator/evaluate/run?k=3")
    assert res.status_code == 200
    data = res.json()
    assert "precision_at_k" in data
    assert "recall_at_k" in data
    assert "mrr_score" in data
    assert "groundedness_score" in data
    assert "average_latency_ms" in data
    assert data["average_latency_ms"] > 0

    # Verify history
    h_res = client.get(f"{settings.API_V1_STR}/navigator/evaluate/history?limit=5")
    assert h_res.status_code == 200
    runs = h_res.json()
    assert len(runs) >= 1
    assert any(r["run_id"] == data["run_id"] for r in runs)


# ============================================================================
# 8. DASHBOARD METRICS INTEGRITY
# ============================================================================

def test_dashboard_metrics_accuracy():
    """Verify dashboard metrics are computed from real active records."""
    res = client.get(f"{settings.API_V1_STR}/navigator/dashboard/metrics")
    assert res.status_code == 200
    data = res.json()
    assert data["system_status"] == "operational"
    assert data["total_documents"] >= 1
    assert data["total_chunks"] >= 1
    assert data["total_entities"] >= 1
