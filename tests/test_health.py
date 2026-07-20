"""Tests for health-check endpoints."""

from app import create_app
from app.config import TestConfig

def test_liveness_endpoint():
    app = create_app(TestConfig)
    client = app.test_client()

    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.get_json() == {"message": "Service is running", "status": "ok"}
