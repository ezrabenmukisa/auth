
"""User management HTTP routes."""

from flask import jsonify, request

from app.users import users_bp
from app.users.schemas import ValidationError, parse_list_query, validate_registration_data

from app.users.services import (
    DuplicateUserError,
    UserNotFoundError,
    get_user_by_id,
    list_users,
    register_user,
    update_profile,
)


def _serialize_user(user):
    """Return a safe, public representation of a user (no password hash)."""
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "role_id": user.role_id,
    }


@users_bp.post("/register")
def register():
    """Register a new user account."""
    payload = request.get_json(silent=True) or {}

    try:
        clean_data = validate_registration_data(payload)
    except ValidationError as exc:
        return jsonify(errors=exc.errors), 400

    try:
        user = register_user(clean_data)
    except DuplicateUserError as exc:
        return jsonify(error=str(exc)), 409

    return jsonify(_serialize_user(user)), 201


@users_bp.get("/<int:user_id>")
def get_profile(user_id):
    """View a user's profile."""
    try:
        user = get_user_by_id(user_id)
    except UserNotFoundError:
        return jsonify(error="User not found"), 404

    return jsonify(_serialize_user(user)), 200


@users_bp.patch("/<int:user_id>")
def patch_profile(user_id):
    """Update a user's own profile."""
    payload = request.get_json(silent=True) or {}

    try:
        user = update_profile(user_id, payload)
    except UserNotFoundError:
        return jsonify(error="User not found"), 404

    return jsonify(_serialize_user(user)), 200


@users_bp.get("/")
def list_all():
    """List and search users, with pagination."""
    query_params = parse_list_query(request.args)

    from app.users.services import list_users

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
