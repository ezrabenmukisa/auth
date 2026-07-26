"""Authorization business logic."""

from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models.permissions import Permission
from app.models.roles import Role
from app.models.users import User
from app.modules.authentication.services import (
    AuthenticationError,
    get_active_user,
)
from app.modules.users.services import UserNotFoundError


class AuthorizationError(Exception):
    """Raised when an authorization rule is violated."""


class AuthorizationPersistenceError(Exception):
    """Raised when authorization changes cannot be persisted."""


def create_role(name, description):
    existing_role = db.session.scalar(db.select(Role).where(Role.name == name))

    if existing_role is not None:
        raise AuthorizationError("Role already exists.")

    role = Role(
        name=name,
        description=description,
    )

    try:
        db.session.add(role)
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        raise AuthorizationPersistenceError("Could not create role.") from exc

    return role


def get_role(role_id):
    role = db.session.get(Role, role_id)

    if role is None:
        raise AuthorizationError("Role not found.")

    return role


def get_roles():
    return db.session.scalars(db.select(Role)).all()


def get_user_role(user_id):
    user = db.session.get(User, user_id)

    if user is None:
        raise UserNotFoundError(f"No user with id {user_id}")

    return user.role


def update_role(role_id, new_name, new_description):
    role = db.session.get(Role, role_id)

    if role is None:
        raise AuthorizationError("Role not found.")

    existing_role = db.session.scalar(db.select(Role).where(Role.name == new_name))

    if existing_role is not None and existing_role.id != role_id:
        raise AuthorizationError("Role already exists.")

    role.name = new_name
    role.description = new_description

    try:
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        raise AuthorizationPersistenceError("Could not update role.") from exc

    return role


def delete_role(role_id):
    role = db.session.get(Role, role_id)

    if role is None:
        raise AuthorizationError("Role not found.")

    if role.users:
        raise AuthorizationError(
            "Cannot delete a role that is still assigned to users. "
            "Reassign those users to another role first."
        )

    try:
        db.session.delete(role)
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        raise AuthorizationPersistenceError("Could not delete role.") from exc

    return role


def create_permission(name, description):
    existing_permission = db.session.scalar(
        db.select(Permission).where(Permission.name == name)
    )

    if existing_permission is not None:
        raise AuthorizationError("Permission already exists.")

    permission = Permission(
        name=name,
        description=description,
    )

    try:
        db.session.add(permission)
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        raise AuthorizationPersistenceError("Could not create permission.") from exc

    return permission


def get_permission(permission_id):
    permission = db.session.get(Permission, permission_id)

    if permission is None:
        raise AuthorizationError("Permission not found.")

    return permission


def get_permissions():
    return db.session.scalars(db.select(Permission)).all()


def update_permission(permission_id, new_name, new_description):
    permission = db.session.get(Permission, permission_id)

    if permission is None:
        raise AuthorizationError("Permission not found.")

    existing_permission = db.session.scalar(
        db.select(Permission).where(Permission.name == new_name)
    )

    if existing_permission is not None and existing_permission.id != permission_id:
        raise AuthorizationError("Permission already exists.")

    permission.name = new_name
    permission.description = new_description

    try:
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        raise AuthorizationPersistenceError("Could not update permission.") from exc

    return permission


def delete_permission(permission_id):
    permission = db.session.get(Permission, permission_id)

    if permission is None:
        raise AuthorizationError("Permission not found.")

    try:
        db.session.delete(permission)
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        raise AuthorizationPersistenceError("Could not delete permission.") from exc

    return permission


def get_role_permissions(role_id):
    role = db.session.get(Role, role_id)

    if role is None:
        raise AuthorizationError("Role not found.")

    return role.permissions


def set_user_role(user_id, role_id):
    user = db.session.get(User, user_id)

    if user is None:
        raise UserNotFoundError(f"No user with id {user_id}")

    role = db.session.get(Role, role_id)

    if role is None:
        raise AuthorizationError("Role not found.")

    user.role = role

    try:
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        raise AuthorizationPersistenceError("Could not assign role to user.") from exc

    return user


def has_permission(user, permission_name):
    if user.role is None:
        return False

    for permission in user.role.permissions:
        if permission.name == permission_name:
            return True

    return False


def assign_permission_to_role(role_id, permission_id):
    role = db.session.get(Role, role_id)

    if role is None:
        raise AuthorizationError("Role not found.")

    permission = db.session.get(Permission, permission_id)

    if permission is None:
        raise AuthorizationError("Permission not found.")

    if permission in role.permissions:
        raise AuthorizationError("Permission is already assigned to the role.")

    role.permissions.append(permission)

    try:
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        raise AuthorizationPersistenceError(
            "Could not assign permission to role."
        ) from exc

    return role


def remove_permission_from_role(role_id, permission_id):
    role = db.session.get(Role, role_id)

    if role is None:
        raise AuthorizationError("Role not found.")

    permission = db.session.get(Permission, permission_id)

    if permission is None:
        raise AuthorizationError("Permission not found.")

    if permission not in role.permissions:
        raise AuthorizationError("Permission is not assigned to the role.")

    role.permissions.remove(permission)

    try:
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        raise AuthorizationPersistenceError(
            "Could not remove permission from role."
        ) from exc

    return role


def require_permission(permission_name):
    """Ensure the authenticated user has the required permission."""

    def decorator(function):

        @wraps(function)
        def wrapper(*args, **kwargs):
            try:
                user = get_active_user(get_jwt_identity())
            except AuthenticationError as exc:
                return jsonify(error=str(exc)), 401

            if not has_permission(user, permission_name):
                return jsonify(error="Permission denied."), 403

            return function(*args, **kwargs)

        return wrapper

    return decorator
