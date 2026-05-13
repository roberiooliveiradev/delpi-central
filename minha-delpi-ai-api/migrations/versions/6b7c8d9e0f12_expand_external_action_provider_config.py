"""expand external action provider config

Revision ID: 6b7c8d9e0f12
Revises: 554d6a5aeff4
Create Date: 2026-05-13
"""

from alembic import op
import sqlalchemy as sa


revision = "6b7c8d9e0f12"
down_revision = "554d6a5aeff4"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "ai_external_action_providers",
        sa.Column("privacy_policy_url", sa.Text(), nullable=True),
    )


def downgrade():
    op.drop_column("ai_external_action_providers", "privacy_policy_url")
