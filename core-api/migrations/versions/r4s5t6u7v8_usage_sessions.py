"""usage_sessions for engagement duration tracking

Revision ID: r4s5t6u7v8
Revises: q3r4s5t6u7
Create Date: 2026-08-24

"""

from alembic import op
import sqlalchemy as sa


revision = "r4s5t6u7v8"
down_revision = "q3r4s5t6u7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "usage_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("app_id", sa.String(length=50), nullable=True),
        sa.Column("route_path", sa.String(length=255), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("socket_session_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["app_id"], ["apps.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_usage_sessions_user_id", "usage_sessions", ["user_id"])
    op.create_index("ix_usage_sessions_app_id", "usage_sessions", ["app_id"])
    op.create_index("ix_usage_sessions_started_at", "usage_sessions", ["started_at"])
    op.create_index(
        "ix_usage_sessions_user_started",
        "usage_sessions",
        ["user_id", "started_at"],
    )


def downgrade():
    op.drop_index("ix_usage_sessions_user_started", table_name="usage_sessions")
    op.drop_index("ix_usage_sessions_started_at", table_name="usage_sessions")
    op.drop_index("ix_usage_sessions_app_id", table_name="usage_sessions")
    op.drop_index("ix_usage_sessions_user_id", table_name="usage_sessions")
    op.drop_table("usage_sessions")
