"""add admin guidelines

Revision ID: 8f1a2b3c4d5e
Revises: 7c8d9e0f1a23
Create Date: 2026-05-15 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "8f1a2b3c4d5e"
down_revision = "7c8d9e0f1a23"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ai_admin_guidelines",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("category", sa.String(length=40), nullable=False, server_default="behavior"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="draft"),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_by", sa.String(length=120), nullable=True),
        sa.Column("updated_by", sa.String(length=120), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_admin_guidelines_category", "ai_admin_guidelines", ["category"])
    op.create_index("ix_ai_admin_guidelines_status", "ai_admin_guidelines", ["status"])
    op.create_index("ix_ai_admin_guidelines_created_at", "ai_admin_guidelines", ["created_at"])
    op.create_index("ix_ai_admin_guidelines_created_by", "ai_admin_guidelines", ["created_by"])


def downgrade():
    op.drop_index("ix_ai_admin_guidelines_created_by", table_name="ai_admin_guidelines")
    op.drop_index("ix_ai_admin_guidelines_created_at", table_name="ai_admin_guidelines")
    op.drop_index("ix_ai_admin_guidelines_status", table_name="ai_admin_guidelines")
    op.drop_index("ix_ai_admin_guidelines_category", table_name="ai_admin_guidelines")
    op.drop_table("ai_admin_guidelines")
