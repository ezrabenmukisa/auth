"""Persisted JWT-session revocation records."""

from datetime import datetime, timezone

from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class RevokedToken(db.Model):
    """Identify a revoked login session without storing either raw JWT."""

    __tablename__ = "revoked_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(
        db.String(36), unique=True, nullable=False, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(db.DateTime, nullable=False)
    revoked_at: Mapped[datetime] = mapped_column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<RevokedToken id={self.id} session_id={self.session_id!r}>"
