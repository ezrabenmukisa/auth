"""Integration tests for registration and the complete JWT lifecycle."""

from datetime import datetime, timedelta, timezone

import pytest
from flask_jwt_extended import create_access_token, create_refresh_token, decode_token

from app.authentication.services import revoke_session, verify_password
from app.extensions import db
from app.models.revoked_tokens import RevokedToken
from app.models.users import User

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
    assert body["username"] == "newuser"
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
    response = _register(client, email="not-an-email")

    assert response.status_code == 400
    assert "email" in response.get_json()["errors"]


def test_registration_rejects_short_password(client):
    response = _register(client, password="short")

    assert response.status_code == 400
    assert "password" in response.get_json()["errors"]


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
    response = getattr(client, method)("/api/v1/auth/register")

    assert response.status_code == 405


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
def test_login_uses_same_error_for_invalid_identifier_and_password(
    client,
    identifier,
    password,
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


def test_protected_endpoint_requires_token(client):
    response = client.get("/api/v1/auth/protected")

    assert response.status_code == 401


def test_protected_endpoint_rejects_malformed_token(client):
    response = client.get(
        "/api/v1/auth/protected",
        headers=_bearer("not-a-jwt"),
    )

    assert response.status_code == 422


def test_access_token_opens_protected_endpoint(client):
    user_id = _register(client).get_json()["id"]
    access_token = _login(client).get_json()["access_token"]

    response = client.get(
        "/api/v1/auth/protected",
        headers=_bearer(access_token),
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "message": "Protected resource accessed.",
        "user_id": user_id,
    }


def test_refresh_token_cannot_open_protected_endpoint(client):
    _register(client)
    refresh_token = _login(client).get_json()["refresh_token"]

    response = client.get(
        "/api/v1/auth/protected",
        headers=_bearer(refresh_token),
    )

    assert response.status_code == 422


def test_malformed_identity_is_rejected_safely(app, client):
    with app.app_context():
        token = create_access_token(identity="not-a-user-id")

    response = client.get(
        "/api/v1/auth/protected",
        headers=_bearer(token),
    )

    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid authentication identity."


@pytest.mark.parametrize("account_change", ["inactive", "deleted"])
def test_changed_user_is_rejected_with_previously_issued_token(
    app,
    client,
    account_change,
):
    _register(client)
    tokens = _login(client).get_json()

    with app.app_context():
        user = User.query.filter_by(username="newuser").one()
        if account_change == "inactive":
            user.is_active = False
        else:
            db.session.delete(user)
        db.session.commit()

    protected_response = client.get(
        "/api/v1/auth/protected",
        headers=_bearer(tokens["access_token"]),
    )
    refresh_response = client.post(
        "/api/v1/auth/refresh",
        headers=_bearer(tokens["refresh_token"]),
    )

    assert protected_response.status_code == 401
    assert refresh_response.status_code == 401


def test_refresh_token_issues_new_access_token(client):
    _register(client)
    refresh_token = _login(client).get_json()["refresh_token"]

    response = client.post(
        "/api/v1/auth/refresh",
        headers=_bearer(refresh_token),
    )

    assert response.status_code == 200
    new_access_token = response.get_json()["access_token"]
    assert (
        client.get(
            "/api/v1/auth/protected",
            headers=_bearer(new_access_token),
        ).status_code
        == 200
    )


def test_refreshed_access_token_preserves_and_respects_session_expiry(app, client):
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(minutes=2)
    _register(client)
    refresh_token = _login(client).get_json()["refresh_token"]

    response = client.post(
        "/api/v1/auth/refresh",
        headers=_bearer(refresh_token),
    )

    assert response.status_code == 200
    with app.app_context():
        refresh_claims = decode_token(refresh_token)
        access_claims = decode_token(response.get_json()["access_token"])
    assert access_claims["sid"] == refresh_claims["sid"]
    assert access_claims["session_expires_at"] == refresh_claims["session_expires_at"]
    assert access_claims["exp"] <= refresh_claims["session_expires_at"]


def test_refresh_rejects_expired_shared_session(app, client):
    user_id = _register(client).get_json()["id"]
    with app.app_context():
        refresh_token = create_refresh_token(
            identity=str(user_id),
            additional_claims={
                "sid": "expired-shared-session",
                "session_expires_at": int(
                    (datetime.now(timezone.utc) - timedelta(minutes=1)).timestamp()
                ),
            },
        )

    response = client.post(
        "/api/v1/auth/refresh",
        headers=_bearer(refresh_token),
    )

    assert response.status_code == 401
    assert response.get_json()["error"] == "Authentication session has expired."


def test_access_token_cannot_refresh(client):
    _register(client)
    access_token = _login(client).get_json()["access_token"]

    response = client.post(
        "/api/v1/auth/refresh",
        headers=_bearer(access_token),
    )

    assert response.status_code == 422


def test_expired_refresh_token_is_rejected(app, client):
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(seconds=-1)
    _register(client)
    refresh_token = _login(client).get_json()["refresh_token"]

    response = client.post(
        "/api/v1/auth/refresh",
        headers=_bearer(refresh_token),
    )

    assert response.status_code == 401


@pytest.mark.parametrize("logout_token", ["access_token", "refresh_token"])
def test_logout_accepts_either_token_and_preserves_user(
    app,
    client,
    logout_token,
):
    _register(client)
    tokens = _login(client).get_json()

    response = client.post(
        "/api/v1/auth/logout",
        headers=_bearer(tokens[logout_token]),
    )

    assert response.status_code == 200
    with app.app_context():
        assert User.query.count() == 1
        assert RevokedToken.query.count() == 1


def test_logout_revokes_both_tokens_from_shared_session(app, client):
    _register(client)
    tokens = _login(client).get_json()

    logout_response = client.post(
        "/api/v1/auth/logout",
        headers=_bearer(tokens["access_token"]),
    )

    assert logout_response.status_code == 200
    assert (
        client.get(
            "/api/v1/auth/protected",
            headers=_bearer(tokens["access_token"]),
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/auth/refresh",
            headers=_bearer(tokens["refresh_token"]),
        ).status_code
        == 401
    )

    with app.app_context():
        assert User.query.count() == 1
        assert RevokedToken.query.count() == 1


def test_repeated_session_revocation_is_idempotent(app, client):
    _register(client)
    access_token = _login(client).get_json()["access_token"]

    with app.app_context():
        claims = decode_token(access_token)
        first = revoke_session(claims)
        second = revoke_session(claims)
        assert first.id == second.id
        assert RevokedToken.query.count() == 1
