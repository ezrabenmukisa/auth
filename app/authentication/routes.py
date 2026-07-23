"""Authentication HTTP routes."""

from flask import jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from app.authentication import authentication_bp
from app.authentication.schemas import (
    ValidationError,
    validate_login_data,
    validate_registration_data,
)
from app.authentication.services import (
    AuthenticationError,
    authenticate_user,
    get_active_user,
    issue_refreshed_access_token,
    issue_token_pair,
    register_user_account,
    revoke_session,
)
from app.users.services import DuplicateUserError, UserPersistenceError


def _serialize_user(user):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
    }


@authentication_bp.post("/register")
def register():
    """Register a user with a securely hashed password."""
    payload = request.get_json(silent=True) or {}
    try:
        clean_data = validate_registration_data(payload)
        user = register_user_account(clean_data)
    except ValidationError as exc:
        return jsonify(errors=exc.errors), 400
    except DuplicateUserError as exc:
        return jsonify(error=str(exc)), 409
    except UserPersistenceError as exc:
        return jsonify(error=str(exc)), 500
    return jsonify(_serialize_user(user)), 201


@authentication_bp.post("/login")
def login():
    """Authenticate an active user and issue an access/refresh token pair."""
    payload = request.get_json(silent=True) or {}
    try:
        clean_data = validate_login_data(payload)
        user = authenticate_user(**clean_data)
    except ValidationError as exc:
        return jsonify(errors=exc.errors), 400
    except AuthenticationError as exc:
        return jsonify(error=str(exc)), 401
    return jsonify(**issue_token_pair(user), token_type="Bearer"), 200


@authentication_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    """Exchange a valid refresh token for a new access token."""
    try:
        access_token = issue_refreshed_access_token(get_jwt_identity(), get_jwt())
    except AuthenticationError as exc:
        return jsonify(error=str(exc)), 401
    return jsonify(access_token=access_token, token_type="Bearer"), 200


@authentication_bp.post("/logout")
@jwt_required(verify_type=False)
def logout():
    """Revoke the session shared by the presented access and refresh tokens."""
    revoke_session(get_jwt())
    return jsonify(message="Successfully logged out."), 200


@authentication_bp.get("/protected")
@jwt_required()
def protected():
    """Return a protected response for an active authenticated user."""
    try:
        user = get_active_user(get_jwt_identity())
    except AuthenticationError as exc:
        return jsonify(error=str(exc)), 401
    return jsonify(message="Protected resource accessed.", user_id=user.id), 200
