"""add action_display_label_cache

Runtime cache of LLM-localized external action display labels.
Separate from presentation_field_label_cache (column headers).

Revision ID: y7z8a9b0c1d2
Revises: x6y7z8a9b0c1
Create Date: 2026-09-10 00:40:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "y7z8a9b0c1d2"
down_revision = "x6y7z8a9b0c1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "action_display_label_cache",
        sa.Column("cache_key", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=240), nullable=False),
        sa.Column(
            "source",
            sa.String(length=48),
            nullable=False,
            server_default="LLM_LOCALIZATION",
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("cache_key"),
    )


def downgrade():
    op.drop_table("action_display_label_cache")
