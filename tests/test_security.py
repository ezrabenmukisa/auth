from app.extensions import db
from app.models.users import User
from app.models.password_reset import PasswordResetToken
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash


def create_test_user():

    return User(
        username="securityuser",
        email="security@test.com",
        password_hash=generate_password_hash(
            "Password123@"
        ),
        is_active=True,
        is_suspended=False
    )


def test_suspended_user_cannot_login(client, app):

    with app.app_context():

        user = create_test_user()

        user.is_suspended = True

        db.session.add(user)
        db.session.commit()


    response = client.post(
        "/api/v1/auth/login",
        json={
            "identifier":"security@test.com",
            "password":"Password123@"
        }
    )


    assert response.status_code == 403



def test_reset_token_expired(client, app):

    with app.app_context():

        user = create_test_user()

        db.session.add(user)
        db.session.commit()


        token = PasswordResetToken(
            user_id=user.id,
            token="expired-token",
            expires_at=datetime.utcnow()-timedelta(hours=1)
        )


        db.session.add(token)
        db.session.commit()


    response = client.post(
        "/api/v1/security/reset-password",
        json={
            "token":"expired-token",
            "password":"NewPassword123@"
        }
    )


    assert response.status_code == 400