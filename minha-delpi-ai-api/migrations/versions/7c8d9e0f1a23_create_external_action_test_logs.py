"""create external action test logs

Revision ID: 7c8d9e0f1a23
Revises: 6b7c8d9e0f12
Create Date: 2026-05-13
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "7c8d9e0f1a23"
down_revision = "6b7c8d9e0f12"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ai_external_action_test_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.String(length=120), nullable=False, index=True),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("provider_key", sa.String(length=120), nullable=False, index=True),
        sa.Column("action_id", sa.String(length=220), nullable=False, index=True),
        sa.Column("method", sa.String(length=10), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("request_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("ok", sa.Boolean(), nullable=False, server_default=sa.text("false"), index=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("response_preview", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), index=True),
    )


def downgrade():
    op.drop_table("ai_external_action_test_logs")
