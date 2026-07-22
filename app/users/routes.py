
"""User management HTTP routes."""

from flask import jsonify, request

from app.users import users_bp
from app.users.schemas import (
    ValidationError,
    parse_list_query,
    validate_profile_update,
)
from app.users.services import (
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
    }


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
def list_all():
    """List and search users, with pagination."""
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
