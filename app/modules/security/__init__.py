"""Security support feature package."""

from flask import Blueprint

security_bp = Blueprint("security", __name__, url_prefix="/api/v1/security")
