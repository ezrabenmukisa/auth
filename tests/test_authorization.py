
import pytest
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models.users import User
from app.models.roles import Role
from app.models.permissions import Permission

from app.authorization.services import (
    AuthorizationError,
    AuthorizationPersistenceError,
    create_role,
    create_permission,
    delete_role,
    assign_permission_to_role,
    remove_permission_from_role,
    set_user_role,
    has_permission,
)

from app.authorization.schemas import (
    ValidationError,
    validate_role_data,
    validate_user_role_data,
)

from app.users.services import UserNotFoundError


# -------------------------------------------------
# Helpers
# -------------------------------------------------

def make_role(name="tester_role", permissions=None):
    role = Role(
        name=name,
        description=None,
    )

    if permissions:
        role.permissions.extend(permissions)

    db.session.add(role)
    db.session.commit()

    return role


def make_permission(name):
    permission = Permission(
        name=name,
        description=None,
    )

    db.session.add(permission)
    db.session.commit()

    return permission


def make_user(username, email, role, is_active=True):
    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash("Password123!"),
        role=role,
        is_active=is_active,
    )

    db.session.add(user)
    db.session.commit()

    return user


# -------------------------------------------------
# Service Tests
# -------------------------------------------------

class TestCreateRole:

    def test_create_role_success(self, app):
        role = create_role(
            "editor",
            "Can edit content",
        )

        assert role.id is not None
        assert role.name == "editor"

    def test_create_duplicate_role_raises(self, app):
        create_role("duplicate_role", None)

        with pytest.raises(AuthorizationError):
            create_role("duplicate_role", None)


class TestCreatePermission:

    def test_create_permission_success(self, app):
        permission = create_permission(
            "reports.read",
            None,
        )

        assert permission.id is not None
        assert permission.name == "reports.read"

    def test_create_duplicate_permission_raises(self, app):
        create_permission("duplicate.permission", None)

        with pytest.raises(AuthorizationError):
            create_permission(
                "duplicate.permission",
                None,
            )


class TestDeleteRole:

    def test_delete_unassigned_role(self, app):
        role = make_role("temporary_role")

        delete_role(role.id)

        assert db.session.get(Role, role.id) is None

    def test_delete_unknown_role(self, app):
        with pytest.raises(AuthorizationError):
            delete_role(999999)

    def test_delete_role_in_use(self, app):
        role = make_role("staff_role")

        make_user(
            "john",
            "john@example.com",
            role,
        )

        with pytest.raises(AuthorizationError):
            delete_role(role.id)

        assert db.session.get(Role, role.id) is not None


class TestPermissionAssignment:

    def test_assign_permission(self, app):
        role = make_role("writer")

        permission = make_permission(
            "articles.publish"
        )

        updated = assign_permission_to_role(
            role.id,
            permission.id,
        )

        assert permission in updated.permissions

    def test_assign_duplicate_permission(self, app):
        role = make_role("writer2")

        permission = make_permission(
            "articles.publish2"
        )

        assign_permission_to_role(
            role.id,
            permission.id,
        )

        with pytest.raises(AuthorizationError):
            assign_permission_to_role(
                role.id,
                permission.id,
            )

    def test_remove_permission(self, app):
        permission = make_permission(
            "articles.archive"
        )

        role = make_role(
            "archiver",
            [permission],
        )

        updated = remove_permission_from_role(
            role.id,
            permission.id,
        )

        assert permission not in updated.permissions

    def test_remove_missing_permission(self, app):
        role = make_role("empty")

        permission = make_permission(
            "unused.permission"
        )

        with pytest.raises(AuthorizationError):
            remove_permission_from_role(
                role.id,
                permission.id,
            )


class TestSetUserRole:

    def test_set_user_role_success(self, app):
        old_role = make_role("old_role")
        new_role = make_role("new_role")

        user = make_user(
            "amy",
            "amy@example.com",
            old_role,
        )

        updated = set_user_role(
            user.id,
            new_role.id,
        )

        assert updated.role_id == new_role.id

    def test_unknown_user(self, app):
        role = make_role("role1")

        with pytest.raises(UserNotFoundError):
            set_user_role(
                999999,
                role.id,
            )

    def test_unknown_role(self, app):
        role = make_role("role2")

        user = make_user(
            "bob",
            "bob@example.com",
            role,
        )

        with pytest.raises(AuthorizationError):
            set_user_role(
                user.id,
                999999,
            )


class TestHasPermission:

    def test_permission_true(self, app):
        permission = make_permission(
            "things.do"
        )

        role = make_role(
            "doer",
            [permission],
        )

        user = make_user(
            "alice",
            "alice@example.com",
            role,
        )

        assert has_permission(
            user,
            "things.do",
        ) is True

    def test_permission_false(self, app):
        role = make_role("empty_role")

        user = make_user(
            "charlie",
            "charlie@example.com",
            role,
        )

        assert has_permission(
            user,
            "things.do",
        ) is False

# ---------- validation schema tests ----------

class TestValidateRoleData:
    def test_valid_data_passes(self):
        result = validate_role_data({"name": "auditor", "description": "reads logs"})
        assert result == {"name": "auditor", "description": "reads logs"}

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_role_data({"description": "no name given"})
        assert "name" in exc_info.value.errors

    def test_unknown_field_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_role_data({"name": "x", "unexpected": "field"})
        assert "fields" in exc_info.value.errors


class TestValidateUserRoleData:
    def test_valid_role_id_passes(self):
        result = validate_user_role_data({"role_id": 3})
        assert result == {"role_id": 3}

    def test_non_integer_role_id_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_user_role_data({"role_id": "not-a-number"})
        assert "role_id" in exc_info.value.errors

    def test_negative_role_id_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_user_role_data({"role_id": -1})
        assert "role_id" in exc_info.value.errors


# ---------- persistence-error path ----------

# -------------------------------------------------
# Persistence Errors
# -------------------------------------------------

class TestPersistenceErrors:

    def test_create_role_wraps_db_failure(
        self,
        app,
        monkeypatch,
    ):
        from sqlalchemy.exc import SQLAlchemyError

        def explode():
            raise SQLAlchemyError("boom")

        monkeypatch.setattr(
            db.session,
            "commit",
            explode,
        )

        with pytest.raises(
            AuthorizationPersistenceError
        ):
            create_role(
                "failure_role",
                None,
            )


# -------------------------------------------------
# Basic Route Tests
# -------------------------------------------------

class TestRouteAccessControl:

    def test_requires_authentication(
        self,
        client,
    ):
        response = client.get(
            "/api/v1/authorization/roles"
        )

        assert response.status_code == 401