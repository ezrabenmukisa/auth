"""Tests for user-facing UI routes and current-user data."""

from app.cli.seed import seed_development_data


def test_public_ui_pages_render(client):
    for path in ("/", "/login", "/register"):
        response = client.get(path, follow_redirects=True)
        assert response.status_code == 200


def test_auth_pages_include_password_visibility_and_confirmation(client):
    login = client.get("/login")
    register = client.get("/register")

    assert b'data-password-toggle="password"' in login.data
    assert b'data-password-toggle="password"' in register.data
    assert b'data-password-toggle="confirm-password"' in register.data
    assert b'name="confirm_password"' in register.data


def test_role_dashboard_pages_render(client):
    for path in ("/admin", "/manager", "/accountant", "/employee"):
        response = client.get(path)
        assert response.status_code == 200
        assert b"dashboard-app" in response.data
        assert b"My profile" in response.data
        assert b"profile-form" in response.data


def test_admin_dashboard_exposes_existing_management_controls(client):
    response = client.get("/admin")

    assert response.status_code == 200
    assert b"people-search-form" in response.data
    assert b"role-permissions-panel" in response.data
    assert b"create-role-form" in response.data
    assert b"create-permission-form" in response.data


def test_current_user_endpoint_returns_role(app, client):
    with app.app_context():
        seed_development_data(
            {
                "username": "ui-admin",
                "email": "ui-admin@example.com",
                "password": "secure-admin-password",
                "full_name": "UI Admin",
            }
        )

    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": "ui-admin", "password": "secure-admin-password"},
    )
    token = login.get_json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.get_json()["role"] == "Admin"

    update = client.patch(
        f"/api/v1/users/{response.get_json()['id']}",
        json={"full_name": "Updated UI Admin"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert update.status_code == 200
    assert update.get_json()["full_name"] == "Updated UI Admin"
