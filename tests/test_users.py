"""Tests for user registration and profile management."""


def _register(client, **overrides):
    """Helper to register a user, with sensible defaults that can be overridden."""
    payload = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123",
    }
    payload.update(overrides)
    return client.post("/api/v1/users/register", json=payload)


def test_register_success(client):
    """A valid registration returns 201 and the created user, without the password hash."""
    response = _register(client)

    assert response.status_code == 201
    body = response.get_json()
    assert body["username"] == "testuser"
    assert body["email"] == "test@example.com"
    assert body["is_active"] is True
    assert "password" not in body
    assert "password_hash" not in body


def test_register_duplicate_username(client):
    """Registering the same username twice is rejected with 409."""
    _register(client)
    response = _register(client, email="different@example.com")

    assert response.status_code == 409
    assert "username" in response.get_json()["error"]


def test_register_duplicate_email(client):
    """Registering the same email twice is rejected with 409."""
    _register(client)
    response = _register(client, username="differentuser")

    assert response.status_code == 409
    assert "email" in response.get_json()["error"]


def test_register_missing_fields(client):
    """Missing required fields returns 400 with field-specific errors."""
    response = client.post("/api/v1/users/register", json={})

    assert response.status_code == 400
    errors = response.get_json()["errors"]
    assert "username" in errors
    assert "email" in errors
    assert "password" in errors


def test_register_short_password(client):
    """A password under 8 characters is rejected."""
    response = _register(client, password="short")

    assert response.status_code == 400
    assert "password" in response.get_json()["errors"]


def test_get_profile_success(client):
    """An existing user's profile can be fetched by id."""
    register_response = _register(client)
    user_id = register_response.get_json()["id"]

    response = client.get(f"/api/v1/users/{user_id}")

    assert response.status_code == 200
    assert response.get_json()["username"] == "testuser"


def test_get_profile_not_found(client):
    """Requesting a non-existent user id returns 404."""
    response = client.get("/api/v1/users/999")

    assert response.status_code == 404


def test_update_profile_success(client):
    """A user's full_name can be updated."""
    register_response = _register(client)
    user_id = register_response.get_json()["id"]

    response = client.patch(
        f"/api/v1/users/{user_id}", json={"full_name": "Test User"}
    )

    assert response.status_code == 200
    assert response.get_json()["full_name"] == "Test User"


def test_update_profile_not_found(client):
    """Updating a non-existent user returns 404."""
    response = client.patch("/api/v1/users/999", json={"full_name": "Nobody"})

    assert response.status_code == 404


def test_list_users_success(client):
    """Listing users returns pagination metadata and results."""
    _register(client)

    response = client.get("/api/v1/users/")

    assert response.status_code == 200
    body = response.get_json()
    assert body["total"] == 1
    assert body["users"][0]["username"] == "testuser"


def test_list_users_search_no_match(client):
    """Searching for a non-existent user returns an empty result."""
    _register(client)

    response = client.get("/api/v1/users/?search=nonexistent")

    assert response.status_code == 200
    body = response.get_json()
    assert body["total"] == 0
    assert body["users"] == []
