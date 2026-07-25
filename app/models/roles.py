"""Role model and role-permission association."""

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

role_permissions = db.Table(
    "role_permissions",
    db.Column("role_id", db.ForeignKey("roles.id"), primary_key=True),
    db.Column(
        "permission_id",
        db.ForeignKey("permissions.id"),
        primary_key=True,
    ),
)


class Role(db.Model):
    """Group permissions for assignment to users."""

    __tablename__ = "roles"

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

    users = relationship("User", back_populates="role")
    permissions = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles",
    )
