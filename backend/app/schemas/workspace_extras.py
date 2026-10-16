"""
Pydantic schemas for Collections, Saved Answers, Notifications, Profile, and User Preferences.
"""

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


# ============================================================================
# COLLECTIONS SCHEMAS
# ============================================================================

class CollectionCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Collection name")
    description: Optional[str] = Field(None, max_length=500, description="Collection purpose or description")
    color: Optional[str] = Field("#4F46E5", max_length=30)
    icon: Optional[str] = Field("📁", max_length=10)


class CollectionItem(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    color: str
    icon: str
    document_count: int = 0
    document_ids: List[str] = []
    created_at: str


class CollectionAssignRequest(BaseModel):
    document_ids: List[str]


# ============================================================================
# SAVED ANSWERS SCHEMAS
# ============================================================================

class SavedAnswerCreate(BaseModel):
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)
    mode: str = Field("rag")
    confidence_score: float = Field(0.92)
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    entities: List[Dict[str, Any]] = Field(default_factory=list)
    user_notes: Optional[str] = None


class SavedAnswerItem(BaseModel):
    id: str
    user_email: Optional[str] = None
    question: str
    answer: str
    mode: str
    confidence_score: float
    citations: List[Dict[str, Any]]
    entities: List[Dict[str, Any]]
    user_notes: Optional[str] = None
    created_at: str


class SavedAnswerNoteUpdate(BaseModel):
    user_notes: str = Field("", max_length=2000)


# ============================================================================
# SEARCH HISTORY SCHEMAS
# ============================================================================

class SearchHistoryItem(BaseModel):
    id: str
    query_text: str
    search_mode: str
    result_count: int
    top_score: float
    created_at: str


# ============================================================================
# NOTIFICATIONS SCHEMAS
# ============================================================================

class NotificationItem(BaseModel):
    id: str
    title: str
    message: str
    category: str
    is_read: bool
    created_at: str


class NotificationsSummaryResponse(BaseModel):
    unread_count: int
    total_count: int
    items: List[NotificationItem]


# ============================================================================
# PROFILE & PREFERENCES SCHEMAS
# ============================================================================

class ProfileUpdateRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    organization: str = Field(..., min_length=2, max_length=100)
    phone_number: Optional[str] = None


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6, max_length=128)


class UserPreferenceUpdate(BaseModel):
    default_search_mode: Optional[str] = None
    default_top_k: Optional[int] = None
    graphrag_enabled: Optional[bool] = None
    email_notifications: Optional[bool] = None
    compact_table_view: Optional[bool] = None


class UserPreferenceResponse(BaseModel):
    default_search_mode: str = "hybrid"
    default_top_k: int = 5
    graphrag_enabled: bool = True
    email_notifications: bool = False
    compact_table_view: bool = False


class UserProfileFullResponse(BaseModel):
    id: str
    email: str
    phone_number: Optional[str] = None
    full_name: str
    role: str
    organization: str
    is_active: bool
    is_verified: Optional[bool] = True
    created_at: Optional[str] = None
    last_login_at: Optional[str] = None
    preferences: UserPreferenceResponse
