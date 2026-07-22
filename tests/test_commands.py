"""Tests for the database seeding command."""

from app.models.permissions import Permission
from app.models.roles import Role


def test_seed_roles_and_permissions_is_idempotent(app):
    """Running the seed function twice does not create duplicates."""
    from app.commands import seed_roles_and_permissions

    with app.app_context():
        seed_roles_and_permissions()
        first_role_count = Role.query.count()
        first_perm_count = Permission.query.count()

        seed_roles_and_permissions()
        second_role_count = Role.query.count()
        second_perm_count = Permission.query.count()

    assert first_role_count == second_role_count
    assert first_perm_count == second_perm_count
