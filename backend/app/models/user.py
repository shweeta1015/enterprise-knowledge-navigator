"""
SQLAlchemy user and authorization model for Enterprise Knowledge Navigator.
"""

import json
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer
from backend.app.core.database import Base


class UserRecord(Base):
    """User account model storing credentials, profile metadata, and verified system role."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone_number = Column(String(50), nullable=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="knowledge_worker", nullable=False, index=True) # admin, knowledge_worker, analyst
    organization = Column(String(255), default="Enterprise", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login_at = Column(DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "phone_number": self.phone_number,
            "full_name": self.full_name,
            "role": self.role,
            "organization": self.organization,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None
        }


class PasswordResetOTPRecord(Base):
    """Stores cryptographically generated OTP codes for password recovery with attempt limits and expiry."""
    __tablename__ = "password_reset_otps"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), index=True, nullable=False)
    delivery_channel = Column(String(20), default="email", nullable=False) # 'email' or 'sms'
    destination = Column(String(255), nullable=False)
    otp_hash = Column(String(255), nullable=False)
    attempts_left = Column(Integer, default=5, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    reset_token = Column(String(255), nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AuditLogRecord(Base):
    """Tracks administrative and sensitive system actions for security auditability."""
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), nullable=True, index=True)
    user_email = Column(String(255), nullable=True)
    action = Column(String(100), nullable=False, index=True) # USER_LOGIN, DOC_UPLOAD, DOC_DELETE, PASSWORD_RESET, USER_ROLE_CHANGE
    resource_type = Column(String(50), nullable=False) # document, user, auth, system
    resource_id = Column(String(255), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_email": self.user_email or "System",
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class RoleRecord(Base):
    """Stores system built-in and administrator-created custom roles with granular permissions."""
    __tablename__ = "roles"

    id = Column(String(50), primary_key=True, index=True) # "admin", "knowledge_worker", "analyst", or "role_<hash>"
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    permissions = Column(Text, default="[]", nullable=False) # JSON array of capability string IDs
    is_builtin = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def get_permissions(self):
        try:
            return json.loads(self.permissions) if self.permissions else []
        except Exception:
            return []

    def set_permissions(self, perms_list):
        self.permissions = json.dumps(perms_list or [])

    def to_dict(self, user_count: int = 0):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description or "",
            "permissions": self.get_permissions(),
            "is_builtin": self.is_builtin,
            "is_active": self.is_active,
            "user_count": user_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

