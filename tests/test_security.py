"""Tests for password security, suspension, and audit behavior."""

from datetime import datetime, timedelta, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from app.cli.seed import seed_development_data
from app.extensions import db
from app.models.audit_logs import AuditLog
from app.models.password_reset import PasswordResetToken
from app.models.roles import Role
from app.models.users import User
from app.modules.authentication.services import issue_token_pair
from app.modules.security.services import send_password_reset_email
from app.modules.users.services import create_user


def create_test_user(username="securityuser", role_name="Employee"):
    role = db.session.scalar(db.select(Role).where(Role.name == role_name))
    return create_user(
        {
            "username": username,
            "email": f"{username}@test.com",
            "full_name": "Security User",
        },
        password_hash=generate_password_hash("Password123@"),
        role=role,
    )


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def test_suspended_user_cannot_login(app, client):
    with app.app_context():
        user = create_test_user()
        user.is_suspended = True
        db.session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": "security@test.com", "password": "Password123@"},
    )

    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid username/email or password."


def test_forgot_password_does_not_disclose_missing_account(client):
    response = client.post(
        "/api/v1/security/forgot-password",
        json={"email": "missing@test.com"},
    )

    assert response.status_code == 200
    assert "reset_token" not in response.get_json()


def test_reset_email_uses_configured_smtp(app, monkeypatch):
    sent = {}

    class FakeSMTP:
        def __init__(self, server, port, **options):
            sent["connection"] = (server, port, options)

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def login(self, username, password):
            sent["login"] = (username, password)

        def send_message(self, message):
            sent["message"] = message

    monkeypatch.setattr("app.modules.security.services.smtplib.SMTP_SSL", FakeSMTP)
    app.config.update(
        MAIL_SERVER="smtp.gmail.com",
        MAIL_PORT=465,
        MAIL_USE_SSL=True,
        MAIL_USERNAME="sender@example.com",
        MAIL_PASSWORD="app-password",
        MAIL_DEFAULT_SENDER="sender@example.com",
        PUBLIC_APP_URL="https://auth.example.com",
    )

    with app.app_context():
        delivered = send_password_reset_email("user@example.com", "reset-token")

    assert delivered is True
    assert sent["login"] == ("sender@example.com", "app-password")
    assert sent["message"]["To"] == "user@example.com"
    assert (
        "https://auth.example.com/reset-password?token=reset-token"
        in sent["message"].get_content()
    )


def test_reset_token_is_single_use(app, client):
    with app.app_context():
        user = create_test_user()
        user_id = user.id
        email = user.email

    request_response = client.post(
        "/api/v1/security/forgot-password",
        json={"email": email},
    )
    token = request_response.get_json()["reset_token"]

    first = client.post(
        "/api/v1/security/reset-password",
        json={"token": token, "password": "NewPassword123@"},
    )
    second = client.post(
        "/api/v1/security/reset-password",
        json={"token": token, "password": "AnotherPassword123@"},
    )

    assert first.status_code == 200
    assert second.status_code == 400
    with app.app_context():
        refreshed_user = db.session.get(User, user_id)
        assert check_password_hash(refreshed_user.password_hash, "NewPassword123@")
        reset = PasswordResetToken.query.one()
        assert reset.token != token
        assert reset.used is True


def test_expired_reset_token_is_rejected(app, client):
    with app.app_context():
        user = create_test_user()
        db.session.add(
            PasswordResetToken(
                user_id=user.id,
                token="b52b3ef2233858ce1156d85f235cf2c41eddfa8ca1eedc924398b9af1db303cb",
                expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            )
        )
        db.session.commit()

    response = client.post(
        "/api/v1/security/reset-password",
        json={"token": "expired-token", "password": "NewPassword123@"},
    )

    assert response.status_code == 400


def test_admin_can_suspend_and_reactivate_another_user(app, client):
    with app.app_context():
        seed_development_data(
            {
                "username": "security-admin",
                "email": "security-admin@test.com",
                "password": "secure-admin-password",
                "full_name": "Security Admin",
            }
        )
        admin = User.query.filter_by(username="security-admin").one()
        employee = create_test_user("employee")
        employee_id = employee.id
        token = issue_token_pair(admin)["access_token"]

    suspend = client.post(
        f"/api/v1/security/users/{employee_id}/suspend",
        headers=bearer(token),
    )
    activate = client.post(
        f"/api/v1/security/users/{employee_id}/activate",
        headers=bearer(token),
    )

    assert suspend.status_code == 200
    assert activate.status_code == 200
    with app.app_context():
        assert db.session.get(User, employee_id).is_suspended is False


def test_employee_cannot_suspend_users(app, client):
    with app.app_context():
        employee = create_test_user()
        other_user = create_test_user("other")
        other_user_id = other_user.id
        token = issue_token_pair(employee)["access_token"]

    response = client.post(
        f"/api/v1/security/users/{other_user_id}/suspend",
        headers=bearer(token),
    )

    assert response.status_code == 403


def test_admin_can_view_audit_activity(app, client):
    with app.app_context():
        seed_development_data(
            {
                "username": "audit-admin",
                "email": "audit-admin@test.com",
                "password": "secure-admin-password",
                "full_name": "Audit Admin",
            }
        )
        admin = User.query.filter_by(username="audit-admin").one()
        token = issue_token_pair(admin)["access_token"]
        db.session.add(
            AuditLog(user_id=admin.id, action="TEST_EVENT", status="SUCCESS")
        )
        db.session.commit()

    response = client.get(
        "/api/v1/security/audit-logs",
        headers=bearer(token),
    )

    assert response.status_code == 200
    assert response.get_json()["events"][0]["action"] == "TEST_EVENT"


def test_employee_cannot_view_audit_activity(app, client):
    with app.app_context():
        employee = create_test_user()
        token = issue_token_pair(employee)["access_token"]

    response = client.get(
        "/api/v1/security/audit-logs",
        headers=bearer(token),
    )

    assert response.status_code == 403
