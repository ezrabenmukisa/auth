"""Business logic for password security and account controls."""

import smtplib
import ssl
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from hashlib import sha256
from uuid import uuid4

from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models.audit_logs import AuditLog
from app.models.password_reset import PasswordResetToken
from app.models.users import User


class SecurityError(Exception):
    """Raised when a security operation cannot be completed."""


class SecurityPersistenceError(SecurityError):
    """Raised when a security write cannot be persisted."""


def _utc_datetime(value: datetime) -> datetime:
    """Treat database values without timezone metadata as UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _token_digest(token: str) -> str:
    """Return the irreversible database representation of a reset token."""
    return sha256(token.encode("utf-8")).hexdigest()


def _audit(user_id, action, status, ip_address=None):
    db.session.add(
        AuditLog(
            user_id=user_id,
            action=action,
            status=status,
            ip_address=ip_address,
        )
    )


def request_password_reset(email: str, ip_address=None) -> str | None:
    """Create a reset token when the normalized email belongs to a user."""
    user = db.session.scalar(db.select(User).where(User.email == email))
    if user is None:
        return None

    token = str(uuid4())
    reset = PasswordResetToken(
        user_id=user.id,
        token=_token_digest(token),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    try:
        db.session.add(reset)
        _audit(user.id, "PASSWORD_RESET_REQUEST", "SUCCESS", ip_address)
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        raise SecurityPersistenceError(
            "Could not create the password-reset request."
        ) from exc
    return token


def send_password_reset_email(recipient: str, token: str) -> bool:
    """Send a password-reset link using environment-configured SMTP."""
    username = current_app.config.get("MAIL_USERNAME")
    password = current_app.config.get("MAIL_PASSWORD")
    sender = current_app.config.get("MAIL_DEFAULT_SENDER")
    if not username or not password or not sender:
        return False

    reset_url = (
        f"{current_app.config['PUBLIC_APP_URL'].rstrip('/')}"
        f"/reset-password?token={token}"
    )
    message = EmailMessage()
    message["Subject"] = "Reset your Access Hub password"
    message["From"] = sender
    message["To"] = recipient
    message.set_content(
        "A password reset was requested for your Access Hub account.\n\n"
        f"Open this link within one hour:\n{reset_url}\n\n"
        "If you did not request this, you can ignore this email."
    )

    try:
        if current_app.config["MAIL_USE_SSL"]:
            with smtplib.SMTP_SSL(
                current_app.config["MAIL_SERVER"],
                current_app.config["MAIL_PORT"],
                context=ssl.create_default_context(),
                timeout=10,
            ) as smtp:
                smtp.login(username, password)
                smtp.send_message(message)
        else:
            with smtplib.SMTP(
                current_app.config["MAIL_SERVER"],
                current_app.config["MAIL_PORT"],
                timeout=10,
            ) as smtp:
                smtp.starttls(context=ssl.create_default_context())
                smtp.login(username, password)
                smtp.send_message(message)
    except (OSError, smtplib.SMTPException):
        return False
    return True


def reset_password(token: str, password: str, ip_address=None) -> User:
    """Replace a password using an unused, unexpired reset token."""
    reset = db.session.scalar(
        db.select(PasswordResetToken).where(
            PasswordResetToken.token == _token_digest(token)
        )
    )
    if (
        reset is None
        or reset.used
        or _utc_datetime(reset.expires_at) <= datetime.now(timezone.utc)
    ):
        raise SecurityError("Invalid or expired reset token.")

    user = db.session.get(User, reset.user_id)
    if user is None:
        raise SecurityError("Invalid or expired reset token.")

    try:
        user.password_hash = generate_password_hash(password)
        reset.used = True
        _audit(user.id, "PASSWORD_RESET", "SUCCESS", ip_address)
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        raise SecurityPersistenceError("Could not reset the password.") from exc
    return user


def set_account_suspension(
    user_id: int,
    *,
    suspended: bool,
    actor_id: int,
    ip_address=None,
) -> User:
    """Suspend or reactivate an account."""
    if user_id == actor_id:
        raise SecurityError("Administrators cannot change their own account status.")
    user = db.session.get(User, user_id)
    if user is None:
        raise SecurityError("User not found.")

    try:
        user.is_suspended = suspended
        if not suspended:
            user.is_active = True
        _audit(
            actor_id,
            "ACCOUNT_SUSPENDED" if suspended else "ACCOUNT_ACTIVATED",
            "SUCCESS",
            ip_address,
        )
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        raise SecurityPersistenceError("Could not update the account status.") from exc
    return user


def list_audit_logs(page: int, per_page: int):
    """Return security events with newest events first."""
    statement = db.select(AuditLog).order_by(
        AuditLog.created_at.desc(), AuditLog.id.desc()
    )
    return db.paginate(statement, page=page, per_page=per_page, error_out=False)
