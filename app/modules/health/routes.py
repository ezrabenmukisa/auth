from flask import Blueprint
from app.extensions import db

health_bp = Blueprint("health", __name__)

@health_bp.route("/health/live")
def live():
    return {"status": "alive"}, 200


@health_bp.route("/health/ready")
def ready():
    try:
        db.session.execute("SELECT 1")
        return {"status": "ready"}, 200
    except:
        return {"status": "not ready"}, 500