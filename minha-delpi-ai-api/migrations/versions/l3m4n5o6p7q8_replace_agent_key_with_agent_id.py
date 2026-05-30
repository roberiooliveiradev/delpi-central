"""replace agent_key with agent_id across chat tables

Revision ID: l3m4n5o6p7q8
Revises: k2l3m4n5o6p7
Create Date: 2026-05-30 14:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "l3m4n5o6p7q8"
down_revision = "k2l3m4n5o6p7"
branch_labels = None
depends_on = None


def upgrade():
    # --- ai_chat_sessions: agent_key -> agent_id ---
    op.add_column(
        "ai_chat_sessions",
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        op.f("ix_ai_chat_sessions_agent_id"),
        "ai_chat_sessions",
        ["agent_id"],
        unique=False,
    )
    op.execute(
        """
        UPDATE ai_chat_sessions AS s
        SET agent_id = a.id
        FROM ai_chat_agents AS a
        WHERE s.agent_key IS NOT NULL
          AND s.agent_key = a.key
        """
    )
    op.create_foreign_key(
        "fk_ai_chat_sessions_agent_id",
        "ai_chat_sessions",
        "ai_chat_agents",
        ["agent_id"],
        ["id"],
        ondelete="SET NULL",
    )
    with op.batch_alter_table("ai_chat_sessions", schema=None) as batch_op:
        batch_op.drop_index("ix_ai_chat_sessions_agent_key")
        batch_op.drop_column("agent_key")

    # --- ai_chat_projects: default_agent_key -> default_agent_id ---
    op.add_column(
        "ai_chat_projects",
        sa.Column("default_agent_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        op.f("ix_ai_chat_projects_default_agent_id"),
        "ai_chat_projects",
        ["default_agent_id"],
        unique=False,
    )
    op.execute(
        """
        UPDATE ai_chat_projects AS p
        SET default_agent_id = a.id
        FROM ai_chat_agents AS a
        WHERE p.default_agent_key IS NOT NULL
          AND p.default_agent_key = a.key
        """
    )
    op.create_foreign_key(
        "fk_ai_chat_projects_default_agent_id",
        "ai_chat_projects",
        "ai_chat_agents",
        ["default_agent_id"],
        ["id"],
        ondelete="SET NULL",
    )
    with op.batch_alter_table("ai_chat_projects", schema=None) as batch_op:
        batch_op.drop_index("ix_ai_chat_projects_default_agent_key")
        batch_op.drop_column("default_agent_key")

    # --- ai_chat_attachments: agent_key -> agent_id ---
    op.add_column(
        "ai_chat_attachments",
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        op.f("ix_ai_chat_attachments_agent_id"),
        "ai_chat_attachments",
        ["agent_id"],
        unique=False,
    )
    op.execute(
        """
        UPDATE ai_chat_attachments AS att
        SET agent_id = a.id
        FROM ai_chat_agents AS a
        WHERE att.agent_key IS NOT NULL
          AND att.agent_key = a.key
        """
    )
    op.create_foreign_key(
        "fk_ai_chat_attachments_agent_id",
        "ai_chat_attachments",
        "ai_chat_agents",
        ["agent_id"],
        ["id"],
        ondelete="SET NULL",
    )
    with op.batch_alter_table("ai_chat_attachments", schema=None) as batch_op:
        batch_op.drop_index("ix_ai_chat_attachments_agent_key")
        batch_op.drop_column("agent_key")

    # --- JSON metadata: agentKey -> agentId (attachments + knowledge) ---
    op.execute(
        """
        UPDATE ai_chat_attachments AS att
        SET metadata = (att.metadata - 'agentKey') || jsonb_build_object('agentId', a.id::text)
        FROM ai_chat_agents AS a
        WHERE att.metadata ? 'agentKey'
          AND att.metadata->>'agentKey' = a.key
        """
    )

    op.execute(
        """
        UPDATE ai_knowledge_documents AS doc
        SET metadata = (doc.metadata - 'agentKey') || jsonb_build_object('agentId', a.id::text)
        FROM ai_chat_agents AS a
        WHERE doc.metadata ? 'agentKey'
          AND doc.metadata->>'agentKey' = a.key
        """
    )

    # --- ai_chat_agents: remove slug key column ---
    with op.batch_alter_table("ai_chat_agents", schema=None) as batch_op:
        batch_op.drop_constraint("uq_ai_chat_agents_key", type_="unique")
        batch_op.drop_column("key")


def downgrade():
    with op.batch_alter_table("ai_chat_agents", schema=None) as batch_op:
        batch_op.add_column(sa.Column("key", sa.String(length=80), nullable=True))
    op.execute(
        """
        UPDATE ai_chat_agents
        SET key = LEFT(REPLACE(id::text, '-', ''), 80)
        WHERE key IS NULL
        """
    )
    with op.batch_alter_table("ai_chat_agents", schema=None) as batch_op:
        batch_op.alter_column("key", nullable=False)
        batch_op.create_unique_constraint("uq_ai_chat_agents_key", ["key"])

    with op.batch_alter_table("ai_chat_attachments", schema=None) as batch_op:
        batch_op.drop_constraint("fk_ai_chat_attachments_agent_id", type_="foreignkey")
        batch_op.drop_index(op.f("ix_ai_chat_attachments_agent_id"))
        batch_op.add_column(sa.Column("agent_key", sa.String(length=80), nullable=True))
    op.execute(
        """
        UPDATE ai_chat_attachments AS att
        SET agent_key = a.key
        FROM ai_chat_agents AS a
        WHERE att.agent_id = a.id
        """
    )
    op.drop_column("ai_chat_attachments", "agent_id")
    op.create_index(
        op.f("ix_ai_chat_attachments_agent_key"),
        "ai_chat_attachments",
        ["agent_key"],
        unique=False,
    )

    with op.batch_alter_table("ai_chat_projects", schema=None) as batch_op:
        batch_op.drop_constraint("fk_ai_chat_projects_default_agent_id", type_="foreignkey")
        batch_op.drop_index(op.f("ix_ai_chat_projects_default_agent_id"))
        batch_op.add_column(sa.Column("default_agent_key", sa.String(length=80), nullable=True))
    op.execute(
        """
        UPDATE ai_chat_projects AS p
        SET default_agent_key = a.key
        FROM ai_chat_agents AS a
        WHERE p.default_agent_id = a.id
        """
    )
    op.drop_column("ai_chat_projects", "default_agent_id")
    op.create_index(
        op.f("ix_ai_chat_projects_default_agent_key"),
        "ai_chat_projects",
        ["default_agent_key"],
        unique=False,
    )

    with op.batch_alter_table("ai_chat_sessions", schema=None) as batch_op:
        batch_op.drop_constraint("fk_ai_chat_sessions_agent_id", type_="foreignkey")
        batch_op.drop_index(op.f("ix_ai_chat_sessions_agent_id"))
        batch_op.add_column(sa.Column("agent_key", sa.String(length=80), nullable=True))
    op.execute(
        """
        UPDATE ai_chat_sessions AS s
        SET agent_key = a.key
        FROM ai_chat_agents AS a
        WHERE s.agent_id = a.id
        """
    )
    op.drop_column("ai_chat_sessions", "agent_id")
    op.create_index(
        op.f("ix_ai_chat_sessions_agent_key"),
        "ai_chat_sessions",
        ["agent_key"],
        unique=False,
    )
