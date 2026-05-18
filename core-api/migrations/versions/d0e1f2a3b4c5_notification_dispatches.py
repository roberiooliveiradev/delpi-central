"""notification dispatches audit and scheduling

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-05-18

"""

from alembic import op
import sqlalchemy as sa


revision = "d0e1f2a3b4c5"
down_revision = "c9d0e1f2a3b4"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "notification_dispatches",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_by_user_id", sa.UUID(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("scheduled_at", sa.DateTime(), nullable=True),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("broadcast", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("recipient_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("title", sa.String(length=120), nullable=True),
        sa.Column("category", sa.String(length=40), nullable=False, server_default="system"),
        sa.Column("presentation", sa.String(length=20), nullable=False, server_default="text"),
        sa.Column("template_id", sa.String(length=80), nullable=True),
        sa.Column("source_app", sa.String(length=80), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("notification_ids", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_notification_dispatches_status",
        "notification_dispatches",
        ["status"],
    )
    op.create_index(
        "ix_notification_dispatches_scheduled_at",
        "notification_dispatches",
        ["scheduled_at"],
    )
    op.create_index(
        "ix_notification_dispatches_created_at",
        "notification_dispatches",
        ["created_at"],
    )
    op.create_index(
        "ix_notification_dispatches_created_by_user_id",
        "notification_dispatches",
        ["created_by_user_id"],
    )


def downgrade():
    op.drop_index("ix_notification_dispatches_created_by_user_id", "notification_dispatches")
    op.drop_index("ix_notification_dispatches_created_at", "notification_dispatches")
    op.drop_index("ix_notification_dispatches_scheduled_at", "notification_dispatches")
    op.drop_index("ix_notification_dispatches_status", "notification_dispatches")
    op.drop_table("notification_dispatches")
