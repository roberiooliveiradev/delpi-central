"""enable api-delpi provider on official system agents (vendas/faturamento)

Revision ID: p8q9r0s1t3
Revises: o7p8q9r0s1t2
Create Date: 2026-05-31 00:25:00.000000

Habilita rotas api_delpi (ex.: /products/{code}/sales/billing) no agente oficial,
complementando api-externa que hoje expõe sobretudo estoque/estrutura/fornecedores.
"""

from alembic import op


revision = "p8q9r0s1t3"
down_revision = "o7p8q9r0s1t2"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        UPDATE ai_chat_agent_action_providers AS cap
        SET enabled = TRUE,
            updated_at = NOW()
        FROM ai_chat_agents AS a
        WHERE cap.agent_id = a.id
          AND a.visibility = 'system'
          AND a.enabled IS TRUE
          AND cap.provider_key = 'api-delpi'
          AND cap.enabled IS FALSE
        """
    )


def downgrade():
    op.execute(
        """
        UPDATE ai_chat_agent_action_providers AS cap
        SET enabled = FALSE,
            updated_at = NOW()
        FROM ai_chat_agents AS a
        WHERE cap.agent_id = a.id
          AND a.visibility = 'system'
          AND a.enabled IS TRUE
          AND cap.provider_key = 'api-delpi'
        """
    )
