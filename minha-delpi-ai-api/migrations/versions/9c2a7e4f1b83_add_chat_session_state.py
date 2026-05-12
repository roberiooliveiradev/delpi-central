"""add chat session state

Revision ID: 9c2a7e4f1b83
Revises: 74b8f9c6e2a1
Create Date: 2026-05-12 13:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "9c2a7e4f1b83"
down_revision = "74b8f9c6e2a1"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("ai_chat_sessions", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "is_pinned",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            )
        )
        batch_op.add_column(
            sa.Column(
                "pinned_at",
                sa.DateTime(timezone=True),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "archived_at",
                sa.DateTime(timezone=True),
                nullable=True,
            )
        )

        batch_op.create_index(
            batch_op.f("ix_ai_chat_sessions_is_pinned"),
            ["is_pinned"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_ai_chat_sessions_archived_at"),
            ["archived_at"],
            unique=False,
        )
        batch_op.create_index(
            "idx_ai_chat_sessions_user_archived_updated",
            ["user_id", "archived_at", "updated_at"],
            unique=False,
        )
        batch_op.create_index(
            "idx_ai_chat_sessions_user_pinned_updated",
            ["user_id", "is_pinned", "pinned_at", "updated_at"],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table("ai_chat_sessions", schema=None) as batch_op:
        batch_op.drop_index("idx_ai_chat_sessions_user_pinned_updated")
        batch_op.drop_index("idx_ai_chat_sessions_user_archived_updated")
        batch_op.drop_index(batch_op.f("ix_ai_chat_sessions_archived_at"))
        batch_op.drop_index(batch_op.f("ix_ai_chat_sessions_is_pinned"))

        batch_op.drop_column("archived_at")
        batch_op.drop_column("pinned_at")
        batch_op.drop_column("is_pinned")
