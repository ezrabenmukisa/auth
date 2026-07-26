"""RBAC and bootstrap-administrator seed command."""

import click
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models.permissions import Permission
from app.models.roles import Role
from app.models.users import User
from app.modules.authentication.schemas import (
    ValidationError as AuthenticationValidationError,
)
from app.modules.authentication.schemas import validate_registration_data
from app.modules.authentication.services import register_user_account
from app.modules.authorization.services import (
    AuthorizationPersistenceError,
    set_user_role,
)
from app.modules.users.services import DuplicateUserError, UserPersistenceError


class SeedError(Exception):
    """Raised when seed data cannot be installed safely."""


AUTHORIZATION_PERMISSIONS = [
    ("roles.create", "Create roles"),
    ("roles.read", "View roles"),
    ("roles.update", "Edit roles"),
    ("roles.delete", "Delete roles"),
    ("roles.assign", "Assign a role to a user"),
    ("permissions.create", "Create permissions"),
    ("permissions.read", "View permissions"),
    ("permissions.update", "Edit permissions"),
    ("permissions.delete", "Delete permissions"),
    ("permissions.assign", "Assign or remove a permission on a role"),
]

ROLE_PERMISSIONS = {
    "Employee": set(),
    "Accountant": {"permissions.read"},
    "Manager": {"roles.read", "permissions.read"},
    "Admin": {name for name, _ in AUTHORIZATION_PERMISSIONS},
}

ROLE_DESCRIPTIONS = {
    "Employee": "Default role for new registrations",
    "Accountant": "Financial and audit visibility",
    "Manager": "Read-only role and permission visibility",
    "Admin": "Full administrative access",
}


def _seed_rbac_data() -> dict[str, Role]:
    """Create or synchronize roles, permissions, and their mappings."""
    try:
        roles = {}
        for name, description in ROLE_DESCRIPTIONS.items():
            role = db.session.scalar(db.select(Role).where(Role.name == name))
            if role is None:
                role = Role(name=name)
                db.session.add(role)
            role.description = description
            roles[name] = role

        permissions = {}
        for name, description in AUTHORIZATION_PERMISSIONS:
            permission = db.session.scalar(
                db.select(Permission).where(Permission.name == name)
            )
            if permission is None:
                permission = Permission(name=name)
                db.session.add(permission)
            permission.description = description
            permissions[name] = permission

        db.session.flush()
        for role_name, permission_names in ROLE_PERMISSIONS.items():
            roles[role_name].permissions = [
                permissions[name] for name in sorted(permission_names)
            ]

        db.session.commit()
        return roles
    except SQLAlchemyError as exc:
        db.session.rollback()
        raise SeedError("Could not seed RBAC roles and permissions.") from exc


def _validate_admin_registration_data(raw_data: dict) -> dict:
    """Validate bootstrap administrator credentials."""
    try:
        return validate_registration_data(raw_data)
    except AuthenticationValidationError as exc:
        raise SeedError(f"Invalid administrator details: {exc.errors}") from exc


def _seed_admin(admin_role: Role, admin_data: dict) -> User:
    """Create the bootstrap administrator or reconcile its role."""
    existing_by_username = db.session.scalar(
        db.select(User).where(User.username == admin_data["username"])
    )
    existing_by_email = db.session.scalar(
        db.select(User).where(User.email == admin_data["email"])
    )

    if (
        existing_by_username is not None
        and existing_by_email is not None
        and existing_by_username.id != existing_by_email.id
    ):
        raise SeedError("Administrator username and email belong to different users.")

    admin_user = existing_by_username or existing_by_email
    if admin_user is None:
        try:
            admin_user = register_user_account(admin_data)
        except (DuplicateUserError, UserPersistenceError) as exc:
            raise SeedError("Could not create the administrator user.") from exc
    elif (
        admin_user.username != admin_data["username"]
        or admin_user.email != admin_data["email"]
    ):
        raise SeedError("Administrator credentials conflict with an existing user.")

    if admin_user.role_id != admin_role.id:
        try:
            admin_user = set_user_role(admin_user.id, admin_role.id)
        except AuthorizationPersistenceError as exc:
            raise SeedError("Could not assign the Admin role.") from exc

    return admin_user


def seed_development_data(admin_data: dict) -> int:
    """Idempotently seed RBAC data and the bootstrap administrator."""
    validated_admin_data = _validate_admin_registration_data(admin_data)
    roles = _seed_rbac_data()
    admin_user = _seed_admin(roles["Admin"], validated_admin_data)
    return admin_user.id


@click.command("seed-db")
def seed_db():
    """Seed RBAC data and an interactively configured administrator."""
    click.echo("Configure the bootstrap administrator.")
    admin_data = {
        "username": click.prompt("Admin username").strip(),
        "email": click.prompt("Admin email").strip(),
        "full_name": click.prompt(
            "Admin full name", default="System Administrator"
        ).strip(),
        "password": click.prompt(
            "Admin password", hide_input=True, confirmation_prompt=True
        ),
    }

    try:
        admin_id = seed_development_data(admin_data)
    except SeedError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo("Seeded roles: Employee, Accountant, Manager, Admin.")
    click.echo("Seeded authorization permissions and role mappings.")
    click.echo(f"Administrator ready (id={admin_id}).")
