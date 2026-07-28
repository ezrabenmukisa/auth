"""Audit log model."""

from datetime import datetime, timezone

from app.extensions import db


class AuditLog(db.Model):
    """Record a security-relevant application event."""

    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True)
    action = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    ip_address = db.Column(db.String(50), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} {self.status}>"
