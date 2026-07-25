"""Authorization HTTP routes."""

from flask import jsonify, request
from flask_jwt_extended import jwt_required

from app.authorization import authorization_bp
from app.authorization.schemas import (
    ValidationError,
    validate_permission_data,
    validate_role_data,
    validate_user_role_data,
)
from app.authorization.services import (
    AuthorizationError,
    AuthorizationPersistenceError,
    assign_permission_to_role,
    create_permission,
    create_role,
    delete_permission,
    delete_role,
    get_permission,
    get_permissions,
    get_role,
    get_user_role,
    get_role_permissions,
    get_roles,
    remove_permission_from_role,
    require_permission,
    set_user_role,
    update_permission,
    update_role,
)
from app.users.services import UserNotFoundError


def _serialize_role(role):
    """Convert a Role model into JSON."""
    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
    }


def _serialize_permission(permission):
    """Convert a Permission model into JSON."""
    return {
        "id": permission.id,
        "name": permission.name,
        "description": permission.description,
    }


@authorization_bp.post("/roles")
@jwt_required()
@require_permission("roles.create")
def create_role_route():
    """Create a new role."""
    payload = request.get_json(silent=True) or {}

    try:
        clean_data = validate_role_data(payload)

        role = create_role(
            clean_data["name"],
            clean_data["description"],
        )

    except ValidationError as exc:
        return jsonify(errors=exc.errors), 400

    except AuthorizationError as exc:
        return jsonify(error=str(exc)), 400

    except AuthorizationPersistenceError as exc:
        return jsonify(error=str(exc)), 500

    return jsonify(_serialize_role(role)), 201


@authorization_bp.get("/roles")
@jwt_required()
@require_permission("roles.read")
def get_roles_route():
    """Return all roles."""
    roles = get_roles()

    return jsonify(
        [_serialize_role(role) for role in roles]
    )


@authorization_bp.get("/roles/<int:role_id>")
@jwt_required()
@require_permission("roles.read")
def get_role_route(role_id):
    """Return a single role."""

    try:
        role = get_role(role_id)

    except AuthorizationError as exc:
        return jsonify(error=str(exc)), 404

    return jsonify(_serialize_role(role))


@authorization_bp.put("/roles/<int:role_id>")
@jwt_required()
@require_permission("roles.update")
def update_role_route(role_id):
    """Update a role."""
    payload = request.get_json(silent=True) or {}

    try:
        clean_data = validate_role_data(payload)

        role = update_role(
            role_id,
            clean_data["name"],
            clean_data["description"],
        )

    except ValidationError as exc:
        return jsonify(errors=exc.errors), 400

    except AuthorizationError as exc:
        return jsonify(error=str(exc)), 400

    except AuthorizationPersistenceError as exc:
        return jsonify(error=str(exc)), 500

    return jsonify(_serialize_role(role))


@authorization_bp.delete("/roles/<int:role_id>")
@jwt_required()
@require_permission("roles.delete")
def delete_role_route(role_id):
    """Delete a role."""

    try:
        delete_role(role_id)

    except AuthorizationError as exc:
        return jsonify(error=str(exc)), 404

    except AuthorizationPersistenceError as exc:
        return jsonify(error=str(exc)), 500

    return jsonify(message="Role deleted successfully.")

@authorization_bp.get("/users/<int:user_id>/role")
@jwt_required()
@require_permission("roles.read")
def get_user_role_route(user_id):
    """Return the role assigned to a user."""

    try:
        role = get_user_role(user_id)

    except UserNotFoundError as exc:
        return jsonify(error=str(exc)), 404

    return jsonify(_serialize_role(role))

@authorization_bp.post("/permissions")
@jwt_required()
@require_permission("permissions.create")
def create_permission_route():
    """Create a new permission."""
    payload = request.get_json(silent=True) or {}

    try:
        clean_data = validate_permission_data(payload)

        permission = create_permission(
            clean_data["name"],
            clean_data["description"],
        )

    except ValidationError as exc:
        return jsonify(errors=exc.errors), 400

    except AuthorizationError as exc:
        return jsonify(error=str(exc)), 400

    except AuthorizationPersistenceError as exc:
        return jsonify(error=str(exc)), 500

    return jsonify(_serialize_permission(permission)), 201


@authorization_bp.get("/permissions")
@jwt_required()
@require_permission("permissions.read")
def get_permissions_route():
    """Return all permissions."""
    permissions = get_permissions()

    return jsonify(
        [
            _serialize_permission(permission)
            for permission in permissions
        ]
    )


@authorization_bp.get("/permissions/<int:permission_id>")
@jwt_required()
@require_permission("permissions.read")
def get_permission_route(permission_id):
    """Return a single permission."""

    try:
        permission = get_permission(permission_id)

    except AuthorizationError as exc:
        return jsonify(error=str(exc)), 404

    return jsonify(_serialize_permission(permission))


@authorization_bp.put("/permissions/<int:permission_id>")
@jwt_required()
@require_permission("permissions.update")
def update_permission_route(permission_id):
    """Update a permission."""
    payload = request.get_json(silent=True) or {}

    try:
        clean_data = validate_permission_data(payload)

        permission = update_permission(
            permission_id,
            clean_data["name"],
            clean_data["description"],
        )

    except ValidationError as exc:
        return jsonify(errors=exc.errors), 400

    except AuthorizationError as exc:
        return jsonify(error=str(exc)), 400

    except AuthorizationPersistenceError as exc:
        return jsonify(error=str(exc)), 500

    return jsonify(_serialize_permission(permission))


@authorization_bp.delete("/permissions/<int:permission_id>")
@jwt_required()
@require_permission("permissions.delete")
def delete_permission_route(permission_id):
    """Delete a permission."""

    try:
        delete_permission(permission_id)

    except AuthorizationError as exc:
        return jsonify(error=str(exc)), 404

    except AuthorizationPersistenceError as exc:
        return jsonify(error=str(exc)), 500

    return jsonify(
        message="Permission deleted successfully."
    )
@authorization_bp.get("/roles/<int:role_id>/permissions")
@jwt_required()
@require_permission("permissions.read")
def get_role_permissions_route(role_id):
    """Return all permissions assigned to a role."""

    try:
        permissions = get_role_permissions(role_id)

    except AuthorizationError as exc:
        return jsonify(error=str(exc)), 404

    return jsonify(
        [
            _serialize_permission(permission)
            for permission in permissions
        ]
    )


@authorization_bp.post(
    "/roles/<int:role_id>/permissions/<int:permission_id>"
)
@jwt_required()
@require_permission("permissions.assign")
def assign_permission_to_role_route(
    role_id,
    permission_id,
):
    """Assign a permission to a role."""

    try:
        role = assign_permission_to_role(
            role_id,
            permission_id,
        )

    except AuthorizationError as exc:
        return jsonify(error=str(exc)), 400

    except AuthorizationPersistenceError as exc:
        return jsonify(error=str(exc)), 500

    return jsonify(_serialize_role(role))


@authorization_bp.delete(
    "/roles/<int:role_id>/permissions/<int:permission_id>"
)
@jwt_required()
@require_permission("permissions.assign")
def remove_permission_from_role_route(
    role_id,
    permission_id,
):
    """Remove a permission from a role."""

    try:
        role = remove_permission_from_role(
            role_id,
            permission_id,
        )

    except AuthorizationError as exc:
        return jsonify(error=str(exc)), 400

    except AuthorizationPersistenceError as exc:
        return jsonify(error=str(exc)), 500

    return jsonify(_serialize_role(role))


@authorization_bp.put("/users/<int:user_id>/role")
@jwt_required()
@require_permission("roles.assign")
def set_user_role_route(user_id):
    """Assign a role to a user."""
    payload = request.get_json(silent=True) or {}

    try:
        clean_data = validate_user_role_data(payload)

        user = set_user_role(
            user_id,
            clean_data["role_id"],
        )

    except ValidationError as exc:
        return jsonify(errors=exc.errors), 400

    except UserNotFoundError as exc:
        return jsonify(error=str(exc)), 404

    except AuthorizationError as exc:
        return jsonify(error=str(exc)), 400

    except AuthorizationPersistenceError as exc:
        return jsonify(error=str(exc)), 500

    return jsonify(
        {
            "message": "Role assigned successfully.",
            "user_id": user.id,
            "role": _serialize_role(user.role),
        }
    )
