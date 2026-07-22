"""Integration tests for registration and the complete JWT lifecycle."""

from datetime import timedelta

import pytest

from app.extensions import db
from app.models.revoked_tokens import RevokedToken
from app.models.users import User
from app.authentication.services import verify_password


VALID_REGISTRATION = {
    "username": "newuser",
    "email": "New.User@Example.COM",
    "password": "secure-password",
    "full_name": "New User",
}


def _register(client, **overrides):
    payload = {**VALID_REGISTRATION, **overrides}
    return client.post("/api/v1/auth/register", json=payload)


def _login(client, identifier="newuser", password="secure-password"):
    return client.post(
        "/api/v1/auth/login",
        json={"identifier": identifier, "password": password},
    )


def _bearer(token):
    return {"Authorization": f"Bearer {token}"}


def test_registration_hashes_password_and_returns_safe_user(app, client):
    response = _register(client)

    assert response.status_code == 201
    body = response.get_json()
    assert body["email"] == "new.user@example.com"
    assert "password" not in body
    assert "password_hash" not in body

    with app.app_context():
        user = User.query.filter_by(username="newuser").one()
        assert user.password_hash != VALID_REGISTRATION["password"]
        assert verify_password(user, VALID_REGISTRATION["password"])


def test_registration_rejects_empty_body(client):
    response = client.post("/api/v1/auth/register", json={})
    assert response.status_code == 400
    assert set(response.get_json()["errors"]) == {
        "username", "email", "password"
    }


def test_registration_rejects_duplicate_username(client):
    _register(client)
    response = _register(client, email="different@example.com")
    assert response.status_code == 409
    assert "username" in response.get_json()["error"]


def test_registration_rejects_duplicate_email(client):
    _register(client)
    response = _register(client, username="differentuser")
    assert response.status_code == 409
    assert "email" in response.get_json()["error"]


@pytest.mark.parametrize("method", ["get", "put", "delete"])
def test_registration_rejects_unsupported_methods(client, method):
    assert getattr(client, method)("/api/v1/auth/register").status_code == 405


@pytest.mark.parametrize("identifier", ["newuser", "new.user@example.com"])
def test_login_issues_access_and_refresh_tokens(client, identifier):
    _register(client)
    response = _login(client, identifier=identifier)

    assert response.status_code == 200
    body = response.get_json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "Bearer"


def test_login_rejects_missing_fields(client):
    response = client.post("/api/v1/auth/login", json={})
    assert response.status_code == 400
    assert set(response.get_json()["errors"]) == {"identifier", "password"}


@pytest.mark.parametrize(
    ("identifier", "password"),
    [("missing", "secure-password"), ("newuser", "wrong-password")],
)
def test_login_rejects_invalid_credentials_without_account_details(
    client, identifier, password
):
    _register(client)
    response = _login(client, identifier=identifier, password=password)
    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid username/email or password."


def test_inactive_user_cannot_log_in(app, client):
    _register(client)
    with app.app_context():
        user = User.query.filter_by(username="newuser").one()
        user.is_active = False
        db.session.commit()

    response = _login(client)
    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid username/email or password."


def test_protected_endpoint_requires_access_token(client):
    assert client.get("/api/v1/auth/protected").status_code == 401


def test_access_token_opens_protected_endpoint(client):
    user_id = _register(client).get_json()["id"]
    access_token = _login(client).get_json()["access_token"]

    response = client.get(
        "/api/v1/auth/protected", headers=_bearer(access_token)
    )
    assert response.status_code == 200
    assert response.get_json()["user_id"] == user_id


def test_malformed_token_is_rejected(client):
    response = client.get(
        "/api/v1/auth/protected", headers=_bearer("not-a-jwt")
    )
    assert response.status_code == 422


def test_refresh_token_issues_new_access_token(client):
    _register(client)
    refresh_token = _login(client).get_json()["refresh_token"]

    response = client.post(
        "/api/v1/auth/refresh", headers=_bearer(refresh_token)
    )
    assert response.status_code == 200
    new_access_token = response.get_json()["access_token"]
    assert client.get(
        "/api/v1/auth/protected", headers=_bearer(new_access_token)
    ).status_code == 200


def test_access_token_cannot_refresh(client):
    _register(client)
    access_token = _login(client).get_json()["access_token"]
    response = client.post(
        "/api/v1/auth/refresh", headers=_bearer(access_token)
    )
    assert response.status_code == 422


def test_refresh_token_cannot_open_access_endpoint(client):
    _register(client)
    refresh_token = _login(client).get_json()["refresh_token"]
    response = client.get(
        "/api/v1/auth/protected", headers=_bearer(refresh_token)
    )
    assert response.status_code == 422


def test_logout_revokes_access_and_refresh_session(app, client):
    _register(client)
    tokens = _login(client).get_json()

    logout_response = client.post(
        "/api/v1/auth/logout", headers=_bearer(tokens["access_token"])
    )
    assert logout_response.status_code == 200

    with app.app_context():
        assert RevokedToken.query.count() == 1

    assert client.get(
        "/api/v1/auth/protected", headers=_bearer(tokens["access_token"])
    ).status_code == 401
    assert client.post(
        "/api/v1/auth/refresh", headers=_bearer(tokens["refresh_token"])
    ).status_code == 401


def test_expired_access_token_is_rejected(app, client):
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(seconds=-1)
    _register(client)
    access_token = _login(client).get_json()["access_token"]

    response = client.get(
        "/api/v1/auth/protected", headers=_bearer(access_token)
    )
    assert response.status_code == 401


def test_expired_refresh_token_is_rejected(app, client):
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(seconds=-1)
    _register(client)
    refresh_token = _login(client).get_json()["refresh_token"]

    response = client.post(
        "/api/v1/auth/refresh", headers=_bearer(refresh_token)
    )
    assert response.status_code == 401
