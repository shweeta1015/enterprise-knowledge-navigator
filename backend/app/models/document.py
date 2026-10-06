"""
SQLAlchemy models for persistent storage of documents and system metrics.
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean
from backend.app.core.database import Base


class DocumentRecord(Base):
    """Stores metadata and processing status for ingested documents."""
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=False)
    status = Column(String(50), default="uploaded", index=True) # uploaded, processing, indexed, error
    chunk_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    error_message = Column(Text, nullable=True)


class SystemLogRecord(Base):
    """Stores operational events and audit logs."""
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
