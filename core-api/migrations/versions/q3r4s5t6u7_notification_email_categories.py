"""user notification preferences email categories

Revision ID: q3r4s5t6u7
Revises: p2q3r4s5t6
Create Date: 2026-08-17

"""

from alembic import op
import sqlalchemy as sa


revision = "q3r4s5t6u7"
down_revision = "p2q3r4s5t6"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user_notification_preferences") as batch_op:
        batch_op.add_column(
            sa.Column(
                "email_categories",
                sa.JSON(),
                nullable=False,
                server_default="[]",
            )
        )


def downgrade():
    with op.batch_alter_table("user_notification_preferences") as batch_op:
        batch_op.drop_column("email_categories")
