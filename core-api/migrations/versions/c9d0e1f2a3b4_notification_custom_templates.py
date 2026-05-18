"""notification custom templates

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-05-18

"""

from alembic import op
import sqlalchemy as sa


revision = "c9d0e1f2a3b4"
down_revision = "b8c9d0e1f2a3"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "notification_custom_templates",
        sa.Column("id", sa.String(length=80), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("category", sa.String(length=40), nullable=False, server_default="custom"),
        sa.Column("default_type", sa.String(length=20), nullable=False, server_default="info"),
        sa.Column("title_template", sa.String(length=120), nullable=False),
        sa.Column("message_template", sa.String(length=500), nullable=False),
        sa.Column("layout", sa.JSON(), nullable=True),
        sa.Column("required_vars", sa.JSON(), nullable=False),
        sa.Column("optional_vars", sa.JSON(), nullable=False),
        sa.Column("recipient_vars", sa.JSON(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("notification_custom_templates")
