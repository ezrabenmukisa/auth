"""Developer-facing OpenAPI and Swagger UI routes."""

from pathlib import Path

from flask import Blueprint, render_template, send_file

api_docs_bp = Blueprint("api_docs", __name__, url_prefix="/api")

OPENAPI_SPEC_PATH = Path(__file__).resolve().parent.parent / "docs" / "openapi.yaml"


@api_docs_bp.get("/openapi.yaml")
def openapi_spec():
    """Return the OpenAPI document used by Swagger UI and GitBook."""
    return send_file(OPENAPI_SPEC_PATH, mimetype="application/yaml")


@api_docs_bp.get("/docs")
def swagger_ui():
    """Render interactive Swagger UI documentation."""
    return render_template("swagger_ui.html")
