"""Authorization feature package."""

from flask import Blueprint

authorization_bp = Blueprint(
    "authorization",
    __name__,
    url_prefix="/api/v1/authorization",
)

from app.authorization import routes  # noqa: E402,F401