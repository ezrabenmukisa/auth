"""User management HTTP routes."""

from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models.users import User
from app.modules.users import users_bp
from app.modules.users.schemas import (
    ValidationError,
    parse_list_query,
    validate_profile_update,
)
from app.modules.users.services import (
    UserNotFoundError,
    UserPersistenceError,
    get_user_by_id,
    list_users,
    update_profile,
)


def _serialize_user(user):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_suspended": user.is_suspended,
    }


def _authorize_profile_owner(user_id):
    """Return an error response when the JWT does not own the profile."""
    try:
        authenticated_user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return jsonify(error="Invalid authentication identity."), 401

    authenticated_user = db.session.get(User, authenticated_user_id)
    if (
        authenticated_user is None
        or not authenticated_user.is_active
        or authenticated_user.is_suspended
    ):
        return jsonify(error="Account is inactive or unavailable."), 401
    if authenticated_user_id != user_id:
        return jsonify(error="You can only access your own profile."), 403
    return None


@users_bp.get("/<int:user_id>")
@jwt_required()
def get_profile(user_id):
    """View a user's profile."""
    try:
        user = get_user_by_id(user_id)
    except UserNotFoundError:
        return jsonify(error="User not found"), 404

    authorization_error = _authorize_profile_owner(user_id)
    if authorization_error is not None:
        return authorization_error
    return jsonify(_serialize_user(user)), 200


@users_bp.patch("/<int:user_id>")
@jwt_required()
def patch_profile(user_id):
    """Update a user's own profile."""
    payload = request.get_json(silent=True) or {}

    try:
        get_user_by_id(user_id)
        authorization_error = _authorize_profile_owner(user_id)
        if authorization_error is not None:
            return authorization_error
        clean_data = validate_profile_update(payload)
        user = update_profile(user_id, clean_data)
    except ValidationError as exc:
        return jsonify(errors=exc.errors), 400
    except UserNotFoundError:
        return jsonify(error="User not found"), 404
    except UserPersistenceError as exc:
        return jsonify(error=str(exc)), 500

    return jsonify(_serialize_user(user)), 200


@users_bp.get("/")
@jwt_required()
def list_all():
    """List and search users, with pagination."""
    from app.modules.authentication.services import (
        AuthenticationError,
        get_active_user,
    )
    from app.modules.authorization.services import has_permission

    try:
        authenticated_user = get_active_user(get_jwt_identity())
    except AuthenticationError as exc:
        return jsonify(error=str(exc)), 401
    if not has_permission(authenticated_user, "users.read"):
        return jsonify(error="Permission denied."), 403

    try:
        query_params = parse_list_query(request.args)
    except ValidationError as exc:
        return jsonify(errors=exc.errors), 400

    pagination = list_users(**query_params)

    return (
        jsonify(
            users=[_serialize_user(user) for user in pagination.items],
            page=pagination.page,
            per_page=pagination.per_page,
            total=pagination.total,
            total_pages=pagination.pages,
        ),
        200,
    )
