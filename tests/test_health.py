"""Tests for health-check endpoints."""


def test_liveness_endpoint(client):
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.get_json() == {"message": "Service is running", "status": "ok"}
