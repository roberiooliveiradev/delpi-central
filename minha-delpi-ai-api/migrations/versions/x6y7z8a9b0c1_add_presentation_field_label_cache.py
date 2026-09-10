"""add presentation_field_label_cache

Runtime cache of LLM-generated table header labels. Not an editable catalog.

Revision ID: x6y7z8a9b0c1
Revises: w5x6y7z8a9b0
Create Date: 2026-09-09 21:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "x6y7z8a9b0c1"
down_revision = "w5x6y7z8a9b0"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "presentation_field_label_cache",
        sa.Column("field_key", sa.String(length=160), nullable=False),
        sa.Column("label", sa.String(length=160), nullable=False),
        sa.Column(
            "source",
            sa.String(length=48),
            nullable=False,
            server_default="LLM_LOCALIZATION",
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("field_key"),
    )


def downgrade():
    op.drop_table("presentation_field_label_cache")
