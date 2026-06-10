"""user portal tour progress and quest events

Revision ID: n0o1p2q3r4
Revises: m9n0o1p2q3
Create Date: 2026-06-10

"""

from alembic import op
import sqlalchemy as sa


revision = "n0o1p2q3r4"
down_revision = "m9n0o1p2q3"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_portal_tour_progress",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("tour_version", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="exploring"),
        sa.Column("completed_quest_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column(
            "started_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "last_activity_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_index(
        "ix_user_portal_tour_progress_tour_version",
        "user_portal_tour_progress",
        ["tour_version"],
    )
    op.create_index(
        "ix_user_portal_tour_progress_status",
        "user_portal_tour_progress",
        ["status"],
    )
    op.create_index(
        "ix_user_portal_tour_progress_last_activity_at",
        "user_portal_tour_progress",
        ["last_activity_at"],
    )

    op.create_table(
        "portal_tour_quest_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("tour_version", sa.String(length=80), nullable=False),
        sa.Column("quest_id", sa.String(length=80), nullable=False),
        sa.Column(
            "completed_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "tour_version",
            "quest_id",
            name="uq_portal_tour_quest_events_user_version_quest",
        ),
    )
    op.create_index(
        "ix_portal_tour_quest_events_user_id",
        "portal_tour_quest_events",
        ["user_id"],
    )
    op.create_index(
        "ix_portal_tour_quest_events_tour_version",
        "portal_tour_quest_events",
        ["tour_version"],
    )
    op.create_index(
        "ix_portal_tour_quest_events_completed_at",
        "portal_tour_quest_events",
        ["completed_at"],
    )


def downgrade():
    op.drop_index("ix_portal_tour_quest_events_completed_at", table_name="portal_tour_quest_events")
    op.drop_index("ix_portal_tour_quest_events_tour_version", table_name="portal_tour_quest_events")
    op.drop_index("ix_portal_tour_quest_events_user_id", table_name="portal_tour_quest_events")
    op.drop_table("portal_tour_quest_events")

    op.drop_index("ix_user_portal_tour_progress_last_activity_at", table_name="user_portal_tour_progress")
    op.drop_index("ix_user_portal_tour_progress_status", table_name="user_portal_tour_progress")
    op.drop_index("ix_user_portal_tour_progress_tour_version", table_name="user_portal_tour_progress")
    op.drop_table("user_portal_tour_progress")
