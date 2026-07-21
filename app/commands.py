"""Flask CLI commands for database management."""

import click
from flask import current_app

from app.extensions import db
from app.models.roles import Role
from app.models.permissions import Permission


def seed_roles_and_permissions():
    """Insert default roles and permissions if they do not already exist."""
    # Define default permissions from the proposal
    permissions_data = [
        ("users.read", "View user profiles"),
        ("users.update", "Update user profiles"),
        ("users.disable", "Activate or suspend users"),
        ("roles.read", "View roles and permissions"),
        ("roles.manage", "Create, update, and delete roles"),
        ("audit.read", "View audit logs"),
    ]

    # Define default roles and which permissions they get
    roles_data = {
        "Admin": {
            "description": "Full administrative access",
            "permissions": [name for name, _ in permissions_data],  # all
        },
        "Manager": {
            "description": "Manage users and roles",
            "permissions": ["users.read", "users.update", "roles.read"],
        },
        "User": {
            "description": "Standard user with basic access",
            "permissions": ["users.read"],
        },
    }

    # 1. Create permissions (skip if already exist)
    created_perms = {}
    for name, desc in permissions_data:
        perm = Permission.query.filter_by(name=name).first()
        if not perm:
            perm = Permission(name=name, description=desc)
            db.session.add(perm)
            current_app.logger.info(f"Created permission: {name}")
        created_perms[name] = perm
    db.session.commit()

    # 2. Create roles and assign permissions
    for role_name, role_info in roles_data.items():
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            role = Role(name=role_name, description=role_info["description"])
            db.session.add(role)
            db.session.flush()  # get the role id

            # Assign permissions
            for perm_name in role_info["permissions"]:
                perm = created_perms.get(perm_name)
                if perm and perm not in role.permissions:
                    role.permissions.append(perm)

            db.session.add(role)
            current_app.logger.info(
                f"Created role: {role_name} with {len(role.permissions)} permissions")
        else:
            # If role exists, ensure it has the correct permissions (optional update)
            # This is useful if permissions change later
            for perm_name in role_info["permissions"]:
                perm = created_perms.get(perm_name)
                if perm and perm not in role.permissions:
                    role.permissions.append(perm)
            current_app.logger.info(f"Updated role: {role_name}")

    db.session.commit()
    current_app.logger.info("Seeding completed successfully.")


@click.command("seed-db")
def seed_db():
    """Seed the database with default roles and permissions."""
    with current_app.app_context():
        seed_roles_and_permissions()
    click.echo(" Database seeded with default roles and permissions.")
