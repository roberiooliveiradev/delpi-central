"""add guideline environment

Revision ID: a1b2c3d4e5f6
Revises: 9a2b3c4d5e6f
Create Date: 2026-05-15 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "a1b2c3d4e5f6"
down_revision = "9a2b3c4d5e6f"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "ai_admin_guidelines",
        sa.Column("environment", sa.String(length=30), nullable=False, server_default="global"),
    )
    op.add_column(
        "ai_admin_guideline_versions",
        sa.Column("environment", sa.String(length=30), nullable=False, server_default="global"),
    )

    op.create_index(
        "ix_ai_admin_guidelines_environment",
        "ai_admin_guidelines",
        ["environment"],
    )

    op.alter_column("ai_admin_guidelines", "environment", server_default=None)
    op.alter_column("ai_admin_guideline_versions", "environment", server_default=None)


def downgrade():
    op.drop_index("ix_ai_admin_guidelines_environment", table_name="ai_admin_guidelines")
    op.drop_column("ai_admin_guideline_versions", "environment")
    op.drop_column("ai_admin_guidelines", "environment")
