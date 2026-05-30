"""add message tree branches and active leaf per session

Revision ID: m5n6o7p8q9r0
Revises: l3m4n5o6p7q8
Create Date: 2026-05-30 21:30:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "m5n6o7p8q9r0"
down_revision = "l3m4n5o6p7q8"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "ai_chat_messages",
        sa.Column("parent_message_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        op.f("ix_ai_chat_messages_parent_message_id"),
        "ai_chat_messages",
        ["parent_message_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_ai_chat_messages_parent_message_id",
        "ai_chat_messages",
        "ai_chat_messages",
        ["parent_message_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column(
        "ai_chat_sessions",
        sa.Column("active_leaf_message_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        op.f("ix_ai_chat_sessions_active_leaf_message_id"),
        "ai_chat_sessions",
        ["active_leaf_message_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_ai_chat_sessions_active_leaf_message_id",
        "ai_chat_sessions",
        "ai_chat_messages",
        ["active_leaf_message_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.execute(
        """
        WITH ordered AS (
            SELECT
                id,
                LAG(id) OVER (
                    PARTITION BY session_id
                    ORDER BY created_at ASC, id ASC
                ) AS prev_id
            FROM ai_chat_messages
        )
        UPDATE ai_chat_messages AS m
        SET parent_message_id = ordered.prev_id
        FROM ordered
        WHERE m.id = ordered.id
          AND ordered.prev_id IS NOT NULL
        """
    )

    op.execute(
        """
        UPDATE ai_chat_sessions AS s
        SET active_leaf_message_id = latest.message_id
        FROM (
            SELECT DISTINCT ON (session_id)
                session_id,
                id AS message_id
            FROM ai_chat_messages
            ORDER BY session_id, created_at DESC, id DESC
        ) AS latest
        WHERE s.id = latest.session_id
        """
    )


def downgrade():
    op.drop_constraint(
        "fk_ai_chat_sessions_active_leaf_message_id",
        "ai_chat_sessions",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_ai_chat_sessions_active_leaf_message_id"),
        table_name="ai_chat_sessions",
    )
    op.drop_column("ai_chat_sessions", "active_leaf_message_id")

    op.drop_constraint(
        "fk_ai_chat_messages_parent_message_id",
        "ai_chat_messages",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_ai_chat_messages_parent_message_id"),
        table_name="ai_chat_messages",
    )
    op.drop_column("ai_chat_messages", "parent_message_id")
