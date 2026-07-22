"""Authentication and JWT lifecycle business logic."""

from datetime import datetime, timezone
from uuid import uuid4

from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models.revoked_tokens import RevokedToken
from app.models.users import User
from app.users.services import create_user


class AuthenticationError(Exception):
    """Raised when credentials or account state prevent authentication."""


def register_user_account(data: dict) -> User:
    """Hash a registration password and delegate user persistence."""
    user_data = {key: value for key, value in data.items() if key != "password"}
    password_hash = generate_password_hash(data["password"])
    return create_user(user_data, password_hash=password_hash)


def verify_password(user: User, password: str) -> bool:
    """Safely compare a plaintext password with its stored hash."""
    return check_password_hash(user.password_hash, password)


def authenticate_user(identifier: str, password: str) -> User:
    """Return an active user when the supplied credentials are valid."""
    user = db.session.scalar(
        db.select(User).where(
            db.or_(User.username == identifier, User.email == identifier.lower())
        )
    )

    if user is None or not verify_password(user, password) or not user.is_active:
        raise AuthenticationError("Invalid username/email or password.")
    return user


def issue_token_pair(user: User) -> dict[str, str]:
    """Issue access and refresh tokens belonging to one revocable session."""
    session_id = str(uuid4())
    session_expires_at = datetime.now(timezone.utc) + current_app.config[
        "JWT_REFRESH_TOKEN_EXPIRES"
    ]
    claims = {
        "sid": session_id,
        "session_expires_at": int(session_expires_at.timestamp()),
    }
    identity = str(user.id)
    return {
        "access_token": create_access_token(
            identity=identity, additional_claims=claims
        ),
        "refresh_token": create_refresh_token(
            identity=identity, additional_claims=claims
        ),
    }


def issue_refreshed_access_token(user_id: str, jwt_claims: dict) -> str:
    """Issue another access token for an active authenticated user."""
    user = db.session.get(User, int(user_id))
    if user is None or not user.is_active:
        raise AuthenticationError("Account is inactive or unavailable.")
    claims = {
        "sid": jwt_claims["sid"],
        "session_expires_at": jwt_claims["session_expires_at"],
    }
    return create_access_token(identity=str(user.id), additional_claims=claims)


def get_active_user(user_id: str) -> User:
    """Return the active user represented by a valid access token."""
    user = db.session.get(User, int(user_id))
    if user is None or not user.is_active:
        raise AuthenticationError("Account is inactive or unavailable.")
    return user


def revoke_session(jwt_claims: dict) -> RevokedToken:
    """Revoke the session shared by an access/refresh token pair."""
    session_id = jwt_claims["sid"]
    existing = RevokedToken.query.filter_by(session_id=session_id).first()
    if existing is not None:
        return existing

    revoked = RevokedToken(
        session_id=session_id,
        expires_at=datetime.fromtimestamp(
            jwt_claims["session_expires_at"], tz=timezone.utc
        ),
    )
    db.session.add(revoked)
    db.session.commit()
    return revoked


def is_session_revoked(jwt_claims: dict) -> bool:
    """Return whether the token's login session is in the blocklist."""
    session_id = jwt_claims.get("sid")
    return bool(
        session_id
        and RevokedToken.query.filter_by(session_id=session_id).first() is not None
    )
