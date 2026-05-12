"""add chat artifacts

Revision ID: a1f4c9d8e2b7
Revises: 9c2a7e4f1b83
Create Date: 2026-05-12 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "a1f4c9d8e2b7"
down_revision = "9c2a7e4f1b83"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ai_chat_artifacts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "message_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("type", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["message_id"],
            ["ai_chat_messages.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["ai_chat_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "idx_ai_chat_artifacts_session_updated",
        "ai_chat_artifacts",
        ["session_id", "updated_at"],
        unique=False,
    )
    op.create_index(
        "idx_ai_chat_artifacts_user_updated",
        "ai_chat_artifacts",
        ["user_id", "updated_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ai_chat_artifacts_type"),
        "ai_chat_artifacts",
        ["type"],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix_ai_chat_artifacts_type"), table_name="ai_chat_artifacts")
    op.drop_index("idx_ai_chat_artifacts_user_updated", table_name="ai_chat_artifacts")
    op.drop_index("idx_ai_chat_artifacts_session_updated", table_name="ai_chat_artifacts")
    op.drop_table("ai_chat_artifacts")
