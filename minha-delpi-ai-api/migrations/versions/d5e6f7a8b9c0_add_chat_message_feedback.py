"""add chat message feedback

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-05-18 14:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "d5e6f7a8b9c0"
down_revision = "c4d5e6f7a8b9"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ai_chat_message_feedback",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rating", sa.SmallInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["ai_chat_messages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("message_id", "user_id", name="uq_ai_chat_message_feedback_message_user"),
    )
    op.create_index(
        "ix_ai_chat_message_feedback_message_id",
        "ai_chat_message_feedback",
        ["message_id"],
    )
    op.create_index(
        "ix_ai_chat_message_feedback_user_id",
        "ai_chat_message_feedback",
        ["user_id"],
    )


def downgrade():
    op.drop_index("ix_ai_chat_message_feedback_user_id", table_name="ai_chat_message_feedback")
    op.drop_index("ix_ai_chat_message_feedback_message_id", table_name="ai_chat_message_feedback")
    op.drop_table("ai_chat_message_feedback")
