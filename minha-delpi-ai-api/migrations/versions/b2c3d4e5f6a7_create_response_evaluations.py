"""create response evaluations

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-18 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ai_response_evaluations",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("evaluator_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("verdict", sa.String(length=20), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("suggestions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("evaluation_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["ai_chat_messages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["ai_chat_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("message_id", name="uq_ai_response_evaluations_message_id"),
    )

    op.create_index(
        "ix_ai_response_evaluations_session_id",
        "ai_response_evaluations",
        ["session_id"],
    )
    op.create_index(
        "ix_ai_response_evaluations_evaluator_user_id",
        "ai_response_evaluations",
        ["evaluator_user_id"],
    )
    op.create_index(
        "ix_ai_response_evaluations_verdict",
        "ai_response_evaluations",
        ["verdict"],
    )
    op.create_index(
        "ix_ai_response_evaluations_created_at",
        "ai_response_evaluations",
        ["created_at"],
    )


def downgrade():
    op.drop_index("ix_ai_response_evaluations_created_at", table_name="ai_response_evaluations")
    op.drop_index("ix_ai_response_evaluations_verdict", table_name="ai_response_evaluations")
    op.drop_index(
        "ix_ai_response_evaluations_evaluator_user_id",
        table_name="ai_response_evaluations",
    )
    op.drop_index("ix_ai_response_evaluations_session_id", table_name="ai_response_evaluations")
    op.drop_table("ai_response_evaluations")
