"""Add RBAC models.

Revision ID: 5b03f5004cc0
Revises: 0174c045dcb9
Create Date: 2026-07-24 16:05:54.968662
"""

import sqlalchemy as sa
from alembic import op

revision = "5b03f5004cc0"
down_revision = "0174c045dcb9"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"]),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )

    roles = sa.table(
        "roles",
        sa.column("id", sa.Integer()),
        sa.column("name", sa.String(length=100)),
        sa.column("description", sa.String(length=255)),
    )
    connection = op.get_bind()
    connection.execute(
        roles.insert().values(
            name="Employee",
            description="Default role for new registrations",
        )
    )
    employee_role_id = connection.execute(
        sa.select(roles.c.id).where(roles.c.name == "Employee")
    ).scalar_one()

    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("role_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_users_role_id_roles",
            "roles",
            ["role_id"],
            ["id"],
        )

    users = sa.table(
        "users",
        sa.column("role_id", sa.Integer()),
    )
    connection.execute(
        users.update().where(users.c.role_id.is_(None)).values(role_id=employee_role_id)
    )

    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "role_id",
            existing_type=sa.Integer(),
            nullable=False,
        )


def downgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint(
            "fk_users_role_id_roles",
            type_="foreignkey",
        )
        batch_op.drop_column("role_id")

    op.drop_table("role_permissions")
    op.drop_table("roles")
    op.drop_table("permissions")
