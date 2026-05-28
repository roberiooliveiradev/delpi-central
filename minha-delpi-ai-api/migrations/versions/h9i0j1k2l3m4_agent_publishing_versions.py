"""agent publishing and version history

Revision ID: h9i0j1k2l3m4
Revises: g8h9i0j1k2l3
Create Date: 2026-05-27 18:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "h9i0j1k2l3m4"
down_revision = "g8h9i0j1k2l3"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "ai_chat_agents",
        sa.Column("published_version", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "ai_chat_agents",
        sa.Column(
            "published_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "ai_chat_agents",
        sa.Column("published_config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    op.create_table(
        "ai_chat_agent_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("event", sa.String(length=40), nullable=False, server_default="published"),
        sa.Column("snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["ai_chat_agents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "agent_id",
            "version",
            name="uq_ai_chat_agent_versions_agent_version",
        ),
    )
    op.create_index(
        "ix_ai_chat_agent_versions_agent_id",
        "ai_chat_agent_versions",
        ["agent_id"],
    )
    op.create_index(
        "ix_ai_chat_agent_versions_created_at",
        "ai_chat_agent_versions",
        ["created_at"],
    )

    # Agentes já ativos passam a contar como publicados na v1 (retrocompat).
    op.execute(
        """
        UPDATE ai_chat_agents
        SET
            published_version = 1,
            published_at = COALESCE(updated_at, created_at, NOW()),
            published_config = jsonb_build_object(
                'version', 1,
                'name', name,
                'description', description,
                'systemPrompt', system_prompt,
                'responseStyle', response_style,
                'category', category,
                'icon', icon,
                'maxToolCalls', max_tool_calls,
                'requiresConfirmationForWrite', requires_confirmation_for_write,
                'metadata', COALESCE(metadata, '{}'::jsonb)
            )
        WHERE enabled IS TRUE
        """
    )


def downgrade():
    op.drop_index("ix_ai_chat_agent_versions_created_at", table_name="ai_chat_agent_versions")
    op.drop_index("ix_ai_chat_agent_versions_agent_id", table_name="ai_chat_agent_versions")
    op.drop_table("ai_chat_agent_versions")
    op.drop_column("ai_chat_agents", "published_config")
    op.drop_column("ai_chat_agents", "published_at")
    op.drop_column("ai_chat_agents", "published_version")
