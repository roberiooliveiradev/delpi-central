"""add delpi_metadata to external actions

Revision ID: w5x6y7z8a9b0
Revises: v4w5x6y7z8a9
Create Date: 2026-06-22 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "w5x6y7z8a9b0"
down_revision = "v4w5x6y7z8a9"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("ai_external_actions", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "delpi_metadata",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
            )
        )


def downgrade():
    with op.batch_alter_table("ai_external_actions", schema=None) as batch_op:
        batch_op.drop_column("delpi_metadata")
