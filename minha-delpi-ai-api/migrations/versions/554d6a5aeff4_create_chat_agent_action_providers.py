"""create chat agent action providers

Revision ID: 554d6a5aeff4
Revises: e7f8a9b0c1d2
Create Date: 2026-05-13 16:02:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "554d6a5aeff4"
down_revision = "e7f8a9b0c1d2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ai_chat_agent_action_providers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider_key", sa.String(length=120), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("allow_read", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("allow_write", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("allow_admin", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("requires_confirmation_for_write", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["ai_chat_agents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "agent_id",
            "provider_key",
            name="uq_ai_chat_agent_action_providers_agent_provider",
        ),
    )
    op.create_index(
        "ix_ai_chat_agent_action_providers_agent_id",
        "ai_chat_agent_action_providers",
        ["agent_id"],
        unique=False,
    )
    op.create_index(
        "ix_ai_chat_agent_action_providers_provider_key",
        "ai_chat_agent_action_providers",
        ["provider_key"],
        unique=False,
    )
    op.create_index(
        "ix_ai_chat_agent_action_providers_enabled",
        "ai_chat_agent_action_providers",
        ["enabled"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_ai_chat_agent_action_providers_enabled", table_name="ai_chat_agent_action_providers")
    op.drop_index("ix_ai_chat_agent_action_providers_provider_key", table_name="ai_chat_agent_action_providers")
    op.drop_index("ix_ai_chat_agent_action_providers_agent_id", table_name="ai_chat_agent_action_providers")
    op.drop_table("ai_chat_agent_action_providers")
