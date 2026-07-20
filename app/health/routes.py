"""Health-check HTTP routes."""

from flask import jsonify

from app.health import health_bp


@health_bp.get("/live")
def live():
    """Confirm that the Flask service is running."""
    return jsonify(message="Service is running", status="ok"), 200
