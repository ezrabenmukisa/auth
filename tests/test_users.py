"""Tests for user creation and user-management HTTP behavior."""

import pytest

from app.extensions import db
from app.models.users import User
from app.users.schemas import ValidationError, validate_user_creation_data
from app.users.services import DuplicateUserError, create_user

TEST_PASSWORD_HASH = "pbkdf2:test-hash-created-by-authentication"


def _create_user(app, number=1, **overrides):
    payload = {
        "username": f"testuser{number}",
        "email": f"test{number}@example.com",
        "full_name": f"Test User {number}",
    }
    payload.update(overrides)

    with app.app_context():
        clean_data = validate_user_creation_data(payload)
        user = create_user(clean_data, password_hash=TEST_PASSWORD_HASH)
        return user.id


def test_registration_http_route_is_disabled(client):
    response = client.post("/api/v1/users/register", json={})

    assert response.status_code == 404


def test_create_user_success(app):
    user_id = _create_user(app)

    with app.app_context():
        user = db.session.get(User, user_id)
        assert user.username == "testuser1"
        assert user.email == "test1@example.com"
        assert user.password_hash == TEST_PASSWORD_HASH
        assert user.is_active is True


def test_create_user_normalizes_email(app):
    user_id = _create_user(app, email="  Test.User@Example.COM  ")

    with app.app_context():
        user = db.session.get(User, user_id)
        assert user.email == "test.user@example.com"


def test_create_user_rejects_duplicate_username(app):
    _create_user(app)

    with app.app_context(), pytest.raises(DuplicateUserError) as exc_info:
        create_user(
            validate_user_creation_data(
                {
                    "username": "testuser1",
                    "email": "different@example.com",
                }
            ),
            password_hash=TEST_PASSWORD_HASH,
        )

    assert exc_info.value.field == "username"


def test_create_user_rejects_duplicate_email(app):
    _create_user(app)

    with app.app_context(), pytest.raises(DuplicateUserError) as exc_info:
        create_user(
            validate_user_creation_data(
                {
                    "username": "differentuser",
                    "email": "test1@example.com",
                }
            ),
            password_hash=TEST_PASSWORD_HASH,
        )

    assert exc_info.value.field == "email"


def test_user_creation_requires_username_and_email():
    with pytest.raises(ValidationError) as exc_info:
        validate_user_creation_data({})

    assert set(exc_info.value.errors) == {"username", "email"}


def test_get_profile_success(app, client):
    user_id = _create_user(app)

    response = client.get(f"/api/v1/users/{user_id}")

    assert response.status_code == 200
    assert response.get_json() == {
        "id": user_id,
        "username": "testuser1",
        "email": "test1@example.com",
        "full_name": "Test User 1",
        "is_active": True,
    }


def test_get_profile_not_found(client):
    response = client.get("/api/v1/users/999")

    assert response.status_code == 404


def test_update_profile_success(app, client):
    user_id = _create_user(app)

    response = client.patch(
        f"/api/v1/users/{user_id}", json={"full_name": "Updated Name"}
    )

    assert response.status_code == 200
    assert response.get_json()["full_name"] == "Updated Name"


def test_update_profile_rejects_unknown_fields(app, client):
    user_id = _create_user(app)

    response = client.patch(
        f"/api/v1/users/{user_id}", json={"email": "changed@example.com"}
    )

    assert response.status_code == 400
    assert "fields" in response.get_json()["errors"]


def test_update_profile_rejects_long_full_name(app, client):
    user_id = _create_user(app)

    response = client.patch(f"/api/v1/users/{user_id}", json={"full_name": "x" * 151})

    assert response.status_code == 400
    assert "full_name" in response.get_json()["errors"]


def test_update_profile_not_found(client):
    response = client.patch("/api/v1/users/999", json={"full_name": "Nobody"})

    assert response.status_code == 404


def test_list_users_success(app, client):
    _create_user(app)

    response = client.get("/api/v1/users/")

    assert response.status_code == 200
    body = response.get_json()
    assert body["total"] == 1
    assert body["users"][0]["username"] == "testuser1"
    assert "password_hash" not in body["users"][0]


def test_list_users_search_finds_matching_user(app, client):
    _create_user(app, 1, username="alice")
    _create_user(app, 2, username="bob")

    response = client.get("/api/v1/users/?search=alice")

    assert response.status_code == 200
    body = response.get_json()
    assert body["total"] == 1
    assert [user["username"] for user in body["users"]] == ["alice"]


def test_list_users_search_returns_no_match(app, client):
    _create_user(app)

    response = client.get("/api/v1/users/?search=missing")

    assert response.status_code == 200
    assert response.get_json()["users"] == []
    assert response.get_json()["total"] == 0


def test_list_users_paginates_across_pages(app, client):
    for number in range(1, 6):
        _create_user(app, number)

    first_response = client.get("/api/v1/users/?page=1&per_page=2")
    second_response = client.get("/api/v1/users/?page=2&per_page=2")

    first = first_response.get_json()
    second = second_response.get_json()
    assert first["total"] == 5
    assert first["total_pages"] == 3
    assert [user["username"] for user in first["users"]] == [
        "testuser1",
        "testuser2",
    ]
    assert [user["username"] for user in second["users"]] == [
        "testuser3",
        "testuser4",
    ]


@pytest.mark.parametrize("page", ["0", "-1", "abc"])
def test_list_users_rejects_invalid_page(client, page):
    response = client.get(f"/api/v1/users/?page={page}")

    assert response.status_code == 400
    assert "page" in response.get_json()["errors"]


@pytest.mark.parametrize("per_page", ["0", "-1", "abc", "101"])
def test_list_users_rejects_invalid_per_page(client, per_page):
    response = client.get(f"/api/v1/users/?per_page={per_page}")

    assert response.status_code == 400
    assert "per_page" in response.get_json()["errors"]
