"""add is_suspended to users"""

from alembic import op
import sqlalchemy as sa


revision = "6580667229c9"
down_revision = "5b03f5004cc0"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(
            sa.Column(
                "is_suspended",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false")
            )
        )


def downgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("is_suspended")