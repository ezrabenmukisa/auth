import secrets
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.password_reset import PasswordResetToken
from app.models.user import User
from app.extensions import db

def change_password(user, current_password, new_password):
    if not check_password_hash(user.password_hash, current_password):
        raise ValueError("Incorrect current password")

    user.password_hash = generate_password_hash(new_password)
    db.session.commit()


def generate_reset_token(user):
    token = secrets.token_urlsafe(32)

    reset = PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(minutes=15)
    )

    db.session.add(reset)
    db.session.commit()

    return token


def reset_password(token, new_password):
    reset = PasswordResetToken.query.filter_by(token=token).first()

    if not reset or reset.used or reset.expires_at < datetime.utcnow():
        raise ValueError("Invalid or expired token")

    user = User.query.get(reset.user_id)
    user.password_hash = generate_password_hash(new_password)

    reset.used = True
    db.session.commit()