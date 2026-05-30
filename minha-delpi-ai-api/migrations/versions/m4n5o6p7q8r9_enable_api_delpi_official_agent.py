"""enable api-delpi provider for official Minha DELPI agent

Revision ID: m4n5o6p7q8r9
Revises: l3m4n5o6p7q8
Create Date: 2026-05-30 16:20:00.000000
"""

from alembic import op


revision = "m4n5o6p7q8r9"
down_revision = "l3m4n5o6p7q8"
branch_labels = None
depends_on = None

_OFFICIAL_AGENT_NAME = "Agente Minha DELPI"
_PROVIDER_KEY = "api-delpi"


def upgrade():
    op.execute(
        f"""
        UPDATE ai_chat_agent_action_providers AS link
        SET enabled = TRUE, updated_at = NOW()
        FROM ai_chat_agents AS agent
        WHERE link.agent_id = agent.id
          AND agent.name = '{_OFFICIAL_AGENT_NAME}'
          AND agent.visibility = 'system'
          AND link.provider_key = '{_PROVIDER_KEY}'
          AND link.enabled IS FALSE
        """
    )


def downgrade():
    op.execute(
        f"""
        UPDATE ai_chat_agent_action_providers AS link
        SET enabled = FALSE, updated_at = NOW()
        FROM ai_chat_agents AS agent
        WHERE link.agent_id = agent.id
          AND agent.name = '{_OFFICIAL_AGENT_NAME}'
          AND agent.visibility = 'system'
          AND link.provider_key = '{_PROVIDER_KEY}'
          AND link.enabled IS TRUE
        """
    )
