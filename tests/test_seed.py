"""Tests for RBAC and bootstrap-administrator seeding."""

from app.cli.seed import AUTHORIZATION_PERMISSIONS, ROLE_PERMISSIONS
from app.models.permissions import Permission
from app.models.roles import Role
from app.models.users import User
from app.modules.authentication.services import verify_password

ADMIN_INPUT = (
    "bootstrap-admin\n"
    "admin@example.com\n"
    "Bootstrap Admin\n"
    "secure-admin-password\n"
    "secure-admin-password\n"
)


def test_seed_command_creates_expected_data_idempotently(app):
    runner = app.test_cli_runner()

    first_result = runner.invoke(args=["seed-db"], input=ADMIN_INPUT)
    second_result = runner.invoke(args=["seed-db"], input=ADMIN_INPUT)

    assert first_result.exit_code == 0, first_result.output
    assert second_result.exit_code == 0, second_result.output

    with app.app_context():
        roles = {role.name: role for role in Role.query.all()}
        permissions = {
            permission.name: permission for permission in Permission.query.all()
        }
        admin = User.query.filter_by(username="bootstrap-admin").one()

        assert set(roles) == {"Employee", "Accountant", "Manager", "Admin"}
        assert set(permissions) == {name for name, _ in AUTHORIZATION_PERMISSIONS}
        assert {
            role_name: {permission.name for permission in roles[role_name].permissions}
            for role_name in roles
        } == ROLE_PERMISSIONS
        assert admin.role.name == "Admin"
        assert admin.email == "admin@example.com"
        assert verify_password(admin, "secure-admin-password")
        assert User.query.count() == 1


def test_seed_command_rejects_invalid_admin_details(app):
    result = app.test_cli_runner().invoke(
        args=["seed-db"],
        input="admin\ninvalid-email\n\nshort\nshort\n",
    )

    assert result.exit_code != 0
    assert "Invalid administrator details" in result.output
    with app.app_context():
        assert User.query.count() == 0
