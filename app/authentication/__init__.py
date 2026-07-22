"""Authentication feature package."""

from flask import Blueprint


authentication_bp = Blueprint(
    "authentication",
    __name__,
    url_prefix="/api/v1/auth",
)

from app.authentication import routes  # noqa: E402, F401
