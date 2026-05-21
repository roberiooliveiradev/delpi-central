"""apps audit columns (created/updated by)

Revision ID: i5j6k7l8m9n0
Revises: h4i5j6k7l8m9
Create Date: 2026-05-21

"""

from alembic import op
import sqlalchemy as sa


revision = "i5j6k7l8m9n0"
down_revision = "h4i5j6k7l8m9"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "apps",
        sa.Column("created_by_user_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "apps",
        sa.Column("created_by_email", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "apps",
        sa.Column("updated_by_user_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "apps",
        sa.Column("updated_by_email", sa.String(length=255), nullable=True),
    )


def downgrade():
    op.drop_column("apps", "updated_by_email")
    op.drop_column("apps", "updated_by_user_id")
    op.drop_column("apps", "created_by_email")
    op.drop_column("apps", "created_by_user_id")
