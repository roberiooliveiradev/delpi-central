"""user notification preferences important categories

Revision ID: p2q3r4s5t6
Revises: o1p2q3r4s5
Create Date: 2026-08-17

"""

from alembic import op
import sqlalchemy as sa


revision = "p2q3r4s5t6"
down_revision = "o1p2q3r4s5"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user_notification_preferences") as batch_op:
        batch_op.add_column(
            sa.Column(
                "important_categories",
                sa.JSON(),
                nullable=False,
                server_default="[]",
            )
        )


def downgrade():
    with op.batch_alter_table("user_notification_preferences") as batch_op:
        batch_op.drop_column("important_categories")
