
from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db


class Permission(db.Model):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        db.String(100), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(
        db.String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    roles = relationship("Role", secondary="role_permissions",
                         back_populates="permissions")

    def __repr__(self) -> str:
        return f"<Permission id={self.id} name={self.name!r}>"
