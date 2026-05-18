"""enrich notifications rich content

Revision ID: b8c9d0e1f2a3
Revises: 7aa51b680332
Create Date: 2026-05-18

"""

from alembic import op
import sqlalchemy as sa


revision = "b8c9d0e1f2a3"
down_revision = "7aa51b680332"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("notifications", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("category", sa.String(length=40), nullable=False, server_default="system")
        )
        batch_op.add_column(
            sa.Column("presentation", sa.String(length=20), nullable=False, server_default="text")
        )
        batch_op.add_column(sa.Column("html_content", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("action_type", sa.String(length=30), nullable=True))
        batch_op.add_column(sa.Column("action_label", sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column("action_target", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("icon", sa.String(length=40), nullable=True))
        batch_op.add_column(sa.Column("metadata", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("expires_at", sa.DateTime(), nullable=True))

    op.execute("UPDATE notifications SET category = 'system' WHERE category IS NULL")
    op.execute("UPDATE notifications SET presentation = 'text' WHERE presentation IS NULL")


def downgrade():
    with op.batch_alter_table("notifications", schema=None) as batch_op:
        batch_op.drop_column("expires_at")
        batch_op.drop_column("metadata")
        batch_op.drop_column("icon")
        batch_op.drop_column("action_target")
        batch_op.drop_column("action_label")
        batch_op.drop_column("action_type")
        batch_op.drop_column("html_content")
        batch_op.drop_column("presentation")
        batch_op.drop_column("category")
