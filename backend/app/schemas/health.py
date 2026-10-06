"""
Pydantic Schemas for API Requests, Responses, and System Health.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class HealthStatus(BaseModel):
    status: str = Field(..., json_schema_extra={"example": "healthy"})
    version: str = Field(..., json_schema_extra={"example": "0.1.0"})
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    environment: str = Field(..., json_schema_extra={"example": "development"})
    database_connected: bool = True
    storage_directories_ready: bool = True
    active_providers: Dict[str, str] = Field(default_factory=dict)


class SystemInfoResponse(BaseModel):
    project_name: str
    version: str
    environment: str
    python_version: str
    database_url: str
    features_available: List[str]
    storage_status: Dict[str, bool]


class StandardResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
