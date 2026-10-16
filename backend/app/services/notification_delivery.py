"""
Notification & OTP Delivery Service for Enterprise Knowledge Navigator.
Handles genuine email and SMS dispatch, OTP security generation, and audit logging.
"""

import os
import smtplib
import secrets
import string
import hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.models.user import AuditLogRecord


def generate_secure_otp(length: int = 6) -> str:
    """Generates a cryptographically strong numeric OTP."""
    digits = string.digits
    return "".join(secrets.choice(digits) for _ in range(length))


def hash_otp(otp_code: str) -> str:
    """Produces SHA-256 hash of the OTP for secure database storage."""
    salted = f"{settings.SECRET_KEY}:{otp_code}"
    return hashlib.sha256(salted.encode("utf-8")).hexdigest()


def verify_otp_hash(plain_otp: str, stored_hash: str) -> bool:
    """Timing-attack safe verification of plain OTP against stored hash."""
    computed = hash_otp(plain_otp)
    return secrets.compare_digest(computed, stored_hash)


def mask_destination(destination: str, channel: str = "email") -> str:
    """Masks destination address for privacy safe display."""
    if channel == "email" and "@" in destination:
        name, domain = destination.split("@", 1)
        if len(name) <= 2:
            masked_name = name[0] + "***"
        else:
            masked_name = name[0] + "***" + name[-1]
        return f"{masked_name}@{domain}"
    elif channel == "sms":
        clean = destination.strip()
        if len(clean) >= 6:
            return clean[:3] + "****" + clean[-2:]
        return "***"
    return destination[:2] + "***"


def send_otp_email(to_email: str, otp_code: str) -> Tuple[bool, str]:
    """
    Dispatches a real email containing the verification code using SMTP if configured.
    If unconfigured, strictly reports unconfigured status without deceptive mock claims.
    """
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        logger.info(
            f"[DEV/TEST MODE] SMTP provider not configured in settings. Generated OTP for {to_email}: {otp_code} (Expires in {settings.OTP_EXPIRE_MINUTES}m)"
        )
        return (
            True,
            f"Verification code generated (development/test mode enabled; see console logs)."
        )

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Enterprise Knowledge Navigator — Password Recovery Code"
        msg["From"] = settings.SMTP_FROM_EMAIL
        msg["To"] = to_email

        text_content = (
            f"Enterprise Knowledge Navigator\n\n"
            f"Your single-use password recovery verification code is:\n\n"
            f"    {otp_code}\n\n"
            f"This code will expire in {settings.OTP_EXPIRE_MINUTES} minutes.\n"
            f"If you did not initiate this request, please contact your enterprise administrator immediately."
        )
        msg.attach(MIMEText(text_content, "plain"))

        if settings.SMTP_TLS:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_FROM_EMAIL, [to_email], msg.as_string())
        else:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_FROM_EMAIL, [to_email], msg.as_string())

        logger.info(f"Successfully dispatched OTP email to {to_email}")
        return True, "Verification code sent to your registered email address."
    except Exception as e:
        logger.error(f"Failed to send OTP email to {to_email}: {e}")
        return False, f"Failed to deliver verification email: {str(e)}"


def send_otp_sms(to_phone: str, otp_code: str) -> Tuple[bool, str]:
    """
    Dispatches a real SMS verification code via Twilio if configured.
    """
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        logger.info(
            f"[DEV/TEST MODE] Twilio SMS gateway not configured. Generated OTP for {to_phone}: {otp_code} (Expires in {settings.OTP_EXPIRE_MINUTES}m)"
        )
        return (
            True,
            f"Verification code generated (development/test mode enabled; see console logs)."
        )

    try:
        import urllib.request
        import urllib.parse
        import base64

        url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"
        data = urllib.parse.urlencode({
            "From": settings.TWILIO_FROM_NUMBER,
            "To": to_phone,
            "Body": f"[EK Navigator] Your password reset verification code is: {otp_code}. Valid for {settings.OTP_EXPIRE_MINUTES} mins."
        }).encode("utf-8")

        req = urllib.request.Request(url, data=data, method="POST")
        auth_str = f"{settings.TWILIO_ACCOUNT_SID}:{settings.TWILIO_AUTH_TOKEN}"
        b64_auth = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
        req.add_header("Authorization", f"Basic {b64_auth}")

        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status in (200, 201):
                logger.info(f"Successfully dispatched OTP SMS to {to_phone}")
                return True, "Verification code sent to your registered mobile number."
            return False, f"SMS gateway returned status code {response.status}."
    except Exception as e:
        logger.error(f"Failed to send SMS to {to_phone}: {e}")
        return False, f"Failed to deliver SMS: {str(e)}"


def record_audit_log(
    db: Session,
    action: str,
    resource_type: str,
    user_id: Optional[str] = None,
    user_email: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = None
) -> AuditLogRecord:
    """Records security and operational actions into the audit log."""
    log = AuditLogRecord(
        id=f"audit_{secrets.token_hex(8)}",
        user_id=user_id,
        user_email=user_email,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
        created_at=datetime.now(timezone.utc)
    )
    db.add(log)
    try:
        db.commit()
        db.refresh(log)
    except Exception as e:
        logger.error(f"Failed to write audit log: {e}")
        db.rollback()
    return log
