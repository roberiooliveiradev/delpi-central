"""rename official minha-delpi-chat agent display name

Revision ID: j1k2l3m4n5o6
Revises: i0j1k2l3m4n5
Create Date: 2026-05-29 16:30:00.000000
"""

from alembic import op


revision = "j1k2l3m4n5o6"
down_revision = "i0j1k2l3m4n5"
branch_labels = None
depends_on = None

_CANONICAL_NAME = "Agente Minha DELPI"


def upgrade():
    op.execute(
        f"""
        UPDATE ai_chat_agents
        SET
            name = '{_CANONICAL_NAME}',
            published_config = CASE
                WHEN published_config IS NOT NULL THEN
                    jsonb_set(
                        published_config,
                        '{{name}}',
                        to_jsonb('{_CANONICAL_NAME}'::text),
                        true
                    )
                ELSE published_config
            END,
            updated_at = NOW()
        WHERE key = 'minha-delpi-chat'
        """
    )


def downgrade():
    op.execute(
        """
        UPDATE ai_chat_agents
        SET
            name = 'Minha DELPI Chat',
            published_config = CASE
                WHEN published_config IS NOT NULL THEN
                    jsonb_set(
                        published_config,
                        '{name}',
                        to_jsonb('Minha DELPI Chat'::text),
                        true
                    )
                ELSE published_config
            END,
            updated_at = NOW()
        WHERE key = 'minha-delpi-chat'
          AND name = 'Agente Minha DELPI'
        """
    )
