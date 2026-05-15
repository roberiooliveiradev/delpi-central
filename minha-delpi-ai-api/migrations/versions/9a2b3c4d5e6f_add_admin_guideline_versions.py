"""add admin guideline versions

Revision ID: 9a2b3c4d5e6f
Revises: 8f1a2b3c4d5e
Create Date: 2026-05-15 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "9a2b3c4d5e6f"
down_revision = "8f1a2b3c4d5e"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ai_admin_guideline_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("guideline_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("category", sa.String(length=40), nullable=False, server_default="behavior"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="draft"),
        sa.Column("event", sa.String(length=40), nullable=False, server_default="saved"),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_by", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["guideline_id"],
            ["ai_admin_guidelines.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "guideline_id",
            "version",
            name="uq_ai_admin_guideline_versions_guideline_version",
        ),
    )
    op.create_index(
        "ix_ai_admin_guideline_versions_guideline_id",
        "ai_admin_guideline_versions",
        ["guideline_id"],
    )
    op.create_index(
        "ix_ai_admin_guideline_versions_event",
        "ai_admin_guideline_versions",
        ["event"],
    )
    op.create_index(
        "ix_ai_admin_guideline_versions_created_by",
        "ai_admin_guideline_versions",
        ["created_by"],
    )
    op.create_index(
        "ix_ai_admin_guideline_versions_created_at",
        "ai_admin_guideline_versions",
        ["created_at"],
    )


def downgrade():
    op.drop_index("ix_ai_admin_guideline_versions_created_at", table_name="ai_admin_guideline_versions")
    op.drop_index("ix_ai_admin_guideline_versions_created_by", table_name="ai_admin_guideline_versions")
    op.drop_index("ix_ai_admin_guideline_versions_event", table_name="ai_admin_guideline_versions")
    op.drop_index("ix_ai_admin_guideline_versions_guideline_id", table_name="ai_admin_guideline_versions")
    op.drop_table("ai_admin_guideline_versions")
