"""add ai_chat_session_memory

Revision ID: o7p8q9r0s1t2
Revises: n6o7p8q9r0s1
Create Date: 2026-05-31 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "o7p8q9r0s1t2"
down_revision = "n6o7p8q9r0s1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ai_chat_session_memory",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("memory_type", sa.String(length=32), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("value_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("source_message_id", sa.UUID(), nullable=True),
        sa.Column("scope", sa.String(length=16), nullable=False, server_default="session"),
        sa.Column("confidence", sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["ai_chat_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_message_id"],
            ["ai_chat_messages.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ai_chat_session_memory_session_active",
        "ai_chat_session_memory",
        ["session_id", "active"],
        unique=False,
    )
    op.create_index(
        "ix_ai_chat_session_memory_session_type_key",
        "ai_chat_session_memory",
        ["session_id", "memory_type", "key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ai_chat_session_memory_source_message_id"),
        "ai_chat_session_memory",
        ["source_message_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_ai_chat_session_memory_source_message_id"),
        table_name="ai_chat_session_memory",
    )
    op.drop_index(
        "ix_ai_chat_session_memory_session_type_key",
        table_name="ai_chat_session_memory",
    )
    op.drop_index(
        "ix_ai_chat_session_memory_session_active",
        table_name="ai_chat_session_memory",
    )
    op.drop_table("ai_chat_session_memory")
