from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db

# Define the association table for User <-> Role (many-to-many)
user_roles = db.Table(
    "user_roles",
    db.Column("user_id", db.Integer, db.ForeignKey(
        "users.id"), primary_key=True),
    db.Column("role_id", db.Integer, db.ForeignKey(
        "roles.id"), primary_key=True),
)


class User(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(
        db.String(80), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(
        db.String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(db.String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(
        db.String(150), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        db.Boolean, default=True, nullable=False)
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
    roles = relationship("Role", secondary=user_roles, back_populates="users")

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r}>"
