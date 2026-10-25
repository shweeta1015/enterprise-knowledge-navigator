"""
Authentication and Role-Based User Management API Endpoints.
"""

import re
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Any, Dict, Set
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import timedelta

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.logging import logger
from backend.app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token
from backend.app.models.user import UserRecord, PasswordResetOTPRecord, AuditLogRecord, RoleRecord
from backend.app.models.workspace_extras import NotificationRecord
from backend.app.services.notification_delivery import (
    generate_secure_otp, hash_otp, verify_otp_hash, mask_destination,
    send_otp_email, send_otp_sms, record_audit_log
)
from backend.app.schemas.auth import (
    LoginRequest, RegisterRequest, AuthTokenResponse, UserResponse,
    UserStatusUpdateRequest, ProvisionUserRequest,
    ForgotPasswordRequest, ForgotPasswordResponse,
    OTPVerifyRequest, OTPVerifyResponse,
    PasswordResetSubmitRequest, PasswordResetSubmitResponse,
    AuditLogResponse,
    RoleCapabilityItem, CustomRoleCreateRequest, CustomRoleUpdateRequest,
    CustomRoleResponse, UserPermissionsResponse
)

router = APIRouter()
security_bearer = HTTPBearer(auto_error=False)


# ============================================================================
# DEPENDENCIES FOR AUTHENTICATION & ROLE ENFORCEMENT
# ============================================================================

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db)
) -> UserRecord:
    """Extracts and validates JWT Bearer token, returning the verified active UserRecord."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing. Please sign in."
        )

    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or token is invalid. Please sign in again."
        )

    user_id = payload.get("sub")
    user = db.query(UserRecord).filter(UserRecord.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Please contact an administrator."
        )

    return user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db)
) -> Optional[UserRecord]:
    """
    Extracts and validates JWT Bearer token if present.
    If valid token is provided, returns the verified active UserRecord.
    If invalid/expired token is provided, raises 401 Unauthorized.
    If no credentials are provided, returns None.
    """
    if not credentials or not credentials.credentials:
        return None

    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or token is invalid. Please sign in again."
        )

    user_id = payload.get("sub")
    user = db.query(UserRecord).filter(UserRecord.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Please contact an administrator."
        )

    return user


def check_document_access(document: Any, user: Optional[UserRecord], operation: str = "view") -> bool:
    """
    Evaluates whether the given user has permission to view, search, or delete the document.
    - Admins have full access to all documents for all operations.
    - Document owner has full access to their own documents.
    - 'public' documents: readable by all users.
    - 'internal' documents: readable by authenticated users or default guest mode.
    - 'confidential' / 'restricted' documents:
        - Readable only by document owner, admin, or users whose role matches allowed_roles.
    - 'delete' operation:
        - Only document owner or Admin can delete.
    """
    if user and (user.role == "admin" or user.id == getattr(document, "owner_id", None)):
        return True

    level = getattr(document, "access_level", "internal") or "internal"

    if operation == "delete":
        return False

    if level in ("public", "internal"):
        return True

    # Confidential or restricted access
    if not user:
        return False

    allowed = getattr(document, "allowed_roles", None)
    if allowed:
        role_list = [r.strip().lower() for r in allowed.split(",") if r.strip()]
        if user.role.lower() in role_list:
            return True

    return False


# Platform Capabilities Matrix
PLATFORM_CAPABILITIES = [
    {
        "id": "system_admin",
        "name": "System Administration",
        "description": "Full platform administration, user provisioning, and role governance",
        "category": "Administration"
    },
    {
        "id": "audit_logs",
        "name": "Operational Audit Logs",
        "description": "Inspect tamper-evident system logs and security events",
        "category": "Administration"
    },
    {
        "id": "system_health",
        "name": "System Health & Diagnostics",
        "description": "Monitor system storage, database persistence, and pipeline health",
        "category": "Administration"
    },
    {
        "id": "doc_ingestion",
        "name": "Document Ingestion & Indexing",
        "description": "Upload enterprise PDF, DOCX, and TXT files for vector and graph extraction",
        "category": "Content & Search"
    },
    {
        "id": "doc_deletion",
        "name": "Document Deletion & Cascade Cleanup",
        "description": "Permanently delete documents and purge graph relations",
        "category": "Content & Search"
    },
    {
        "id": "search_retrieval",
        "name": "Hybrid Search & Semantic Retrieval",
        "description": "Execute lexical keyword, dense vector, and hybrid searches",
        "category": "Content & Search"
    },
    {
        "id": "qa_citations",
        "name": "Grounded AI Q&A with Citations",
        "description": "Ask questions with verifiable, grounded page citations",
        "category": "Content & Search"
    },
    {
        "id": "knowledge_graph",
        "name": "Interactive Knowledge Graph",
        "description": "Explore semantic entity relationships and GraphRAG evidence",
        "category": "Analytics & Intelligence"
    },
    {
        "id": "evaluation",
        "name": "Quality Evaluation Benchmarks",
        "description": "Execute Precision@K, Recall@K, and MRR benchmark runs",
        "category": "Analytics & Intelligence"
    },
    {
        "id": "export_center",
        "name": "Data Export Center",
        "description": "Export document catalog, evaluation benchmarks, and logs to CSV/JSON",
        "category": "Analytics & Intelligence"
    },
    {
        "id": "profile_settings",
        "name": "Profile & Settings Management",
        "description": "Manage individual credentials, contact info, and preferences",
        "category": "General"
    }
]

VALID_CAPABILITY_IDS = {c["id"] for c in PLATFORM_CAPABILITIES}


def get_user_permissions(role_id: str, db: Session) -> List[str]:
    """Retrieves list of active capability strings for a role from DB, with built-in fallbacks."""
    role = db.query(RoleRecord).filter(RoleRecord.id == role_id).first()
    if role:
        return role.get_permissions()

    if role_id == "admin":
        return [c["id"] for c in PLATFORM_CAPABILITIES]
    elif role_id == "analyst":
        return ["search_retrieval", "qa_citations", "knowledge_graph", "evaluation", "export_center", "profile_settings"]
    else:
        return ["doc_ingestion", "doc_deletion", "search_retrieval", "qa_citations", "profile_settings"]


def build_user_response(user: UserRecord, db: Session) -> UserResponse:
    """Standardized builder for UserResponse with permissions attached."""
    perms = get_user_permissions(user.role, db)
    return UserResponse(
        id=user.id,
        email=user.email,
        phone_number=user.phone_number,
        full_name=user.full_name,
        role=user.role,
        organization=user.organization,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at.isoformat() if user.created_at else None,
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        permissions=perms
    )


def require_admin(
    current_user: UserRecord = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UserRecord:
    """Enforces that the authenticated user possesses the 'admin' role or 'system_admin' capability."""
    if current_user.role == "admin":
        return current_user
    role = db.query(RoleRecord).filter(RoleRecord.id == current_user.role).first()
    if role and "system_admin" in role.get_permissions():
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied. Administrator privileges are required for this action."
    )



# ============================================================================
# 1. LOGIN
# ============================================================================

@router.post("/login", response_model=AuthTokenResponse, summary="Authenticate User & Issue Access Token")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticates user with email and password.
    Verifies user's actual database role regardless of any UI selector.
    """
    email_clean = payload.email.strip().lower()
    user = db.query(UserRecord).filter(UserRecord.email == email_clean).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        logger.warning(f"Failed authentication attempt for email: {email_clean}")
        record_audit_log(db, "LOGIN_FAILED", "auth", details=f"Failed attempt for email: {email_clean}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email address or password. Please verify your credentials."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Please contact an administrator."
        )

    # Record login timestamp & audit
    user.last_login_at = datetime.now(timezone.utc)
    record_audit_log(db, "USER_LOGIN_SUCCESS", "auth", user.id, user.email, details=f"Role: {user.role}")
    db.commit()

    token_data = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "full_name": user.full_name
    }
    access_token = create_access_token(token_data)

    logger.info(f"User {user.email} successfully logged in as verified role: '{user.role}'")

    return AuthTokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=build_user_response(user, db)
    )


# ============================================================================
# 2. PUBLIC SIGN UP
# ============================================================================

@router.post("/register", response_model=AuthTokenResponse, summary="Public Account Registration")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """
    Registers a new public user account.
    CRITICAL SECURITY: Public visitors can only register as 'knowledge_worker' or 'analyst'.
    Admin accounts cannot be self-registered.
    """
    email_clean = payload.email.strip().lower()
    
    # Check for existing email
    existing = db.query(UserRecord).filter(UserRecord.email == email_clean).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists. Please log in instead."
        )

    # Prevent public administrator registration
    requested_role = (payload.role or "knowledge_worker").strip().lower()
    if requested_role == "admin":
        logger.warning(f"Blocked attempt to self-register as Administrator for {email_clean}")
        record_audit_log(db, "UNAUTHORIZED_ADMIN_SIGNUP_ATTEMPT", "auth", details=f"Attempted for {email_clean}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Self-registration as Administrator is strictly prohibited. Administrator accounts must be provisioned internally."
        )

    if requested_role not in ["knowledge_worker", "analyst"]:
        requested_role = "knowledge_worker"

    new_user = UserRecord(
        id=f"user_{str(uuid.uuid4())[:12]}",
        email=email_clean,
        phone_number=payload.phone_number.strip() if payload.phone_number else None,
        full_name=payload.full_name.strip(),
        hashed_password=get_password_hash(payload.password),
        role=requested_role,
        organization=payload.organization.strip() if payload.organization else "Enterprise",
        is_active=True,
        is_verified=True,
        created_at=datetime.now(timezone.utc),
        last_login_at=datetime.now(timezone.utc)
    )
    db.add(new_user)
    record_audit_log(db, "USER_REGISTERED", "auth", new_user.id, new_user.email, details=f"Role: {new_user.role}")
    db.commit()
    db.refresh(new_user)

    token_data = {
        "sub": new_user.id,
        "email": new_user.email,
        "role": new_user.role,
        "full_name": new_user.full_name
    }
    access_token = create_access_token(token_data)

    logger.info(f"Registered new user {new_user.email} with role '{new_user.role}'")

    return AuthTokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=build_user_response(new_user, db)
    )


# ============================================================================
# 3. GET CURRENT PROFILE (/me)
# ============================================================================

@router.get("/me", response_model=UserResponse, summary="Get Current Authenticated User Profile")
def get_current_user_profile(
    current_user: UserRecord = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns the verified profile and active role of the authenticated caller."""
    return build_user_response(current_user, db)


# ============================================================================
# 4. ADMINISTRATOR-ONLY USER MANAGEMENT
# ============================================================================

@router.get("/users", response_model=List[UserResponse], summary="List All Users (Admin Only)")
def list_all_users(
    admin: UserRecord = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Returns the complete list of registered users in the organization."""
    users = db.query(UserRecord).order_by(UserRecord.created_at.desc()).all()
    return [build_user_response(u, db) for u in users]


@router.patch("/users/{user_id}/status", response_model=UserResponse, summary="Update User Status / Role (Admin Only)")
def update_user_status(
    user_id: str,
    payload: UserStatusUpdateRequest,
    admin: UserRecord = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Allows an administrator to activate/deactivate an account or adjust roles."""
    user = db.query(UserRecord).filter(UserRecord.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if user.id == admin.id and payload.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot deactivate their own account."
        )

    if payload.is_active is not None:
        user.is_active = payload.is_active

    if payload.role:
        role_clean = payload.role.strip().lower()
        if role_clean in ["admin", "knowledge_worker", "analyst"]:
            user.role = role_clean
        else:
            custom_role = db.query(RoleRecord).filter(
                (RoleRecord.id == role_clean) | (RoleRecord.name.ilike(payload.role.strip()))
            ).first()
            if custom_role and custom_role.is_active:
                user.role = custom_role.id
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Role '{payload.role}' does not exist or is inactive."
                )

    if payload.new_password:
        if len(payload.new_password) < 6:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 6 characters.")
        user.hashed_password = get_password_hash(payload.new_password)
        record_audit_log(
            db=db,
            action="ADMIN_RESET_PASSWORD",
            resource_type="user",
            user_id=admin.id,
            user_email=admin.email,
            resource_id=user.id,
            details=f"Password reset for {user.email} by administrator"
        )

    db.commit()
    db.refresh(user)
    logger.info(f"Admin {admin.email} updated user {user.email}: active={user.is_active}, role={user.role}")

    return build_user_response(user, db)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete User Account (Admin Only)")
def delete_user(
    user_id: str,
    admin: UserRecord = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Allows an administrator to delete a user account."""
    user = db.query(UserRecord).filter(UserRecord.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if user.id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Administrators cannot delete their own account.")

    user_email = user.email
    db.delete(user)
    db.commit()
    record_audit_log(
        db=db,
        action="ADMIN_DELETE_USER",
        resource_type="user",
        user_id=admin.id,
        user_email=admin.email,
        resource_id=user_id,
        details=f"User account {user_email} deleted by administrator"
    )
    logger.info(f"Admin {admin.email} deleted user account {user_email}")


@router.post("/users/provision", response_model=UserResponse, summary="Provision User Account (Admin Only)")
def provision_user(
    payload: ProvisionUserRequest,
    admin: UserRecord = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Allows an administrator to securely provision any user account, including new administrators."""
    email_clean = payload.email.strip().lower()
    existing = db.query(UserRecord).filter(UserRecord.email == email_clean).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A user with this email already exists.")

    req_role = (payload.role or "knowledge_worker").strip().lower()
    if req_role in ["admin", "knowledge_worker", "analyst"]:
        valid_role = req_role
    else:
        custom_role = db.query(RoleRecord).filter(
            (RoleRecord.id == req_role) | (RoleRecord.name.ilike(payload.role.strip()))
        ).first()
        if custom_role and custom_role.is_active:
            valid_role = custom_role.id
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role '{payload.role}' does not exist or is inactive."
            )

    new_user = UserRecord(
        id=f"user_{str(uuid.uuid4())[:12]}",
        email=email_clean,
        full_name=payload.full_name.strip(),
        hashed_password=get_password_hash(payload.password),
        role=valid_role,
        organization=payload.organization or "Enterprise",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(f"Admin {admin.email} provisioned new user {new_user.email} with role '{new_user.role}'")

    return build_user_response(new_user, db)


# ============================================================================
# 5. FORGOT PASSWORD WORKFLOW (REAL EMAIL / SMS OTP)
# ============================================================================

@router.post("/forgot-password/request", response_model=ForgotPasswordResponse, summary="Request Password Reset OTP")
def request_password_reset_otp(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Initiates password recovery by sending a single-use cryptographically secure OTP.
    Supports email and SMS channels when configured.
    """
    clean_id = (payload.identifier or payload.email or payload.phone_number or "").strip()
    if not clean_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Identifier (email or phone) is required."
        )

    channel = (payload.delivery_method or payload.channel or "email").strip().lower()
    if channel not in ["email", "sms"]:
        channel = "email"

    # Find matching account
    user = None
    if "@" in clean_id or channel == "email":
        user = db.query(UserRecord).filter(UserRecord.email == clean_id.lower()).first()
    else:
        user = db.query(UserRecord).filter(UserRecord.phone_number == clean_id).first()

    if not user:
        logger.warning(f"Password reset requested for non-existent identifier: {clean_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account matching this identifier was found in the enterprise directory."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is deactivated. Please contact an enterprise administrator."
        )

    destination = user.email if channel == "email" else (user.phone_number or clean_id)
    if channel == "sms" and not user.phone_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No mobile phone number is registered on this account. Please select Email verification."
        )

    # Check for active cooldown (within OTP_RESEND_COOLDOWN_SECONDS)
    now = datetime.now(timezone.utc)
    recent_otp = db.query(PasswordResetOTPRecord).filter(
        PasswordResetOTPRecord.user_id == user.id,
        PasswordResetOTPRecord.is_used == False,
        PasswordResetOTPRecord.created_at >= now - timedelta(seconds=settings.OTP_RESEND_COOLDOWN_SECONDS)
    ).first()

    if recent_otp:
        elapsed = (now - recent_otp.created_at.replace(tzinfo=timezone.utc)).total_seconds()
        remaining = max(1, int(settings.OTP_RESEND_COOLDOWN_SECONDS - elapsed))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"A recovery code was recently generated. Please wait {remaining} seconds before requesting a new code."
        )

    # Invalidate previous unused OTPs for this user
    db.query(PasswordResetOTPRecord).filter(
        PasswordResetOTPRecord.user_id == user.id,
        PasswordResetOTPRecord.is_used == False
    ).update({"is_used": True})

    # Generate genuine 6-digit OTP & store hash
    plain_otp = generate_secure_otp(6)
    hashed_otp = hash_otp(plain_otp)
    otp_session_id = f"otp_{uuid.uuid4().hex[:12]}"
    expires_at = now + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)

    # Dispatch OTP via provider
    if channel == "email":
        dispatched, dispatch_msg = send_otp_email(user.email, plain_otp)
    else:
        dispatched, dispatch_msg = send_otp_sms(user.phone_number, plain_otp)

    if not dispatched:
        logger.error(f"OTP dispatch failed for user {user.email}: {dispatch_msg}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=dispatch_msg
        )

    otp_record = PasswordResetOTPRecord(
        id=otp_session_id,
        user_id=user.id,
        delivery_channel=channel,
        destination=destination,
        otp_hash=hashed_otp,
        attempts_left=settings.OTP_MAX_ATTEMPTS,
        is_used=False,
        expires_at=expires_at,
        created_at=now
    )
    db.add(otp_record)
    record_audit_log(db, "OTP_DISPATCHED", "auth", user.id, user.email, details=f"Channel: {channel}")
    db.commit()

    return ForgotPasswordResponse(
        success=True,
        message=f"Verification code has been dispatched to {mask_destination(destination, channel)}.",
        session_id=otp_session_id,
        request_id=otp_session_id,
        channel=channel,
        delivery_method=channel,
        masked_destination=mask_destination(destination, channel),
        cooldown_seconds=settings.OTP_RESEND_COOLDOWN_SECONDS,
        expires_in_seconds=settings.OTP_EXPIRE_MINUTES * 60
    )


@router.post("/forgot-password/verify", response_model=OTPVerifyResponse, summary="Verify OTP Code")
def verify_password_reset_otp(payload: OTPVerifyRequest, db: Session = Depends(get_db)):
    """
    Verifies the submitted OTP against the session record.
    Enforces expiry, single-use, and attempt decrement.
    """
    req_id = (payload.session_id or payload.reset_request_id or "").strip()
    if not req_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session ID or Reset Request ID is required."
        )

    otp_record = db.query(PasswordResetOTPRecord).filter(
        PasswordResetOTPRecord.id == req_id
    ).first()

    if not otp_record or otp_record.is_used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification session. Please request a new code."
        )

    now = datetime.now(timezone.utc)
    exp = otp_record.expires_at.replace(tzinfo=timezone.utc) if otp_record.expires_at.tzinfo is None else otp_record.expires_at
    if now > exp:
        otp_record.is_used = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The verification code has expired. Please request a fresh code."
        )

    if otp_record.attempts_left <= 0:
        otp_record.is_used = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum verification attempts exceeded. For security, this code is invalidated."
        )

    is_valid = verify_otp_hash(payload.otp_code.strip(), otp_record.otp_hash)
    if not is_valid:
        otp_record.attempts_left -= 1
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Incorrect verification code. {otp_record.attempts_left} attempt(s) remaining."
        )

    # Valid OTP: generate short-lived reset token
    reset_token = f"rst_{uuid.uuid4().hex}{uuid.uuid4().hex[:8]}"
    otp_record.reset_token = reset_token
    record_audit_log(db, "OTP_VERIFICATION_SUCCESS", "auth", otp_record.user_id, details="OTP successfully verified.")
    db.commit()

    return OTPVerifyResponse(
        success=True,
        message="Verification code confirmed successfully.",
        session_id=otp_record.id,
        reset_token=reset_token
    )


@router.post("/forgot-password/reset", response_model=PasswordResetSubmitResponse, summary="Reset Password with Verified Token")
def reset_password_with_token(payload: PasswordResetSubmitRequest, db: Session = Depends(get_db)):
    """
    Updates the account password after successful OTP verification.
    Invalidates session and records security notification.
    """
    session_id = (payload.session_id or "").strip() if payload.session_id else None
    reset_token = (payload.reset_token or "").strip()

    if session_id:
        otp_record = db.query(PasswordResetOTPRecord).filter(
            PasswordResetOTPRecord.id == session_id
        ).first()
    else:
        otp_record = db.query(PasswordResetOTPRecord).filter(
            PasswordResetOTPRecord.reset_token == reset_token
        ).first()

    if not otp_record or otp_record.is_used or not otp_record.reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset session."
        )

    if otp_record.reset_token != reset_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid security reset token. Please restart password recovery."
        )

    now = datetime.now(timezone.utc)
    exp = otp_record.expires_at.replace(tzinfo=timezone.utc) if otp_record.expires_at.tzinfo is None else otp_record.expires_at
    if now > exp:
        otp_record.is_used = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset session has expired. Please request a new code."
        )

    if len(payload.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 6 characters in length."
        )

    user = db.query(UserRecord).filter(UserRecord.id == otp_record.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User account not found.")

    user.hashed_password = get_password_hash(payload.new_password)
    otp_record.is_used = True
    otp_record.reset_token = None

    # In-app security notification
    sec_notif = NotificationRecord(
        id=f"notif_{uuid.uuid4().hex[:12]}",
        user_id=user.id,
        title="Password Reset Completed",
        message="Your account password was successfully reset via security verification.",
        category="security",
        is_read=False,
        created_at=datetime.now(timezone.utc)
    )
    db.add(sec_notif)
    record_audit_log(db, "PASSWORD_RESET_SUCCESS", "auth", user.id, user.email, details="Password changed via verified OTP.")
    db.commit()

    return PasswordResetSubmitResponse(
        success=True,
        message="Password has been updated successfully. Please sign in with your new password."
    )


# ============================================================================
# 6. ADMINISTRATOR AUDIT & SYSTEM STATUS ENDPOINTS
# ============================================================================

@router.get("/admin/audit-logs", response_model=List[AuditLogResponse], summary="Get System Audit Logs (Admin Only)")
def get_audit_logs(
    admin: UserRecord = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Returns recent recorded operational and security audit events."""
    logs = db.query(AuditLogRecord).order_by(AuditLogRecord.created_at.desc()).limit(100).all()
    return [
        AuditLogResponse(
            id=l.id,
            user_id=l.user_id,
            user_email=l.user_email or "System",
            action=l.action,
            resource_type=l.resource_type,
            resource_id=l.resource_id,
            details=l.details,
            ip_address=l.ip_address,
            created_at=l.created_at.isoformat() if l.created_at else None
        ) for l in logs
    ]


@router.get("/my-permissions", response_model=UserPermissionsResponse, summary="Get Current User Permissions")
def get_my_permissions(
    current_user: UserRecord = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns the caller's verified permissions list and role descriptor."""
    role_obj = db.query(RoleRecord).filter(RoleRecord.id == current_user.role).first()
    perms = get_user_permissions(current_user.role, db)
    role_name = role_obj.name if role_obj else current_user.role.replace("_", " ").title()
    is_builtin = role_obj.is_builtin if role_obj else current_user.role in ["admin", "knowledge_worker", "analyst"]

    return UserPermissionsResponse(
        role_id=current_user.role,
        role_name=role_name,
        is_builtin=is_builtin,
        permissions=perms
    )


@router.get("/admin/capabilities", response_model=List[RoleCapabilityItem], summary="List Assignable Capabilities (Admin Only)")
def list_capabilities(admin: UserRecord = Depends(require_admin)):
    """Returns all standardized platform capabilities that can be granted to roles."""
    return [RoleCapabilityItem(**c) for c in PLATFORM_CAPABILITIES]


@router.get("/admin/roles", response_model=List[CustomRoleResponse], summary="List All Roles (Admin Only)")
def list_roles(
    admin: UserRecord = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Returns all built-in and administrator-created custom roles with active user counts."""
    from sqlalchemy import func
    roles = db.query(RoleRecord).order_by(RoleRecord.is_builtin.desc(), RoleRecord.created_at.asc()).all()
    counts = dict(db.query(UserRecord.role, func.count(UserRecord.id)).group_by(UserRecord.role).all())

    results = []
    for r in roles:
        u_count = counts.get(r.id, 0)
        results.append(CustomRoleResponse(
            id=r.id,
            name=r.name,
            description=r.description or "",
            permissions=r.get_permissions(),
            is_builtin=r.is_builtin,
            is_active=r.is_active,
            user_count=u_count,
            created_at=r.created_at.isoformat() if r.created_at else None,
            updated_at=r.updated_at.isoformat() if r.updated_at else None
        ))
    return results


@router.post("/admin/roles", response_model=CustomRoleResponse, status_code=status.HTTP_201_CREATED, summary="Create Custom Role (Admin Only)")
def create_custom_role(
    payload: CustomRoleCreateRequest,
    admin: UserRecord = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Creates a new enterprise custom role with chosen granular permissions."""
    clean_name = payload.name.strip()
    if not clean_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role name cannot be empty.")

    if clean_name.lower() in ["admin", "administrator", "knowledge worker", "knowledge_worker", "analyst", "knowledge analyst"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role name '{clean_name}' conflicts with a reserved built-in system role."
        )

    existing = db.query(RoleRecord).filter(RoleRecord.name.ilike(clean_name)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A role with the name '{clean_name}' already exists."
        )

    invalid_perms = [p for p in payload.permissions if p not in VALID_CAPABILITY_IDS]
    if invalid_perms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid permission capabilities: {', '.join(invalid_perms)}"
        )

    role_slug = re.sub(r'[^a-zA-Z0-9_]', '_', clean_name.lower()).strip('_')
    role_id = f"role_{role_slug[:20]}_{str(uuid.uuid4())[:6]}"

    new_role = RoleRecord(
        id=role_id,
        name=clean_name,
        description=payload.description.strip() if payload.description else "",
        is_builtin=False,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    new_role.set_permissions(payload.permissions)
    db.add(new_role)
    db.commit()
    db.refresh(new_role)

    record_audit_log(
        db=db,
        action="ADMIN_CREATE_ROLE",
        resource_type="role",
        user_id=admin.id,
        user_email=admin.email,
        resource_id=new_role.id,
        details=f"Created role '{new_role.name}' with permissions: {', '.join(payload.permissions)}"
    )
    logger.info(f"Admin {admin.email} created custom role '{new_role.name}' (ID: {new_role.id})")

    return CustomRoleResponse(
        id=new_role.id,
        name=new_role.name,
        description=new_role.description or "",
        permissions=new_role.get_permissions(),
        is_builtin=new_role.is_builtin,
        is_active=new_role.is_active,
        user_count=0,
        created_at=new_role.created_at.isoformat() if new_role.created_at else None,
        updated_at=new_role.updated_at.isoformat() if new_role.updated_at else None
    )


@router.put("/admin/roles/{role_id}", response_model=CustomRoleResponse, summary="Update Custom Role (Admin Only)")
def update_custom_role(
    role_id: str,
    payload: CustomRoleUpdateRequest,
    admin: UserRecord = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Updates custom role name, description, active status, and granted permissions."""
    role = db.query(RoleRecord).filter(RoleRecord.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")

    if role.is_builtin:
        if payload.name and payload.name.strip().lower() != role.name.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Built-in system roles cannot be renamed."
            )
        if payload.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Built-in system roles cannot be deactivated."
            )

    if payload.name:
        clean_name = payload.name.strip()
        if not clean_name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role name cannot be empty.")
        conflict = db.query(RoleRecord).filter(RoleRecord.name.ilike(clean_name), RoleRecord.id != role_id).first()
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A role with the name '{clean_name}' already exists."
            )
        role.name = clean_name

    if payload.description is not None:
        role.description = payload.description.strip()

    if payload.permissions is not None:
        invalid_perms = [p for p in payload.permissions if p not in VALID_CAPABILITY_IDS]
        if invalid_perms:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid permission capabilities: {', '.join(invalid_perms)}"
            )
        role.set_permissions(payload.permissions)

    if payload.is_active is not None and not role.is_builtin:
        role.is_active = payload.is_active

    role.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(role)

    record_audit_log(
        db=db,
        action="ADMIN_UPDATE_ROLE",
        resource_type="role",
        user_id=admin.id,
        user_email=admin.email,
        resource_id=role.id,
        details=f"Updated role '{role.name}'"
    )
    logger.info(f"Admin {admin.email} updated role '{role.name}' ({role.id})")

    from sqlalchemy import func
    u_count = db.query(func.count(UserRecord.id)).filter(UserRecord.role == role.id).scalar() or 0

    return CustomRoleResponse(
        id=role.id,
        name=role.name,
        description=role.description or "",
        permissions=role.get_permissions(),
        is_builtin=role.is_builtin,
        is_active=role.is_active,
        user_count=u_count,
        created_at=role.created_at.isoformat() if role.created_at else None,
        updated_at=role.updated_at.isoformat() if role.updated_at else None
    )


@router.delete("/admin/roles/{role_id}", summary="Delete Custom Role (Admin Only)")
def delete_custom_role(
    role_id: str,
    admin: UserRecord = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Safely deletes a custom role, preventing deletion of built-in roles or roles assigned to active users."""
    role = db.query(RoleRecord).filter(RoleRecord.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")

    if role.is_builtin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Built-in system roles cannot be deleted."
        )

    assigned_count = db.query(UserRecord).filter(
        (UserRecord.role == role.id) | (UserRecord.role == role.name)
    ).count()
    if assigned_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete role '{role.name}' because it is currently assigned to {assigned_count} user(s). Please reassign those users before deleting this role."
        )

    role_name = role.name
    db.delete(role)
    db.commit()

    record_audit_log(
        db=db,
        action="ADMIN_DELETE_ROLE",
        resource_type="role",
        user_id=admin.id,
        user_email=admin.email,
        resource_id=role_id,
        details=f"Deleted custom role '{role_name}'"
    )
    logger.info(f"Admin {admin.email} deleted custom role '{role_name}' ({role_id})")

    return {"success": True, "message": f"Role '{role_name}' has been successfully deleted."}


@router.get("/admin/roles-permissions", summary="Get Roles & Permissions Matrix")
def get_roles_permissions(
    admin: UserRecord = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Returns the platform role-based access matrix, including built-in and custom roles."""
    custom_roles = db.query(RoleRecord).filter(RoleRecord.is_builtin == False, RoleRecord.is_active == True).all()

    matrix = []
    for cap in PLATFORM_CAPABILITIES:
        row = {
            "capability": cap["name"],
            "capability_id": cap["id"],
            "description": cap["description"],
            "category": cap.get("category", "General"),
            "admin": True,
            "knowledge_worker": cap["id"] in ["doc_ingestion", "doc_deletion", "search_retrieval", "qa_citations", "profile_settings"],
            "analyst": cap["id"] in ["search_retrieval", "qa_citations", "knowledge_graph", "evaluation", "export_center", "profile_settings"]
        }
        for cr in custom_roles:
            row[cr.id] = cap["id"] in cr.get_permissions()
        matrix.append(row)
    return matrix


@router.get("/admin/system-health", summary="Get System Operational Health (Admin Only)")
def get_admin_system_health(
    admin: UserRecord = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Provides genuine operational health metrics for the enterprise console without exposing raw developer docs."""
    from backend.app.models.document import DocumentRecord, DocumentChunkRecord, GraphEntityRecord, GraphRelationRecord
    
    doc_count = db.query(DocumentRecord).count()
    chunk_count = db.query(DocumentChunkRecord).count()
    entity_count = db.query(GraphEntityRecord).count()
    relation_count = db.query(GraphRelationRecord).count()
    user_count = db.query(UserRecord).count()

    return {
        "status": "healthy",
        "database": {
            "connected": True,
            "engine": "SQLite 3",
            "active_tables": ["documents", "chunks", "graph_entities", "users", "collections", "audit_logs"]
        },
        "storage": {
            "raw_docs_ready": settings.RAW_DOCS_DIR.exists(),
            "vector_store_ready": settings.VECTOR_STORE_DIR.exists(),
            "graph_store_ready": settings.GRAPH_STORE_DIR.exists()
        },
        "ai_engine": {
            "llm_provider": settings.LLM_PROVIDER,
            "llm_model": settings.LLM_MODEL,
            "embedding_provider": settings.EMBEDDING_PROVIDER,
            "embedding_model": settings.EMBEDDING_MODEL
        },
        "metrics": {
            "total_documents": doc_count,
            "indexed_chunks": chunk_count,
            "graph_entities": entity_count,
            "graph_relations": relation_count,
            "registered_users": user_count
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
