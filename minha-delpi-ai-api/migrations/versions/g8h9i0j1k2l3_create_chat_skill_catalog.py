"""create chat skill catalog

Revision ID: g8h9i0j1k2l3
Revises: f7a8b9c0d1e2
Create Date: 2026-05-27 12:00:00.000000

"""
from pathlib import Path

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "g8h9i0j1k2l3"
down_revision = "f7a8b9c0d1e2"
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
    op.create_table(
        "ai_chat_skill_catalog",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_key", sa.String(length=80), nullable=False),
        sa.Column("label", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("policy_content", sa.Text(), nullable=True),
        sa.Column("policy_file", sa.String(length=120), nullable=True),
        sa.Column("metadata_flag", sa.String(length=80), nullable=False, server_default="enabled"),
        sa.Column("legacy_metadata_flag", sa.String(length=80), nullable=True),
        sa.Column("execution_path_hint", sa.String(length=200), nullable=True),
        sa.Column("execution_derived_key", sa.String(length=80), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("skill_key", name="uq_ai_chat_skill_catalog_key"),
    )

    op.create_index(
        "ix_ai_chat_skill_catalog_active_sort",
        "ai_chat_skill_catalog",
        ["is_active", "sort_order"],
        unique=False,
    )

    sql_policy = _read_policy("sql-assistant-skill.md")
    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            INSERT INTO ai_chat_skill_catalog (
                id, skill_key, label, description, policy_content, policy_file,
                metadata_flag, legacy_metadata_flag, execution_path_hint,
                execution_derived_key, is_active, sort_order
            ) VALUES (
                gen_random_uuid(),
                'sql',
                'Especialista SQL',
                :description,
                :policy_content,
                'sql-assistant-skill.md',
                'authoring',
                'sqlAuthoring',
                'POST /data/sql',
                'sqlExecutionAvailable',
                true,
                0
            )
            """
        ),
        {
            "description": (
                "Elabora, explica, corrige e revisa consultas SELECT (SQL genérico) em blocos ```sql```. "
                "Identifica erros de sintaxe e lógica quando o usuário colar SQL ou mensagens de erro. "
                "A execução no banco depende da action POST /data/sql habilitada no agente."
            ),
            "policy_content": sql_policy,
        },
    )


def downgrade():
    op.drop_index("ix_ai_chat_skill_catalog_active_sort", table_name="ai_chat_skill_catalog")
    op.drop_table("ai_chat_skill_catalog")
