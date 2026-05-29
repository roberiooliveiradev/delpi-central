"""disable legacy seed agents (produtos-estoque, openapi-actions)

Revision ID: k2l3m4n5o6p7
Revises: j1k2l3m4n5o6
Create Date: 2026-05-29 20:00:00.000000
"""

from alembic import op


revision = "k2l3m4n5o6p7"
down_revision = "j1k2l3m4n5o6"
branch_labels = None
depends_on = None

_LEGACY_AGENT_KEYS = ("produtos-estoque", "openapi-actions")


def upgrade():
    keys_sql = ", ".join(f"'{key}'" for key in _LEGACY_AGENT_KEYS)
    op.execute(
        f"""
        UPDATE ai_chat_agents
        SET enabled = FALSE
        WHERE key IN ({keys_sql})
          AND enabled IS TRUE
        """
    )


def downgrade():
    keys_sql = ", ".join(f"'{key}'" for key in _LEGACY_AGENT_KEYS)
    op.execute(
        f"""
        UPDATE ai_chat_agents
        SET enabled = TRUE
        WHERE key IN ({keys_sql})
        """
    )
