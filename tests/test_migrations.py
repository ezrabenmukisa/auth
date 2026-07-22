"""Tests that Alembic migrations produce the expected user schema."""

import sqlalchemy as sa

from app.extensions import db


EXPECTED_USER_COLUMNS = {
    "id",
    "username",
    "email",
    "password_hash",
    "full_name",
    "is_active",
    "created_at",
    "updated_at",
}


def test_migration_creates_only_user_management_schema(app):
    with app.app_context():
        db.drop_all()

    result = app.test_cli_runner().invoke(args=["db", "upgrade"])

    assert result.exit_code == 0, result.output

    with app.app_context():
        inspector = sa.inspect(db.engine)
        table_names = set(inspector.get_table_names())
        user_columns = {
            column["name"] for column in inspector.get_columns("users")
        }

    assert table_names == {"alembic_version", "users"}
    assert user_columns == EXPECTED_USER_COLUMNS
