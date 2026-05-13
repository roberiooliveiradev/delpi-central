"""create chat attachments

Revision ID: d1e2f3a4b5c6
Revises: c7a9e3b2f4d6
Create Date: 2026-05-13 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "d1e2f3a4b5c6"
down_revision = "c7a9e3b2f4d6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ai_chat_attachments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("agent_key", sa.String(length=80), nullable=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=160), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("storage_path", sa.String(length=600), nullable=False),
        sa.Column("status", sa.String(length=40), server_default="uploaded", nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["ai_chat_messages.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["ai_chat_projects.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["session_id"], ["ai_chat_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_ai_chat_attachments_user_id", "ai_chat_attachments", ["user_id"])
    op.create_index("ix_ai_chat_attachments_session_id", "ai_chat_attachments", ["session_id"])
    op.create_index("ix_ai_chat_attachments_message_id", "ai_chat_attachments", ["message_id"])
    op.create_index("ix_ai_chat_attachments_project_id", "ai_chat_attachments", ["project_id"])
    op.create_index("ix_ai_chat_attachments_agent_key", "ai_chat_attachments", ["agent_key"])
    op.create_index("ix_ai_chat_attachments_status", "ai_chat_attachments", ["status"])
    op.create_index("ix_ai_chat_attachments_created_at", "ai_chat_attachments", ["created_at"])


def downgrade():
    op.drop_index("ix_ai_chat_attachments_created_at", table_name="ai_chat_attachments")
    op.drop_index("ix_ai_chat_attachments_status", table_name="ai_chat_attachments")
    op.drop_index("ix_ai_chat_attachments_agent_key", table_name="ai_chat_attachments")
    op.drop_index("ix_ai_chat_attachments_project_id", table_name="ai_chat_attachments")
    op.drop_index("ix_ai_chat_attachments_message_id", table_name="ai_chat_attachments")
    op.drop_index("ix_ai_chat_attachments_session_id", table_name="ai_chat_attachments")
    op.drop_index("ix_ai_chat_attachments_user_id", table_name="ai_chat_attachments")
    op.drop_table("ai_chat_attachments")
