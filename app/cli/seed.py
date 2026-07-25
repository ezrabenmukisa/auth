"""Development database seed command."""

import os

import click
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models.roles import Role
from app.models.permissions import Permission
from app.models.users import User
from app.authentication.services import register_user_account
from app.users.services import (
    DuplicateUserError,
    UserPersistenceError,
)
from app.authorization.services import set_user_role, AuthorizationError


class SeedError(Exception):
    """Raised when development seed work cannot complete safely."""



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
    ("permissions.assign", "Assign/remove a permission on a role"),
    
]


ROLE_PERMISSIONS = {
    "Employee": [],
    "Accountant": [
        "permissions.read",
    ],
    "Manager": [
        "roles.read",
        "permissions.read",
    ],
    "Admin": [name for name, _ in AUTHORIZATION_PERMISSIONS],
}

ROLE_DESCRIPTIONS = {
    "Employee": "Default role for new sign-ups",
    "Accountant": "Financial and audit visibility",
    "Manager": "Limited administrative access",
    "Admin": "Full administrative access",
}


def _get_or_create_role(name):
    role = db.session.scalar(db.select(Role).where(Role.name == name))
    if role is None:
        role = Role(name=name, description=ROLE_DESCRIPTIONS[name])
        db.session.add(role)
        db.session.flush()
    return role


def _get_or_create_permission(name, description):
    permission = db.session.scalar(
        db.select(Permission).where(Permission.name == name)
    )
    if permission is None:
        permission = Permission(name=name, description=description)
        db.session.add(permission)
        db.session.flush()
    return permission


def seed_development_data() -> int:
    """Idempotent: safe to run multiple times. Returns the admin user's id."""
    try:
        
            # 'Employee' must be created first in a fresh DB so it lands on
            # id 1 (User.role_id defaults to 1 for new sign-ups).
            employee_role = _get_or_create_role("Employee")
            accountant_role = _get_or_create_role("Accountant")
            manager_role = _get_or_create_role("Manager")
            admin_role = _get_or_create_role("Admin")

            roles_by_name = {
                "Employee": employee_role,
                "Accountant": accountant_role,
                "Manager": manager_role,
                "Admin": admin_role,
            }

            permissions_by_name = {
                name: _get_or_create_permission(name, description)
                for name, description in AUTHORIZATION_PERMISSIONS
            }

            for role_name, permission_names in ROLE_PERMISSIONS.items():
                role = roles_by_name[role_name]
                for permission_name in permission_names:
                    permission = permissions_by_name[permission_name]
                    if permission not in role.permissions:
                        role.permissions.append(permission)
            db.session.commit()

            if employee_role.id != 1:
                click.echo(
                    f"WARNING: 'Employee' role has id {employee_role.id}, not 1. "
                    "New sign-ups will default to the wrong role."
                )

            # ---- bootstrap admin user ----
            admin_email = os.environ.get("SEED_ADMIN_EMAIL", "admin@example.com")
            admin_username = os.environ.get("SEED_ADMIN_USERNAME", "admin")
            admin_password = os.environ.get("SEED_ADMIN_PASSWORD")

            if not admin_password:
                raise SeedError(
                    "Set SEED_ADMIN_PASSWORD in your environment before seeding "
                    "(don't hardcode a real password in this file)."
                )

            existing_admin = db.session.scalar(
                db.select(User).where(User.email == admin_email)
            )

            if existing_admin is None:
                try:
                    admin_user = register_user_account(
                        {
                            "username": admin_username,
                            "email": admin_email,
                            "full_name": "System Administrator",
                            "password": admin_password,
                        }
                    )
                except DuplicateUserError as exc:
                    raise SeedError(
                        f"Admin user already exists under a conflicting {exc}."
                    ) from exc
                except UserPersistenceError as exc:
                    raise SeedError("Could not create admin user.") from exc

                # register_user_account creates the user with the default
                # (Employee) role — bump it up to Admin.
                try:
                    set_user_role(admin_user.id, admin_role.id)
                except AuthorizationError as exc:
                    raise SeedError(
                        "Admin user created but role assignment failed."
                    ) from exc

                admin_user_id = admin_user.id
            else:
                admin_user_id = existing_admin.id

            return admin_user_id

    except SQLAlchemyError as exc:
        db.session.rollback()
        raise SeedError("Database seeding failed.") from exc


@click.command("seed-db")
def seed_db():
    """Run explicit, development-only database seeding.

    Requires SEED_ADMIN_PASSWORD to be set in the environment, e.g.:
        SEED_ADMIN_PASSWORD='Str0ngPass!' flask seed-db
    """
    admin_id = seed_development_data()
    click.echo("Seeded roles: Employee, Accountant, Manager, Admin.")
    click.echo(f"Admin user ready (id={admin_id}). Log in and change the password.")
    