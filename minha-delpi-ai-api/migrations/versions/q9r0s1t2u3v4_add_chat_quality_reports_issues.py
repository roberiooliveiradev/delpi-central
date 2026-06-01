"""add ai_chat_quality_reports and ai_chat_quality_issues

Revision ID: q9r0s1t2u3v4
Revises: p8q9r0s1t2u3
Create Date: 2026-06-01 14:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "q9r0s1t2u3v4"
down_revision = "p8q9r0s1t2u3"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ai_chat_quality_reports",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("report_type", sa.String(length=32), nullable=False, server_default="weekly"),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("summary_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("markdown", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ai_chat_quality_reports_created_at",
        "ai_chat_quality_reports",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_ai_chat_quality_reports_period",
        "ai_chat_quality_reports",
        ["period_start", "period_end"],
        unique=False,
    )

    op.create_table(
        "ai_chat_quality_issues",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=96), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="open"),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="feedback_auto"),
        sa.Column("issue_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("external_url", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ai_chat_quality_issues_code_status",
        "ai_chat_quality_issues",
        ["code", "status"],
        unique=False,
    )
    op.create_index(
        "ix_ai_chat_quality_issues_created_at",
        "ai_chat_quality_issues",
        ["created_at"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_ai_chat_quality_issues_created_at", table_name="ai_chat_quality_issues")
    op.drop_index("ix_ai_chat_quality_issues_code_status", table_name="ai_chat_quality_issues")
    op.drop_table("ai_chat_quality_issues")
    op.drop_index("ix_ai_chat_quality_reports_period", table_name="ai_chat_quality_reports")
    op.drop_index("ix_ai_chat_quality_reports_created_at", table_name="ai_chat_quality_reports")
    op.drop_table("ai_chat_quality_reports")
