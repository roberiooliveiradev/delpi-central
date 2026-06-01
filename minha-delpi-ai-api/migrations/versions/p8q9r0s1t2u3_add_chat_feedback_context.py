"""add context_metadata and comment to ai_chat_message_feedback

Revision ID: p8q9r0s1t2u3
Revises: o7p8q9r0s1t2
Create Date: 2026-06-01 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "p8q9r0s1t2u3"
down_revision = "o7p8q9r0s1t2"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "ai_chat_message_feedback",
        sa.Column("comment", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "ai_chat_message_feedback",
        sa.Column(
            "context_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_ai_chat_message_feedback_created_at",
        "ai_chat_message_feedback",
        ["created_at"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_ai_chat_message_feedback_created_at",
        table_name="ai_chat_message_feedback",
    )
    op.drop_column("ai_chat_message_feedback", "context_metadata")
    op.drop_column("ai_chat_message_feedback", "comment")
