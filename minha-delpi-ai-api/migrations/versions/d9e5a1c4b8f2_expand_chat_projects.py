"""expand chat projects

Revision ID: d9e5a1c4b8f2
Revises: c7a9e3b2f4d6
Create Date: 2026-05-12 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "d9e5a1c4b8f2"
down_revision = "c7a9e3b2f4d6"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("ai_chat_projects", schema=None) as batch_op:
        batch_op.add_column(sa.Column("instructions", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("default_agent_key", sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column("visibility", sa.String(length=20), nullable=False, server_default="private"))
        batch_op.add_column(sa.Column("icon", sa.String(length=60), nullable=True))
        batch_op.add_column(sa.Column("color", sa.String(length=40), nullable=True))
        batch_op.add_column(sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True))

        batch_op.create_index("idx_ai_chat_projects_user_archived_updated", ["user_id", "archived_at", "updated_at"], unique=False)
        batch_op.create_index("idx_ai_chat_projects_visibility", ["visibility"], unique=False)
        batch_op.create_index("ix_ai_chat_projects_default_agent_key", ["default_agent_key"], unique=False)

    op.create_table(
        "ai_chat_project_shares",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="viewer"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["project_id"], ["ai_chat_projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "target_user_id", name="uq_ai_chat_project_shares_project_user"),
    )

    op.create_index(
        "idx_ai_chat_project_shares_target",
        "ai_chat_project_shares",
        ["target_user_id", "project_id"],
        unique=False,
    )


def downgrade():
    op.drop_index("idx_ai_chat_project_shares_target", table_name="ai_chat_project_shares")
    op.drop_table("ai_chat_project_shares")

    with op.batch_alter_table("ai_chat_projects", schema=None) as batch_op:
        batch_op.drop_index("ix_ai_chat_projects_default_agent_key")
        batch_op.drop_index("idx_ai_chat_projects_visibility")
        batch_op.drop_index("idx_ai_chat_projects_user_archived_updated")
        batch_op.drop_column("metadata")
        batch_op.drop_column("archived_at")
        batch_op.drop_column("color")
        batch_op.drop_column("icon")
        batch_op.drop_column("visibility")
        batch_op.drop_column("default_agent_key")
        batch_op.drop_column("instructions")
