"""create audit logs table

Revision ID: 37db346198da
Revises: 6580667229c9
Create Date: 2026-07-27

"""

from alembic import op
import sqlalchemy as sa


revision = "37db346198da"
down_revision = "6580667229c9"
branch_labels = None
depends_on = None


def upgrade():

    op.create_table(
        "audit_logs",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            nullable=True
        ),
        sa.Column(
            "action",
            sa.String(length=255),
            nullable=False
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False
        ),
        sa.Column(
            "ip_address",
            sa.String(length=50),
            nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False
        ),
        sa.PrimaryKeyConstraint("id")
    )


def downgrade():

    op.drop_table("audit_logs")