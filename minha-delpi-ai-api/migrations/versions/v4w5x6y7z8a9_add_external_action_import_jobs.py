"""add external action import jobs

Revision ID: v4w5x6y7z8a9
Revises: u3v4w5x6y7z8
Create Date: 2026-06-12 00:30:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "v4w5x6y7z8a9"
down_revision = "u3v4w5x6y7z8"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ai_external_action_import_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider_key", sa.String(length=120), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("phase", sa.String(length=40), nullable=False),
        sa.Column("progress_done", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("progress_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ai_external_action_import_jobs_provider_key",
        "ai_external_action_import_jobs",
        ["provider_key"],
    )
    op.create_index(
        "ix_ai_external_action_import_jobs_status",
        "ai_external_action_import_jobs",
        ["status"],
    )


def downgrade():
    op.drop_index("ix_ai_external_action_import_jobs_status", table_name="ai_external_action_import_jobs")
    op.drop_index(
        "ix_ai_external_action_import_jobs_provider_key",
        table_name="ai_external_action_import_jobs",
    )
    op.drop_table("ai_external_action_import_jobs")
