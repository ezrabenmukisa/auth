"""Tests for the temporary Authentication registration boundary."""

import pytest

from app.models.users import User


VALID_REGISTRATION = {
    "username": "newuser",
    "email": "New.User@Example.COM",
    "password": "secure-password",
    "full_name": "New User",
}


def test_registration_rejects_empty_body(client):
    response = client.post("/api/v1/auth/register", json={})

    assert response.status_code == 400
    assert set(response.get_json()["errors"]) == {
        "username",
        "email",
        "password",
    }


def test_registration_rejects_missing_username(client):
    payload = {**VALID_REGISTRATION}
    payload.pop("username")

    response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 400
    assert "username" in response.get_json()["errors"]


def test_registration_rejects_invalid_email(client):
    response = client.post(
        "/api/v1/auth/register",
        json={**VALID_REGISTRATION, "email": "invalid-email"},
    )

    assert response.status_code == 400
    assert "email" in response.get_json()["errors"]


def test_registration_rejects_short_password(client):
    response = client.post(
        "/api/v1/auth/register",
        json={**VALID_REGISTRATION, "password": "short"},
    )

    assert response.status_code == 400
    assert "password" in response.get_json()["errors"]


def test_valid_registration_returns_pending_response(app, client):
    response = client.post("/api/v1/auth/register", json=VALID_REGISTRATION)

    assert response.status_code == 501
    assert response.get_json() == {
        "error": "Password hashing is not yet implemented",
        "status": "registration_pending",
    }
    assert VALID_REGISTRATION["password"] not in response.get_data(as_text=True)

    with app.app_context():
        assert User.query.count() == 0


@pytest.mark.parametrize("method", ["get", "put", "delete"])
def test_registration_rejects_unsupported_methods(client, method):
    response = getattr(client, method)("/api/v1/auth/register")

    assert response.status_code == 405
