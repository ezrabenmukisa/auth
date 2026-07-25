"""Permission model."""

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class Permission(db.Model):
    """Represent one named authorization capability."""

    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        db.String(100),
        unique=True,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        db.String(255),
        nullable=True,
    )

    roles = relationship(
        "Role",
        secondary="role_permissions",
        back_populates="permissions",
    )
