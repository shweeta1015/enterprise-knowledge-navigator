"""
Workspace Extensions API: Collections, Saved Answers, Search History, Notifications,
User Profile, Preferences, and Data Export.
"""

import csv
import io
import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.logging import logger
from backend.app.core.security import verify_password, get_password_hash
from backend.app.models.user import UserRecord
from backend.app.models.document import DocumentRecord, EvaluationRunRecord, SystemLogRecord
from backend.app.models.workspace_extras import (
    CollectionRecord, DocumentCollectionRecord, SavedAnswerRecord,
    SearchHistoryRecord, NotificationRecord, UserPreferenceRecord
)
from backend.app.schemas.workspace_extras import (
    CollectionCreate, CollectionItem, CollectionAssignRequest,
    SavedAnswerCreate, SavedAnswerItem, SavedAnswerNoteUpdate,
    SearchHistoryItem, NotificationItem, NotificationsSummaryResponse,
    ProfileUpdateRequest, PasswordChangeRequest, UserPreferenceUpdate,
    UserPreferenceResponse, UserProfileFullResponse
)
from backend.app.api.v1.auth import get_current_user

router = APIRouter()


def create_system_notification(
    db: Session,
    title: str,
    message: str,
    category: str = "system",
    user_id: Optional[str] = None
) -> NotificationRecord:
    """Helper to log real events into the notifications database."""
    notif = NotificationRecord(
        id=f"notif_{str(uuid.uuid4())[:12]}",
        user_id=user_id,
        title=title,
        message=message,
        category=category,
        is_read=False,
        created_at=datetime.now(timezone.utc)
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


# ============================================================================
# 1. COLLECTIONS & FOLDERS
# ============================================================================

@router.get("/collections", response_model=List[CollectionItem], summary="List Document Collections")
def list_collections(db: Session = Depends(get_db)):
    """Returns all document collections with item counts and document IDs."""
    collections = db.query(CollectionRecord).order_by(CollectionRecord.created_at.desc()).all()
    results = []
    for col in collections:
        doc_ids = [m.document_id for m in col.document_mappings]
        results.append(CollectionItem(
            id=col.id,
            name=col.name,
            description=col.description,
            color=col.color or "#4F46E5",
            icon=col.icon or "📁",
            document_count=len(doc_ids),
            document_ids=doc_ids,
            created_at=col.created_at.isoformat() if col.created_at else ""
        ))
    return results


@router.post("/collections", response_model=CollectionItem, status_code=status.HTTP_201_CREATED, summary="Create Collection")
def create_collection(
    payload: CollectionCreate,
    current_user: UserRecord = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Creates a new organized document folder/collection."""
    clean_name = payload.name.strip()
    existing = db.query(CollectionRecord).filter(CollectionRecord.name.ilike(clean_name)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A collection named '{clean_name}' already exists."
        )

    col = CollectionRecord(
        id=f"col_{str(uuid.uuid4())[:12]}",
        name=clean_name,
        description=payload.description.strip() if payload.description else None,
        color=payload.color or "#4F46E5",
        icon=payload.icon or "📁",
        created_by=current_user.id,
        created_at=datetime.now(timezone.utc)
    )
    db.add(col)
    db.commit()
    db.refresh(col)

    create_system_notification(
        db,
        title="Collection Created",
        message=f"Collection '{col.name}' was created by {current_user.full_name}.",
        category="system",
        user_id=current_user.id
    )

    return CollectionItem(
        id=col.id,
        name=col.name,
        description=col.description,
        color=col.color,
        icon=col.icon,
        document_count=0,
        document_ids=[],
        created_at=col.created_at.isoformat()
    )


@router.delete("/collections/{collection_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Collection")
def delete_collection(
    collection_id: str,
    current_user: UserRecord = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deletes an existing collection (leaves documents in main library)."""
    col = db.query(CollectionRecord).filter(CollectionRecord.id == collection_id).first()
    if not col:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found.")

    col_name = col.name
    db.delete(col)
    db.commit()

    create_system_notification(
        db,
        title="Collection Removed",
        message=f"Collection '{col_name}' was removed by {current_user.full_name}.",
        category="system",
        user_id=current_user.id
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/collections/{collection_id}/documents", summary="Assign Documents to Collection")
def assign_documents_to_collection(
    collection_id: str,
    payload: CollectionAssignRequest,
    current_user: UserRecord = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Adds documents into a specified collection."""
    col = db.query(CollectionRecord).filter(CollectionRecord.id == collection_id).first()
    if not col:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found.")

    added_count = 0
    for doc_id in payload.document_ids:
        # Check doc exists
        doc = db.query(DocumentRecord).filter(DocumentRecord.id == doc_id).first()
        if not doc:
            continue
        exists = db.query(DocumentCollectionRecord).filter(
            DocumentCollectionRecord.collection_id == collection_id,
            DocumentCollectionRecord.document_id == doc_id
        ).first()
        if not exists:
            mapping = DocumentCollectionRecord(
                collection_id=collection_id,
                document_id=doc_id,
                added_at=datetime.now(timezone.utc)
            )
            db.add(mapping)
            added_count += 1

    db.commit()
    return {"message": f"Successfully mapped {added_count} documents to '{col.name}'.", "collection_id": collection_id}


@router.delete("/collections/{collection_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove Document from Collection")
def remove_document_from_collection(
    collection_id: str,
    document_id: str,
    current_user: UserRecord = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Removes a document from a collection."""
    mapping = db.query(DocumentCollectionRecord).filter(
        DocumentCollectionRecord.collection_id == collection_id,
        DocumentCollectionRecord.document_id == document_id
    ).first()
    if mapping:
        db.delete(mapping)
        db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ============================================================================
# 2. SAVED ANSWERS & INSIGHTS
# ============================================================================

@router.get("/saved-answers", response_model=List[SavedAnswerItem], summary="List Saved Q&A Answers")
def list_saved_answers(
    current_user: UserRecord = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves all bookmarked AI responses with citations and user notes."""
    records = db.query(SavedAnswerRecord).order_by(SavedAnswerRecord.created_at.desc()).all()
    results = []
    for r in records:
        try:
            cits = json.loads(r.citations_json) if r.citations_json else []
        except Exception:
            cits = []
        try:
            ents = json.loads(r.entities_json) if r.entities_json else []
        except Exception:
            ents = []

        results.append(SavedAnswerItem(
            id=r.id,
            user_email=r.user_email,
            question=r.question,
            answer=r.answer,
            mode=r.mode,
            confidence_score=r.confidence_score,
            citations=cits,
            entities=ents,
            user_notes=r.user_notes,
            created_at=r.created_at.isoformat() if r.created_at else ""
        ))
    return results


@router.post("/saved-answers", response_model=SavedAnswerItem, status_code=status.HTTP_201_CREATED, summary="Bookmark AI Answer")
def save_answer(
    payload: SavedAnswerCreate,
    current_user: UserRecord = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Bookmarks an answer from the Grounded AI assistant for later review."""
    rec = SavedAnswerRecord(
        id=f"saved_{str(uuid.uuid4())[:12]}",
        user_id=current_user.id,
        user_email=current_user.email,
        question=payload.question.strip(),
        answer=payload.answer.strip(),
        mode=payload.mode,
        confidence_score=payload.confidence_score,
        citations_json=json.dumps(payload.citations),
        entities_json=json.dumps(payload.entities),
        user_notes=payload.user_notes.strip() if payload.user_notes else None,
        created_at=datetime.now(timezone.utc)
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    return SavedAnswerItem(
        id=rec.id,
        user_email=rec.user_email,
        question=rec.question,
        answer=rec.answer,
        mode=rec.mode,
        confidence_score=rec.confidence_score,
        citations=payload.citations,
        entities=payload.entities,
        user_notes=rec.user_notes,
        created_at=rec.created_at.isoformat()
    )


@router.delete("/saved-answers/{answer_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Saved Answer")
def delete_saved_answer(
    answer_id: str,
    current_user: UserRecord = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Removes a saved answer bookmark."""
    rec = db.query(SavedAnswerRecord).filter(SavedAnswerRecord.id == answer_id).first()
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved answer not found.")
    db.delete(rec)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/saved-answers/{answer_id}/note", response_model=SavedAnswerItem, summary="Update Saved Answer Note")
def update_saved_answer_note(
    answer_id: str,
    payload: SavedAnswerNoteUpdate,
    current_user: UserRecord = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates user personal note/annotation on a saved answer."""
    rec = db.query(SavedAnswerRecord).filter(SavedAnswerRecord.id == answer_id).first()
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved answer not found.")
    rec.user_notes = payload.user_notes.strip()
    db.commit()
    db.refresh(rec)

    try:
        cits = json.loads(rec.citations_json) if rec.citations_json else []
    except Exception:
        cits = []
    try:
        ents = json.loads(rec.entities_json) if rec.entities_json else []
    except Exception:
        ents = []

    return SavedAnswerItem(
        id=rec.id,
        user_email=rec.user_email,
        question=rec.question,
        answer=rec.answer,
        mode=rec.mode,
        confidence_score=rec.confidence_score,
        citations=cits,
        entities=ents,
        user_notes=rec.user_notes,
        created_at=rec.created_at.isoformat() if rec.created_at else ""
    )


# ============================================================================
# 3. SEARCH HISTORY
# ============================================================================

@router.get("/search-history", response_model=List[SearchHistoryItem], summary="Get Recent Search History")
def get_search_history(
    limit: int = Query(20, ge=1, le=100),
    current_user: UserRecord = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns recent queries and search telemetry for the current user or platform."""
    records = db.query(SearchHistoryRecord).order_by(
        SearchHistoryRecord.created_at.desc()
    ).limit(limit).all()

    return [
        SearchHistoryItem(
            id=r.id,
            query_text=r.query_text,
            search_mode=r.search_mode,
            result_count=r.result_count,
            top_score=r.top_score,
            created_at=r.created_at.isoformat() if r.created_at else ""
        ) for r in records
    ]


@router.delete("/search-history", status_code=status.HTTP_204_NO_CONTENT, summary="Clear Search History")
def clear_search_history(
    current_user: UserRecord = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clears search history records."""
    db.query(SearchHistoryRecord).delete()
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ============================================================================
# 4. NOTIFICATIONS CENTER
# ============================================================================

@router.get("/notifications", response_model=NotificationsSummaryResponse, summary="Get Notifications")
def get_notifications(
    current_user: UserRecord = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetches real-time system, ingestion, and evaluation event notifications."""
    # Fetch notifications targeted to user or broadcast (user_id is None)
    query = db.query(NotificationRecord).filter(
        (NotificationRecord.user_id == current_user.id) | (NotificationRecord.user_id.is_(None))
    ).order_by(NotificationRecord.created_at.desc())

    items = query.limit(50).all()
    unread_count = db.query(NotificationRecord).filter(
        ((NotificationRecord.user_id == current_user.id) | (NotificationRecord.user_id.is_(None))),
        NotificationRecord.is_read.is_(False)
    ).count()

    return NotificationsSummaryResponse(
        unread_count=unread_count,
        total_count=len(items),
        items=[
            NotificationItem(
                id=n.id,
                title=n.title,
                message=n.message,
                category=n.category,
                is_read=n.is_read,
                created_at=n.created_at.isoformat() if n.created_at else ""
            ) for n in items
        ]
    )


@router.patch("/notifications/{notif_id}/read", summary="Mark Notification as Read")
def mark_notification_read(
    notif_id: str,
    current_user: UserRecord = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marks a single notification as read."""
    notif = db.query(NotificationRecord).filter(NotificationRecord.id == notif_id).first()
    if notif:
        notif.is_read = True
        db.commit()
    return {"status": "success", "id": notif_id}


@router.post("/notifications/mark-all-read", summary="Mark All Notifications as Read")
def mark_all_notifications_read(
    current_user: UserRecord = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marks all notifications for the user as read."""
    db.query(NotificationRecord).filter(
        ((NotificationRecord.user_id == current_user.id) | (NotificationRecord.user_id.is_(None))),
        NotificationRecord.is_read.is_(False)
    ).update({"is_read": True}, synchronize_session=False)
    db.commit()
    return {"status": "success", "message": "All notifications marked as read."}


# ============================================================================
# 5. PERSONAL PROFILE & USER PREFERENCES
# ============================================================================

def _get_or_create_preferences(db: Session, user_id: str) -> UserPreferenceRecord:
    prefs = db.query(UserPreferenceRecord).filter(UserPreferenceRecord.user_id == user_id).first()
    if not prefs:
        prefs = UserPreferenceRecord(
            user_id=user_id,
            default_search_mode="hybrid",
            default_top_k=5,
            graphrag_enabled=True,
            email_notifications=False,
            compact_table_view=False,
            updated_at=datetime.now(timezone.utc)
        )
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    return prefs


@router.get("/profile/me", response_model=UserProfileFullResponse, summary="Get Current User Profile & Preferences")
def get_user_profile(
    current_user: UserRecord = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns detailed user account information and customizable UI preferences."""
    prefs = _get_or_create_preferences(db, current_user.id)
    return UserProfileFullResponse(
        id=current_user.id,
        email=current_user.email,
        phone_number=current_user.phone_number,
        full_name=current_user.full_name,
        role=current_user.role,
        organization=current_user.organization,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at.isoformat() if current_user.created_at else None,
        last_login_at=current_user.last_login_at.isoformat() if current_user.last_login_at else None,
        preferences=UserPreferenceResponse(
            default_search_mode=prefs.default_search_mode,
            default_top_k=prefs.default_top_k,
            graphrag_enabled=prefs.graphrag_enabled,
            email_notifications=prefs.email_notifications,
            compact_table_view=prefs.compact_table_view
        )
    )


@router.patch("/profile/update", summary="Update User Profile Information")
def update_profile(
    payload: ProfileUpdateRequest,
    current_user: UserRecord = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates the user's display name, organization, and phone number."""
    current_user.full_name = payload.full_name.strip()
    current_user.organization = payload.organization.strip()
    if payload.phone_number is not None:
        current_user.phone_number = payload.phone_number.strip() if payload.phone_number.strip() else None
    db.commit()
    db.refresh(current_user)

    create_system_notification(
        db,
        title="Profile Updated",
        message="Your profile details have been successfully updated.",
        category="security",
        user_id=current_user.id
    )

    return {
        "status": "success",
        "message": "Profile updated successfully.",
        "user": current_user.to_dict()
    }


@router.post("/profile/change-password", summary="Change Password")
def change_password(
    payload: PasswordChangeRequest,
    current_user: UserRecord = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verifies existing password and securely hashes new password."""
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password verification failed. Please check your existing password."
        )

    if len(payload.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 6 characters in length."
        )

    current_user.hashed_password = get_password_hash(payload.new_password)
    db.commit()

    create_system_notification(
        db,
        title="Security Alert: Password Changed",
        message="Your account password was updated successfully.",
        category="security",
        user_id=current_user.id
    )

    return {"status": "success", "message": "Password changed successfully."}


@router.patch("/profile/preferences", response_model=UserPreferenceResponse, summary="Update Preferences")
def update_preferences(
    payload: UserPreferenceUpdate,
    current_user: UserRecord = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Saves user personal interface preferences (search mode, top-k, graphrag toggle)."""
    prefs = _get_or_create_preferences(db, current_user.id)

    if payload.default_search_mode is not None:
        if payload.default_search_mode in ["hybrid", "semantic", "keyword"]:
            prefs.default_search_mode = payload.default_search_mode
    if payload.default_top_k is not None:
        prefs.default_top_k = max(1, min(10, payload.default_top_k))
    if payload.graphrag_enabled is not None:
        prefs.graphrag_enabled = payload.graphrag_enabled
    if payload.email_notifications is not None:
        prefs.email_notifications = payload.email_notifications
    if payload.compact_table_view is not None:
        prefs.compact_table_view = payload.compact_table_view

    prefs.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(prefs)

    return UserPreferenceResponse(
        default_search_mode=prefs.default_search_mode,
        default_top_k=prefs.default_top_k,
        graphrag_enabled=prefs.graphrag_enabled,
        email_notifications=prefs.email_notifications,
        compact_table_view=prefs.compact_table_view
    )


# ============================================================================
# 6. REPORTS & DATA EXPORT CENTER
# ============================================================================

@router.get("/reports/export/documents", summary="Export Documents Inventory (CSV/JSON)")
def export_documents(
    format: str = Query("csv", pattern="^(csv|json)$"),
    current_user: UserRecord = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Exports indexed document repository inventory as CSV or JSON."""
    docs = db.query(DocumentRecord).order_by(DocumentRecord.created_at.desc()).all()

    if format == "json":
        data = [
            {
                "id": d.id,
                "filename": d.filename,
                "file_type": d.file_type,
                "file_size_bytes": d.file_size_bytes,
                "status": d.status,
                "page_count": d.page_count,
                "chunk_count": d.chunk_count,
                "entity_count": d.entity_count,
                "content_hash": d.content_hash,
                "created_at": d.created_at.isoformat() if d.created_at else None
            } for d in docs
        ]
        return data

    # CSV Format
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Filename", "File Type", "Size (Bytes)", "Status", "Pages", "Chunks", "Entities", "SHA-256 Hash", "Created At"])
    for d in docs:
        writer.writerow([
            d.id,
            d.filename,
            d.file_type,
            d.file_size_bytes,
            d.status,
            d.page_count,
            d.chunk_count,
            d.entity_count,
            d.content_hash,
            d.created_at.isoformat() if d.created_at else ""
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=documents_inventory.csv"}
    )


@router.get("/reports/export/evaluations", summary="Export Evaluation Runs History (CSV/JSON)")
def export_evaluations(
    format: str = Query("csv", pattern="^(csv|json)$"),
    current_user: UserRecord = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Exports quantitative evaluation benchmarks as CSV or JSON."""
    runs = db.query(EvaluationRunRecord).order_by(EvaluationRunRecord.run_timestamp.desc()).all()

    if format == "json":
        return [
            {
                "id": r.id,
                "run_timestamp": r.run_timestamp.isoformat() if r.run_timestamp else None,
                "query_count": r.query_count,
                "precision_at_k": r.precision_at_k,
                "recall_at_k": r.recall_at_k,
                "mrr_score": r.mrr_score,
                "groundedness_score": r.groundedness_score,
                "average_latency_ms": r.average_latency_ms,
                "summary_notes": r.summary_notes
            } for r in runs
        ]

    # CSV Format
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Run ID", "Timestamp", "Queries", "Precision@K", "Recall@K", "MRR", "Groundedness", "Latency (ms)", "Notes"])
    for r in runs:
        writer.writerow([
            r.id,
            r.run_timestamp.isoformat() if r.run_timestamp else "",
            r.query_count,
            round(r.precision_at_k, 4),
            round(r.recall_at_k, 4),
            round(r.mrr_score, 4),
            round(r.groundedness_score, 4),
            round(r.average_latency_ms, 2),
            r.summary_notes or ""
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=evaluation_history.csv"}
    )


@router.get("/reports/export/audit-logs", summary="Export Operational Audit Logs (CSV/JSON)")
def export_audit_logs(
    format: str = Query("csv", pattern="^(csv|json)$"),
    current_user: UserRecord = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Exports system telemetry audit logs as CSV or JSON."""
    logs = db.query(SystemLogRecord).order_by(SystemLogRecord.id.desc()).limit(500).all()

    if format == "json":
        return [
            {
                "id": l.id,
                "level": l.level,
                "message": l.message,
                "created_at": l.created_at.isoformat() if l.created_at else None
            } for l in logs
        ]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Log ID", "Level", "Message", "Timestamp"])
    for l in logs:
        writer.writerow([
            l.id,
            l.level,
            l.message,
            l.created_at.isoformat() if l.created_at else ""
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_logs.csv"}
    )
