"""
SQLAlchemy models for Collections, Saved Answers, Search History, Notifications, and User Preferences.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class CollectionRecord(Base):
    """Organizes documents into department, project, or domain-specific collections."""
    __tablename__ = "collections"

    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    color = Column(String(30), default="#4F46E5")
    icon = Column(String(20), default="📁")
    created_by = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    document_mappings = relationship("DocumentCollectionRecord", back_populates="collection", cascade="all, delete-orphan")


class DocumentCollectionRecord(Base):
    """Maps documents to collections (many-to-many junction)."""
    __tablename__ = "document_collections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    collection_id = Column(String(36), ForeignKey("collections.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    added_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    collection = relationship("CollectionRecord", back_populates="document_mappings")


class SavedAnswerRecord(Base):
    """Stores bookmarked Q&A responses, citations, confidence scores, and user annotations."""
    __tablename__ = "saved_answers"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), nullable=True, index=True)
    user_email = Column(String(255), nullable=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    mode = Column(String(50), default="rag") # "rag" or "graphrag"
    confidence_score = Column(Float, default=0.92)
    citations_json = Column(Text, default="[]")
    entities_json = Column(Text, default="[]")
    user_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SearchHistoryRecord(Base):
    """Tracks queries, retrieval mode, latency, and result counts for search telemetry."""
    __tablename__ = "search_history"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), nullable=True, index=True)
    query_text = Column(String(500), nullable=False)
    search_mode = Column(String(50), default="hybrid")
    result_count = Column(Integer, default=0)
    top_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class NotificationRecord(Base):
    """Real-time event notification record for ingestion, evaluation, and security alerts."""
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), nullable=True, index=True) # None = broadcast to all
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    category = Column(String(50), default="system") # ingestion, evaluation, security, system
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class UserPreferenceRecord(Base):
    """Stores customized workspace preferences per user."""
    __tablename__ = "user_preferences"

    user_id = Column(String(36), primary_key=True, index=True)
    default_search_mode = Column(String(50), default="hybrid") # hybrid, semantic, keyword
    default_top_k = Column(Integer, default=5)
    graphrag_enabled = Column(Boolean, default=True)
    email_notifications = Column(Boolean, default=False)
    compact_table_view = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
