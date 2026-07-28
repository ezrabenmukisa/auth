"""Tests for the complete Alembic migration chain."""

from datetime import datetime, timezone

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
    "role_id",
    "is_suspended",
}

EXPECTED_REVOKED_TOKEN_COLUMNS = {
    "id",
    "session_id",
    "expires_at",
    "revoked_at",
}


def _reset_schema(app):
    with app.app_context():
        db.drop_all()


def test_migrations_create_complete_schema(app):
    _reset_schema(app)

    result = app.test_cli_runner().invoke(args=["db", "upgrade"])

    assert result.exit_code == 0, result.output

    with app.app_context():
        inspector = sa.inspect(db.engine)
        table_names = set(inspector.get_table_names())
        user_columns = {column["name"] for column in inspector.get_columns("users")}
        revoked_token_columns = {
            column["name"] for column in inspector.get_columns("revoked_tokens")
        }
        role_id_column = next(
            column
            for column in inspector.get_columns("users")
            if column["name"] == "role_id"
        )
        revoked_token_indexes = inspector.get_indexes("revoked_tokens")
        revoked_token_unique_constraints = inspector.get_unique_constraints(
            "revoked_tokens"
        )

    assert table_names == {
    "alembic_version",
    "permissions",
    "revoked_tokens",
    "role_permissions",
    "roles",
    "users",
    "audit_logs",
}
    
    assert user_columns == EXPECTED_USER_COLUMNS
    assert role_id_column["nullable"] is False
    assert revoked_token_columns == EXPECTED_REVOKED_TOKEN_COLUMNS
    assert any(
        index["column_names"] == ["session_id"] and index["unique"]
        for index in revoked_token_indexes
    ) or any(
        constraint["column_names"] == ["session_id"]
        for constraint in revoked_token_unique_constraints
    )


def test_rbac_migration_backfills_existing_users(app):
    _reset_schema(app)
    runner = app.test_cli_runner()
    base_result = runner.invoke(args=["db", "upgrade", "0174c045dcb9"])
    assert base_result.exit_code == 0, base_result.output

    now = datetime.now(timezone.utc).isoformat()
    with app.app_context():
        db.session.execute(
            sa.text("""
                INSERT INTO users (
                    username, email, password_hash, full_name,
                    is_active, created_at, updated_at
                ) VALUES (
                    :username, :email, :password_hash, :full_name,
                    :is_active, :created_at, :updated_at
                )
                """),
            {
                "username": "existing-user",
                "email": "existing@example.com",
                "password_hash": "existing-hash",
                "full_name": "Existing User",
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            },
        )
        db.session.commit()

    upgrade_result = runner.invoke(args=["db", "upgrade"])
    assert upgrade_result.exit_code == 0, upgrade_result.output

    with app.app_context():
        assigned_role = db.session.execute(
            sa.text("""
                SELECT roles.name
                FROM users
                JOIN roles ON roles.id = users.role_id
                WHERE users.username = :username
                """),
            {"username": "existing-user"},
        ).scalar_one()

    assert assigned_role == "Employee"
