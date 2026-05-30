"""app_usage_events caller_app_id

Revision ID: m9n0o1p2q3
Revises: l8m9n0o1p2
Create Date: 2026-05-29

"""

from alembic import op
import sqlalchemy as sa


revision = "m9n0o1p2q3"
down_revision = "l8m9n0o1p2"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "app_usage_events",
        sa.Column("caller_app_id", sa.String(length=50), nullable=True),
    )
    op.create_foreign_key(
        "fk_app_usage_events_caller_app_id",
        "app_usage_events",
        "apps",
        ["caller_app_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_app_usage_events_caller_app_id",
        "app_usage_events",
        ["caller_app_id"],
    )


def downgrade():
    op.drop_index("ix_app_usage_events_caller_app_id", table_name="app_usage_events")
    op.drop_constraint(
        "fk_app_usage_events_caller_app_id",
        "app_usage_events",
        type_="foreignkey",
    )
    op.drop_column("app_usage_events", "caller_app_id")
