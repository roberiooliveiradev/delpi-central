"""app_usage_events for plugin usage tracking

Revision ID: h4i5j6k7l8m9
Revises: g3b4c5d6e7f8
Create Date: 2026-05-19

"""

from alembic import op
import sqlalchemy as sa


revision = "h4i5j6k7l8m9"
down_revision = "g3b4c5d6e7f8"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "app_usage_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("app_id", sa.String(length=50), nullable=False),
        sa.Column("route_path", sa.String(length=255), nullable=True),
        sa.Column("opened_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["app_id"], ["apps.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_app_usage_events_user_id",
        "app_usage_events",
        ["user_id"],
    )
    op.create_index(
        "ix_app_usage_events_app_id",
        "app_usage_events",
        ["app_id"],
    )
    op.create_index(
        "ix_app_usage_events_opened_at",
        "app_usage_events",
        ["opened_at"],
    )
    op.create_index(
        "ix_app_usage_events_user_app_opened",
        "app_usage_events",
        ["user_id", "app_id", "opened_at"],
    )


def downgrade():
    op.drop_index("ix_app_usage_events_user_app_opened", table_name="app_usage_events")
    op.drop_index("ix_app_usage_events_opened_at", table_name="app_usage_events")
    op.drop_index("ix_app_usage_events_app_id", table_name="app_usage_events")
    op.drop_index("ix_app_usage_events_user_id", table_name="app_usage_events")
    op.drop_table("app_usage_events")
