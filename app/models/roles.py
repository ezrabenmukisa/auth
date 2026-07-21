"""Placeholder for future role models."""
from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db

# Association table for Role <-> Permission
role_permissions = db.Table(
    "role_permissions",
    db.Column("role_id", db.Integer, db.ForeignKey(
        "roles.id"), primary_key=True),
    db.Column("permission_id", db.Integer, db.ForeignKey(
        "permissions.id"), primary_key=True),
)


class Role(db.Model):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        db.String(80), unique=True, nullable=False, index=True)
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
    users = relationship("User", secondary="user_roles",
                         back_populates="roles")
    permissions = relationship(
        "Permission", secondary=role_permissions, back_populates="roles")

    def __repr__(self) -> str:
        return f"<Role id={self.id} name={self.name!r}>"
