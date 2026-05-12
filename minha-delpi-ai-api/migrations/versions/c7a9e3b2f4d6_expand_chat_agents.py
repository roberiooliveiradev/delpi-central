"""expand chat agents

Revision ID: c7a9e3b2f4d6
Revises: b8d2f6c3a9e1
Create Date: 2026-05-12 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "c7a9e3b2f4d6"
down_revision = "b8d2f6c3a9e1"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("ai_chat_agents", schema=None) as batch_op:
        batch_op.add_column(sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=True))
        batch_op.add_column(sa.Column("visibility", sa.String(length=20), nullable=False, server_default="system"))
        batch_op.add_column(sa.Column("category", sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column("icon", sa.String(length=60), nullable=True))
        batch_op.add_column(sa.Column("response_style", sa.String(length=40), nullable=True))
        batch_op.add_column(sa.Column("max_tool_calls", sa.Integer(), nullable=False, server_default="5"))
        batch_op.add_column(sa.Column("requires_confirmation_for_write", sa.Boolean(), nullable=False, server_default=sa.text("true")))

        batch_op.create_index("idx_ai_chat_agents_owner_updated", ["owner_user_id", "updated_at"], unique=False)
        batch_op.create_index("idx_ai_chat_agents_visibility_enabled", ["visibility", "enabled"], unique=False)

    op.create_table(
        "ai_chat_agent_shares",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="viewer"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["agent_id"], ["ai_chat_agents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent_id", "target_user_id", name="uq_ai_chat_agent_shares_agent_user"),
    )

    op.create_index(
        "idx_ai_chat_agent_shares_target",
        "ai_chat_agent_shares",
        ["target_user_id", "agent_id"],
        unique=False,
    )

    op.create_table(
        "ai_chat_agent_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider_key", sa.String(length=120), nullable=False),
        sa.Column("action_id", sa.String(length=300), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("sensitivity", sa.String(length=40), nullable=False, server_default="read"),
        sa.Column("requires_confirmation", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["agent_id"], ["ai_chat_agents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent_id", "provider_key", "action_id", name="uq_ai_chat_agent_actions_agent_provider_action"),
    )

    op.create_index(
        "idx_ai_chat_agent_actions_agent_enabled",
        "ai_chat_agent_actions",
        ["agent_id", "enabled"],
        unique=False,
    )


def downgrade():
    op.drop_index("idx_ai_chat_agent_actions_agent_enabled", table_name="ai_chat_agent_actions")
    op.drop_table("ai_chat_agent_actions")

    op.drop_index("idx_ai_chat_agent_shares_target", table_name="ai_chat_agent_shares")
    op.drop_table("ai_chat_agent_shares")

    with op.batch_alter_table("ai_chat_agents", schema=None) as batch_op:
        batch_op.drop_index("idx_ai_chat_agents_visibility_enabled")
        batch_op.drop_index("idx_ai_chat_agents_owner_updated")
        batch_op.drop_column("requires_confirmation_for_write")
        batch_op.drop_column("max_tool_calls")
        batch_op.drop_column("response_style")
        batch_op.drop_column("icon")
        batch_op.drop_column("category")
        batch_op.drop_column("visibility")
        batch_op.drop_column("owner_user_id")
