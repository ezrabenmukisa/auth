"""Shared audit-event persistence."""

from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models.audit_logs import AuditLog


def create_audit_log(action, status, user_id=None, ip_address=None):
    """Persist an audit event without breaking the primary operation."""
    log = AuditLog(
        user_id=user_id,
        action=action,
        status=status,
        ip_address=ip_address,
    )
    try:
        db.session.add(log)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return None
    return log
