"""
SQLAlchemy models for persistent storage of documents, chunks, graph entities,
relationships, search/query history, and evaluation runs.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class DocumentRecord(Base):
    """Stores metadata, extraction details, and processing status for ingested documents."""
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=False)
    content_hash = Column(String(64), nullable=True, index=True) # SHA-256 for duplicate detection
    status = Column(String(50), default="uploaded", index=True) # uploaded, processing, indexed, error
    page_count = Column(Integer, default=1)
    chunk_count = Column(Integer, default=0)
    entity_count = Column(Integer, default=0)
    owner_id = Column(String(36), nullable=True, index=True)
    access_level = Column(String(50), default="internal", index=True)  # public, internal, confidential, restricted
    allowed_roles = Column(String(255), nullable=True)  # comma-separated roles permitted if restricted
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    error_message = Column(Text, nullable=True)

    # Relationships
    chunks = relationship("ChunkRecord", back_populates="document", cascade="all, delete-orphan")
    entities = relationship("EntityRecord", back_populates="document", cascade="all, delete-orphan")
    relations = relationship("RelationRecord", back_populates="document", cascade="all, delete-orphan")


class ChunkRecord(Base):
    """Stores segmented document chunks with page offsets and text representations."""
    __tablename__ = "document_chunks"

    id = Column(String(64), primary_key=True, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, default=1)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    document = relationship("DocumentRecord", back_populates="chunks")


class EntityRecord(Base):
    """Stores extracted named entities from documents for Knowledge Graph navigation."""
    __tablename__ = "graph_entities"

    id = Column(String(64), primary_key=True, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True) # PERSON, ORG, TECH, PRODUCT, CONCEPT, POLICY
    mention_count = Column(Integer, default=1)
    source_context = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    document = relationship("DocumentRecord", back_populates="entities")


class RelationRecord(Base):
    """Stores extracted semantic relationships (triples) connecting knowledge entities."""
    __tablename__ = "graph_relations"

    id = Column(String(64), primary_key=True, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    source_entity = Column(String(255), nullable=False, index=True)
    relation_type = Column(String(100), nullable=False, index=True) # MANAGES, DEVELOPS, OPERATES_IN, GOVERNS, INTEGRATES
    target_entity = Column(String(255), nullable=False, index=True)
    provenance_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    document = relationship("DocumentRecord", back_populates="relations")


class EvaluationRunRecord(Base):
    """Stores persistent quantitative evaluation runs and quality telemetry."""
    __tablename__ = "evaluation_runs"

    id = Column(String(36), primary_key=True, index=True)
    run_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    query_count = Column(Integer, nullable=False)
    precision_at_k = Column(Float, nullable=False)
    recall_at_k = Column(Float, nullable=False)
    mrr_score = Column(Float, nullable=False) # Mean Reciprocal Rank
    groundedness_score = Column(Float, nullable=False)
    average_latency_ms = Column(Float, nullable=False)
    summary_notes = Column(Text, nullable=True)


class SystemLogRecord(Base):
    """Stores operational events and audit logs."""
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
