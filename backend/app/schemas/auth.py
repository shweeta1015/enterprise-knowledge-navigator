"""
Pydantic v2 schemas for authentication, registration, and user management.
"""

from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    preferred_role: Optional[str] = None # UI convenience only; verified from DB
    remember_me: Optional[bool] = False


class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone_number: Optional[str] = None
    password: str = Field(..., min_length=6, max_length=100)
    organization: Optional[str] = "Enterprise"
    role: Optional[str] = "knowledge_worker" # Only non-admin roles allowed for public signup


class UserResponse(BaseModel):
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
    permissions: Optional[List[str]] = None

    model_config = {"from_attributes": True}


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserStatusUpdateRequest(BaseModel):
    is_active: Optional[bool] = None
    role: Optional[str] = None
    new_password: Optional[str] = None


class ProvisionUserRequest(BaseModel):
    full_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    password: str = Field(..., min_length=6)
    role: str = "knowledge_worker" # admin, knowledge_worker, analyst
    organization: Optional[str] = "Enterprise"


# Password Recovery & OTP Schemas
class ForgotPasswordRequest(BaseModel):
    identifier: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    channel: Optional[str] = "email"
    delivery_method: Optional[str] = None


class ForgotPasswordResponse(BaseModel):
    success: bool
    message: str
    session_id: str
    request_id: Optional[str] = None
    channel: str
    delivery_method: Optional[str] = None
    masked_destination: str
    cooldown_seconds: int = 60
    expires_in_seconds: int = 600


class OTPVerifyRequest(BaseModel):
    session_id: Optional[str] = None
    reset_request_id: Optional[str] = None
    otp_code: str


class OTPVerifyResponse(BaseModel):
    success: bool
    message: str
    session_id: str
    reset_token: str


class PasswordResetSubmitRequest(BaseModel):
    session_id: Optional[str] = None
    reset_token: str
    new_password: str = Field(..., min_length=6, max_length=100)
    confirm_password: Optional[str] = None


class PasswordResetSubmitResponse(BaseModel):
    success: bool
    message: str


class AuditLogResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    user_email: Optional[str] = "System"
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


# Role & Permission Management Schemas
class RoleCapabilityItem(BaseModel):
    id: str
    name: str
    description: str
    category: Optional[str] = "General"


class CustomRoleCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = ""
    permissions: List[str] = Field(default_factory=list)


class CustomRoleUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None
    is_active: Optional[bool] = None


class CustomRoleResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = ""
    permissions: List[str] = Field(default_factory=list)
    is_builtin: bool = False
    is_active: bool = True
    user_count: Optional[int] = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = {"from_attributes": True}


class UserPermissionsResponse(BaseModel):
    role_id: str
    role_name: str
    is_builtin: bool
    permissions: List[str]

