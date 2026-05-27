"""add company knowledge chat skill

Revision ID: i0j1k2l3m4n5
Revises: h9i0j1k2l3m4
Create Date: 2026-05-27 20:00:00.000000
"""

from pathlib import Path

from alembic import op
import sqlalchemy as sa


revision = "i0j1k2l3m4n5"
down_revision = "h9i0j1k2l3m4"
branch_labels = None
depends_on = None

_POLICIES_DIR = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "domain"
    / "prompt_policies"
)


def _read_policy(filename: str) -> str:
    path = _POLICIES_DIR / filename
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def upgrade():
    policy = _read_policy("company-knowledge-skill.md")
    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            INSERT INTO ai_chat_skill_catalog (
                id, skill_key, label, description, policy_content, policy_file,
                metadata_flag, legacy_metadata_flag, execution_path_hint,
                execution_derived_key, is_active, sort_order
            )
            SELECT
                gen_random_uuid(),
                'company-knowledge',
                'Conhecimento da empresa',
                :description,
                :policy_content,
                'company-knowledge-skill.md',
                'enabled',
                'companyKnowledge',
                'search_knowledge_base',
                NULL,
                true,
                10
            WHERE NOT EXISTS (
                SELECT 1 FROM ai_chat_skill_catalog
                WHERE skill_key = 'company-knowledge'
            )
            """
        ),
        {
            "description": (
                "Prioriza a base documental global da empresa (políticas, diretrizes, "
                "glossário e manuais). Orienta o uso do RAG e da ferramenta "
                "search_knowledge_base, com citação de fontes quando aplicável."
            ),
            "policy_content": policy,
        },
    )


def downgrade():
    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            DELETE FROM ai_chat_skill_catalog
            WHERE skill_key = 'company-knowledge'
            """
        )
    )
