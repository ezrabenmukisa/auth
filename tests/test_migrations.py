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

EXPECTED_REVOKED_TOKEN_COLUMNS = {
    "id",
    "session_id",
    "expires_at",
    "revoked_at",
}


def test_migrations_create_authentication_schema(app):
    with app.app_context():
        db.drop_all()

    result = app.test_cli_runner().invoke(args=["db", "upgrade"])

    assert result.exit_code == 0, result.output

    with app.app_context():
        inspector = sa.inspect(db.engine)
        table_names = set(inspector.get_table_names())
        user_columns = {column["name"] for column in inspector.get_columns("users")}
        revoked_token_columns = {
            column["name"] for column in inspector.get_columns("revoked_tokens")
        }
        revoked_token_indexes = inspector.get_indexes("revoked_tokens")
        revoked_token_unique_constraints = inspector.get_unique_constraints(
            "revoked_tokens"
        )

    assert table_names == {"alembic_version", "revoked_tokens", "users"}
    assert user_columns == EXPECTED_USER_COLUMNS
    assert revoked_token_columns == EXPECTED_REVOKED_TOKEN_COLUMNS
    assert any(
        index["column_names"] == ["session_id"] and index["unique"]
        for index in revoked_token_indexes
    ) or any(
        constraint["column_names"] == ["session_id"]
        for constraint in revoked_token_unique_constraints
    )
