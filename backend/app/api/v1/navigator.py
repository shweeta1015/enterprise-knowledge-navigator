"""
REST API Endpoints for Documents, Retrieval, Grounded RAG, Knowledge Graph, and Evaluation.
"""

import os
import re
import shutil
import uuid
from pathlib import Path
from typing import List, Optional, Set
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.logging import logger
from backend.app.models.user import UserRecord
from backend.app.models.document import (
    DocumentRecord, ChunkRecord, EntityRecord, RelationRecord, EvaluationRunRecord
)
from backend.app.api.v1.auth import get_optional_current_user, check_document_access
from backend.app.services.document_processor import document_processor
from backend.app.services.vector_index import vector_index_service
from backend.app.services.knowledge_graph import knowledge_graph_service
from backend.app.services.rag_assistant import rag_assistant_service
from backend.app.services.evaluation_service import evaluation_service
from backend.app.schemas.navigator import (
    DocumentItem, DocumentListResponse, DocumentDetailResponse,
    SearchRequest, SearchResponse, AskRequest, AskResponse,
    GraphResponse, EvalRunResponse, DashboardMetricsResponse
)

router = APIRouter()


def get_allowed_document_ids(db: Session, user: Optional[UserRecord]) -> Set[str]:
    """Returns the set of document IDs that the given user has permission to view/search."""
    all_docs = db.query(DocumentRecord).all()
    return {d.id for d in all_docs if check_document_access(d, user, operation="view")}


# ============================================================================
# 1. DOCUMENT INGESTION & MANAGEMENT
# ============================================================================

@router.post("/documents/upload", response_model=DocumentItem, summary="Upload & Ingest Enterprise Document")
async def upload_document(
    file: UploadFile = File(...),
    access_level: str = Form("internal"),
    allowed_roles: Optional[str] = Form(None),
    current_user: Optional[UserRecord] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    Uploads a PDF, DOCX, or TXT file, performs validation, text extraction,
    chunking, vector indexing, and knowledge graph extraction with multi-tenant access tags.
    """
    raw_filename = file.filename or "uploaded_document"
    clean_name = re.sub(r'[\x00/\\:*?"<>|]', '_', Path(raw_filename).name)
    safe_filename = clean_name.strip() or "uploaded_document"
    ext = Path(safe_filename).suffix.lower()

    if ext not in document_processor.SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Supported formats: PDF, DOCX, TXT."
        )

    doc_id = f"doc_{str(uuid.uuid4())[:12]}"
    settings.RAW_DOCS_DIR.mkdir(parents=True, exist_ok=True)
    saved_path = settings.RAW_DOCS_DIR / f"{doc_id}_{safe_filename}"

    # Read and save file safely
    try:
        with open(saved_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store uploaded file on disk."
        )

    file_size = saved_path.stat().st_size
    if file_size == 0:
        saved_path.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    if file_size > document_processor.MAX_FILE_SIZE_BYTES:
        saved_path.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File exceeds maximum 25 MB limit.")

    # Duplicate detection via SHA-256 against indexed documents
    file_hash = document_processor.compute_sha256(saved_path)
    existing_doc = db.query(DocumentRecord).filter(
        DocumentRecord.content_hash == file_hash,
        DocumentRecord.status == "indexed"
    ).first()
    if existing_doc:
        saved_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Duplicate document detected. This file is already indexed as '{existing_doc.filename}'."
        )

    # Clean up any stale failed attempts with the same hash
    stale_failed = db.query(DocumentRecord).filter(
        DocumentRecord.content_hash == file_hash,
        DocumentRecord.status == "error"
    ).all()
    for failed_doc in stale_failed:
        db.delete(failed_doc)
    if stale_failed:
        db.commit()

    # Register initial DB record with access control tags
    clean_level = access_level.lower().strip() if access_level else "internal"
    if clean_level not in ("public", "internal", "confidential", "restricted"):
        clean_level = "internal"

    doc_record = DocumentRecord(
        id=doc_id,
        filename=safe_filename,
        file_type=ext.replace(".", "").upper(),
        file_size_bytes=file_size,
        file_path=str(saved_path),
        content_hash=file_hash,
        status="processing",
        owner_id=current_user.id if current_user else None,
        access_level=clean_level,
        allowed_roles=allowed_roles
    )
    db.add(doc_record)
    db.commit()

    # Process document
    try:
        pages = document_processor.extract_text(saved_path, ext)
        doc_record.page_count = len(pages)
        full_text = "\n\n".join(p["text"] for p in pages)

        # Chunk document
        chunks_data = document_processor.chunk_document(pages, chunk_size=400, chunk_overlap=60)
        doc_record.chunk_count = len(chunks_data)

        # Persist chunk records in SQLite
        for c in chunks_data:
            chunk_rec = ChunkRecord(
                id=f"{doc_id}_{c['chunk_index']}",
                document_id=doc_id,
                chunk_index=c["chunk_index"],
                page_number=c["page_number"],
                content=c["content"],
                token_count=c["token_count"]
            )
            db.add(chunk_rec)

        # Update Vector Index
        vector_index_service.add_document_chunks(doc_id, safe_filename, chunks_data)

        # Extract Knowledge Graph Entities & Relations
        entity_count, relation_count = knowledge_graph_service.extract_and_store(db, doc_id, full_text)
        doc_record.entity_count = entity_count

        doc_record.status = "indexed"
        db.commit()
        logger.info(f"Successfully indexed document '{safe_filename}': {len(chunks_data)} chunks, {entity_count} entities")

        try:
            from backend.app.api.v1.workspace import create_system_notification
            create_system_notification(
                db=db,
                title="Document Ingested",
                message=f"'{doc_record.filename}' was indexed ({doc_record.chunk_count} chunks, {doc_record.entity_count} graph entities).",
                category="ingestion"
            )
        except Exception as notif_err:
            logger.warning(f"Could not dispatch ingestion notification: {notif_err}")

    except Exception as e:
        logger.error(f"Error processing document {safe_filename}: {e}")
        db.rollback()
        # Mark document record as error without saving partial chunks
        doc_err = db.query(DocumentRecord).filter(DocumentRecord.id == doc_id).first()
        if doc_err:
            doc_err.status = "error"
            doc_err.error_message = str(e)
            db.commit()
        # Clean up any partial chunks in vector store
        vector_index_service.remove_document_chunks(doc_id)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to process and index document: {str(e)}"
        )

    db.refresh(doc_record)
    return doc_record


@router.get("/documents", response_model=DocumentListResponse, summary="List Indexed Documents")
def list_documents(
    current_user: Optional[UserRecord] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Returns all ingested enterprise documents with processing statuses and metadata, filtered by user permissions."""
    docs = db.query(DocumentRecord).order_by(DocumentRecord.created_at.desc()).all()
    accessible = [d for d in docs if check_document_access(d, current_user, operation="view")]
    return DocumentListResponse(
        total_count=len(accessible),
        documents=accessible
    )


@router.get("/documents/{document_id}", response_model=DocumentDetailResponse, summary="Get Document Details")
def get_document_details(
    document_id: str,
    current_user: Optional[UserRecord] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Returns detailed metadata, chunk previews, and extracted entities for a document, enforcing permission guards."""
    doc = db.query(DocumentRecord).filter(DocumentRecord.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if not check_document_access(doc, current_user, operation="view"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not have permission to access this document."
        )

    chunks = db.query(ChunkRecord).filter(ChunkRecord.document_id == document_id).limit(8).all()
    entities = db.query(EntityRecord).filter(EntityRecord.document_id == document_id).limit(10).all()

    return DocumentDetailResponse(
        document=doc,
        chunks_preview=[{
            "chunk_index": c.chunk_index,
            "page_number": c.page_number,
            "snippet": c.content[:250] + "..." if len(c.content) > 250 else c.content
        } for c in chunks],
        entities_sample=[{
            "name": e.name,
            "category": e.category,
            "mentions": e.mention_count
        } for e in entities]
    )


@router.delete("/documents/{document_id}", summary="Delete Document and Cleanup Indexes")
def delete_document(
    document_id: str,
    current_user: Optional[UserRecord] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Deletes document record, associated chunks, vector index entries, graph data, and file on disk with role checks."""
    doc = db.query(DocumentRecord).filter(DocumentRecord.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if current_user and not check_document_access(doc, current_user, operation="delete"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Only the document owner or an administrator can delete this document."
        )

    # Remove physical file
    file_path = Path(doc.file_path)
    if file_path.exists():
        file_path.unlink(missing_ok=True)

    # Remove vector index chunks
    vector_index_service.remove_document_chunks(document_id)

    # Delete DB records (cascades chunks, entities, relations)
    db.delete(doc)
    db.commit()

    # Refresh exported graph snapshot
    knowledge_graph_service._export_graph_json(db)

    logger.info(f"Deleted document {document_id} and cleared associated indexes.")
    return {"success": True, "message": f"Document '{doc.filename}' deleted and unindexed successfully."}


@router.post("/documents/{document_id}/reprocess", summary="Retry / Reprocess Ingestion for Document")
def reprocess_document(document_id: str, db: Session = Depends(get_db)):
    """
    Retries text extraction, chunking, vector indexing, and knowledge graph extraction
    for an existing document record.
    """
    doc = db.query(DocumentRecord).filter(DocumentRecord.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    saved_path = Path(doc.file_path)
    if not saved_path.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Original document file '{doc.filename}' is no longer present on disk."
        )

    ext = saved_path.suffix.lower()
    # Clean up previous chunks/graph associations before reprocessing
    vector_index_service.remove_document_chunks(document_id)
    db.query(ChunkRecord).filter(ChunkRecord.document_id == document_id).delete()
    db.query(EntityRecord).filter(EntityRecord.document_id == document_id).delete()
    db.query(RelationRecord).filter(RelationRecord.document_id == document_id).delete()
    db.commit()

    try:
        pages = document_processor.extract_text(saved_path, ext)
        doc.page_count = len(pages)
        full_text = "\n\n".join(p["text"] for p in pages)

        chunks_data = document_processor.chunk_document(pages, chunk_size=400, chunk_overlap=60)
        doc.chunk_count = len(chunks_data)

        for c in chunks_data:
            chunk_rec = ChunkRecord(
                id=f"{document_id}_{c['chunk_index']}",
                document_id=document_id,
                chunk_index=c["chunk_index"],
                page_number=c["page_number"],
                content=c["content"],
                token_count=c["token_count"]
            )
            db.add(chunk_rec)

        vector_index_service.add_document_chunks(document_id, doc.filename, chunks_data)
        entity_count, relation_count = knowledge_graph_service.extract_and_store(db, document_id, full_text)
        doc.entity_count = entity_count
        doc.status = "indexed"
        doc.error_message = None
        db.commit()

        return {
            "success": True,
            "message": f"Successfully reprocessed '{doc.filename}': {len(chunks_data)} chunks, {entity_count} entities extracted.",
            "document": doc
        }
    except Exception as e:
        db.rollback()
        doc.status = "error"
        doc.error_message = str(e)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Reprocessing failed: {str(e)}"
        )


@router.get("/documents/{document_id}/download", summary="Download Raw Document File")
def download_document_file(
    document_id: str,
    current_user: Optional[UserRecord] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Allows downloading the original ingested raw document file with permission verification."""
    doc = db.query(DocumentRecord).filter(DocumentRecord.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if not check_document_access(doc, current_user, operation="view"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not have permission to download this document."
        )

    file_path = Path(doc.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Original document file not found on disk.")
    return FileResponse(file_path, filename=doc.filename)


@router.get("/documents/{document_id}/preview", summary="Preview Extracted Document Text")
def preview_document_text(
    document_id: str,
    current_user: Optional[UserRecord] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Returns the full text or extracted chunk passages for document preview with permission verification."""
    doc = db.query(DocumentRecord).filter(DocumentRecord.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if not check_document_access(doc, current_user, operation="view"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not have permission to preview this document."
        )

    chunks = db.query(ChunkRecord).filter(ChunkRecord.document_id == document_id).order_by(ChunkRecord.chunk_index.asc()).all()
    preview_parts = []
    pages_dict = {}
    for c in chunks:
        preview_parts.append(f"--- [Page {c.page_number}] Section {c.chunk_index + 1} ---\n{c.content}")
        p_num = c.page_number or 1
        if p_num not in pages_dict:
            pages_dict[p_num] = []
        pages_dict[p_num].append(c.content)

    pages = []
    for p_num in sorted(pages_dict.keys()):
        pages.append({
            "page_number": p_num,
            "text": "\n\n".join(pages_dict[p_num])
        })
    if not pages:
        pages = [{"page_number": 1, "text": "No extracted text available."}]

    full_text = "\n\n".join(preview_parts)

    return {
        "id": doc.id,
        "document_id": doc.id,
        "filename": doc.filename,
        "file_type": doc.file_type,
        "file_size_bytes": doc.file_size_bytes,
        "sha256": getattr(doc, "content_hash", "") or getattr(doc, "sha256", "") or "",
        "page_count": doc.page_count or len(pages),
        "chunk_count": len(chunks),
        "pages": pages,
        "content_preview": full_text if full_text else "No extracted text available."
    }


# ============================================================================
# 2. HYBRID SEARCH & RETRIEVAL
# ============================================================================

@router.post("/search", response_model=SearchResponse, summary="Execute Hybrid / Semantic / Keyword Search")
def execute_search(
    payload: SearchRequest,
    current_user: Optional[UserRecord] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Executes multi-mode document retrieval (semantic vector, keyword, or hybrid fusion) restricted to authorized documents."""
    allowed_ids = get_allowed_document_ids(db, current_user)
    if payload.document_id and payload.document_id not in allowed_ids:
        return SearchResponse(
            query=payload.query,
            mode=payload.mode,
            total_found=0,
            results=[]
        )

    mode = payload.mode.lower()
    if mode == "semantic":
        results = vector_index_service.semantic_search(
            query=payload.query, top_k=payload.top_k, document_id=payload.document_id, allowed_doc_ids=allowed_ids
        )
    elif mode == "keyword":
        results = vector_index_service.keyword_search(
            query=payload.query, top_k=payload.top_k, document_id=payload.document_id, allowed_doc_ids=allowed_ids
        )
    else:
        results = vector_index_service.hybrid_search(
            query=payload.query, top_k=payload.top_k, document_id=payload.document_id, allowed_doc_ids=allowed_ids
        )

    formatted = [{
        "chunk_id": r.get("chunk_id", ""),
        "document_id": r.get("document_id", ""),
        "filename": r.get("filename", ""),
        "page_number": r.get("page_number", 1),
        "chunk_index": r.get("chunk_index", 0),
        "content": r.get("content", ""),
        "score": r.get("score", 0.0),
        "retrieval_mode": r.get("retrieval_mode", mode)
    } for r in results]

    # Log search history record
    try:
        from backend.app.models.workspace_extras import SearchHistoryRecord
        from datetime import datetime, timezone
        sh_rec = SearchHistoryRecord(
            id=f"sh_{str(uuid.uuid4())[:12]}",
            query_text=payload.query,
            search_mode=mode,
            result_count=len(formatted),
            top_score=formatted[0]["score"] if formatted else 0.0,
            created_at=datetime.now(timezone.utc)
        )
        db.add(sh_rec)
        db.commit()
    except Exception as sh_err:
        logger.warning(f"Could not persist search history: {sh_err}")

    return SearchResponse(
        query=payload.query,
        mode=mode,
        total_found=len(formatted),
        results=formatted
    )


# ============================================================================
# 3. GROUNDED RAG & GRAPHRAG ASSISTANT
# ============================================================================

@router.post("/ask", response_model=AskResponse, summary="Grounded Enterprise RAG & GraphRAG Answering")
def ask_question(
    payload: AskRequest,
    current_user: Optional[UserRecord] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Answers natural-language enterprise queries strictly backed by retrieved evidence and citations, gated by permissions."""
    allowed_ids = get_allowed_document_ids(db, current_user)
    if payload.document_filter and payload.document_filter not in allowed_ids:
        return AskResponse(
            question=payload.question,
            answer="Access Restricted: You do not have authorization to query the specified document.",
            confidence=0.0,
            is_grounded=False,
            sources=[],
            graph_evidence=[],
            retrieval_mode="access_restricted",
            searched_chunks_count=0,
            verification_status="refused",
            claim_support_rate=0.0,
            verified_claims_count=0,
            unverified_claims_count=0,
            contradictions_detected=[],
            synthesis_engine="access_guard"
        )

    ans_data = rag_assistant_service.query(
        db=db,
        question=payload.question,
        top_k=payload.top_k,
        enable_graphrag=payload.enable_graphrag,
        document_filter=payload.document_filter,
        allowed_doc_ids=allowed_ids
    )
    return AskResponse(**ans_data)


# ============================================================================
# 4. KNOWLEDGE GRAPH
# ============================================================================

@router.get("/graph", response_model=GraphResponse, summary="Fetch Knowledge Graph Entities and Relations")
def get_knowledge_graph(
    category: Optional[str] = Query(None, description="Optional category filter (PERSON, ORG, TECH, PRODUCT, POLICY)"),
    current_user: Optional[UserRecord] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Returns interactive Knowledge Graph nodes and edges for exploration, filtered by authorized documents."""
    allowed_ids = get_allowed_document_ids(db, current_user)
    data = knowledge_graph_service.get_graph_data(db, filter_category=category, allowed_doc_ids=allowed_ids)
    return GraphResponse(**data)


# ============================================================================
# 5. EVALUATION & QUALITY TELEMETRY
# ============================================================================

@router.post("/evaluate/run", response_model=EvalRunResponse, summary="Execute Evaluation Benchmark")
def run_evaluation_suite(
    k: int = Query(3, ge=1, le=10),
    db: Session = Depends(get_db)
):
    """Executes quantitative evaluation measuring Precision@K, Recall@K, MRR, groundedness, and latency."""
    res = evaluation_service.run_evaluation(db, k=k)

    try:
        from backend.app.api.v1.workspace import create_system_notification
        create_system_notification(
            db=db,
            title="Evaluation Benchmark Completed",
            message=f"Quantitative run finished: P@K={res.get('precision_at_k', 0):.2f}, Recall@K={res.get('recall_at_k', 0):.2f}, MRR={res.get('mrr_score', 0):.2f}.",
            category="evaluation"
        )
    except Exception as ev_err:
        logger.warning(f"Could not dispatch evaluation notification: {ev_err}")

    return EvalRunResponse(**res)


@router.post("/evaluate/accuracy-benchmark", summary="Execute Comprehensive High-Accuracy Grounding Benchmark")
def run_accuracy_benchmark(
    k: int = Query(3, ge=1, le=10),
    db: Session = Depends(get_db)
):
    """
    Executes a rigorous 7-category accuracy, evidence-verification, and security benchmark.
    Tests: factual exactness, numerical precision, paraphrased queries, multi-document synthesis,
    abstention on unanswerable queries, contradiction detection, and prompt-injection defense.
    """
    res = evaluation_service.run_accuracy_benchmark(db, k=k)
    try:
        from backend.app.api.v1.workspace import create_system_notification
        create_system_notification(
            db=db,
            title="Accuracy Benchmark Finished",
            message=f"Benchmark: {res['passed_cases']}/{res['total_benchmark_cases']} passed. Citations: {res['metrics']['citation_correctness_rate']*100:.0f}%, Claim Support: {res['metrics']['claim_support_rate']*100:.0f}%.",
            category="evaluation"
        )
    except Exception as ev_err:
        logger.warning(f"Could not dispatch benchmark notification: {ev_err}")

    return res


@router.get("/evaluate/history", summary="Get Evaluation Run History")
def get_evaluation_history(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Returns historical evaluation benchmark records from the database."""
    return evaluation_service.get_evaluation_history(db, limit=limit)


# ============================================================================
# 6. DASHBOARD & SYSTEM METRICS
# ============================================================================

@router.get("/dashboard/metrics", response_model=DashboardMetricsResponse, summary="Get Live Dashboard Metrics")
def get_dashboard_metrics(db: Session = Depends(get_db)):
    """Computes real-time system metrics directly from active database records and indexes."""
    total_docs = db.query(DocumentRecord).count()
    indexed_docs = db.query(DocumentRecord).filter(DocumentRecord.status == "indexed").count()
    total_chunks = db.query(ChunkRecord).count()
    total_entities = db.query(EntityRecord).count()
    total_relations = db.query(RelationRecord).count()

    latest_eval = db.query(EvaluationRunRecord).order_by(EvaluationRunRecord.run_timestamp.desc()).first()

    # Calculate stored files size
    storage_bytes = 0
    if settings.RAW_DOCS_DIR.exists():
        for f in settings.RAW_DOCS_DIR.glob("*"):
            if f.is_file():
                storage_bytes += f.stat().st_size

    return DashboardMetricsResponse(
        total_documents=total_docs,
        indexed_documents=indexed_docs,
        total_chunks=total_chunks,
        total_entities=total_entities,
        total_relations=total_relations,
        storage_size_bytes=storage_bytes,
        latest_precision=latest_eval.precision_at_k if latest_eval else None,
        latest_mrr=latest_eval.mrr_score if latest_eval else None,
        system_status="operational"
    )
