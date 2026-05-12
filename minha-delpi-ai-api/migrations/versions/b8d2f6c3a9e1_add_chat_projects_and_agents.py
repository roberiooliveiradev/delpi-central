"""add chat projects and agents

Revision ID: b8d2f6c3a9e1
Revises: a1f4c9d8e2b7
Create Date: 2026-05-12 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "b8d2f6c3a9e1"
down_revision = "a1f4c9d8e2b7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ai_chat_projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
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
    )

    op.create_index(
        "idx_ai_chat_projects_user_updated",
        "ai_chat_projects",
        ["user_id", "updated_at"],
        unique=False,
    )

    op.create_table(
        "ai_chat_agents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("key", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=800), nullable=True),
        sa.Column("system_prompt", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
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
        sa.UniqueConstraint("key", name="uq_ai_chat_agents_key"),
    )

    op.create_index(
        op.f("ix_ai_chat_agents_enabled"),
        "ai_chat_agents",
        ["enabled"],
        unique=False,
    )

    with op.batch_alter_table("ai_chat_sessions", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "project_id",
                postgresql.UUID(as_uuid=True),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "agent_key",
                sa.String(length=80),
                nullable=True,
            )
        )
        batch_op.create_foreign_key(
            "fk_ai_chat_sessions_project_id_ai_chat_projects",
            "ai_chat_projects",
            ["project_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index(
            "idx_ai_chat_sessions_user_project_updated",
            ["user_id", "project_id", "updated_at"],
            unique=False,
        )
        batch_op.create_index(
            op.f("ix_ai_chat_sessions_agent_key"),
            ["agent_key"],
            unique=False,
        )

    op.execute(
        """
        insert into ai_chat_agents
            (id, key, name, description, system_prompt, enabled, metadata)
        values
            (
                gen_random_uuid(),
                'minha-delpi-chat',
                'Minha DELPI Chat',
                'Assistente corporativo geral da Minha DELPI, com acesso a conhecimento, APIs autorizadas e ferramentas configuradas.',
                'Você é o assistente corporativo Minha DELPI Chat. Responda em português do Brasil, com clareza, objetividade e respeitando permissões.',
                true,
                '{"icon": "bot", "category": "general"}'::jsonb
            ),
            (
                gen_random_uuid(),
                'openapi-actions',
                'Ações OpenAPI',
                'Agente focado em consultar APIs internas e externas cadastradas via schema OpenAPI.',
                'Você é um agente de ações OpenAPI. Use ferramentas autorizadas quando a pergunta exigir dados operacionais, explique os resultados em português e nunca invente dados.',
                true,
                '{"icon": "box", "category": "actions"}'::jsonb
            ),
            (
                gen_random_uuid(),
                'produtos-estoque',
                'Produtos e estoque',
                'Agente especializado em produtos, estoque, compras, estrutura e dados operacionais da API DELPI.',
                'Você é um agente especializado em produtos e estoque da DELPI. Priorize consultas autorizadas na API DELPI para dados operacionais e traduza campos técnicos para linguagem humana.',
                true,
                '{"icon": "package", "category": "products"}'::jsonb
            )
        on conflict (key) do nothing
        """
    )


def downgrade():
    with op.batch_alter_table("ai_chat_sessions", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_ai_chat_sessions_agent_key"))
        batch_op.drop_index("idx_ai_chat_sessions_user_project_updated")
        batch_op.drop_constraint(
            "fk_ai_chat_sessions_project_id_ai_chat_projects",
            type_="foreignkey",
        )
        batch_op.drop_column("agent_key")
        batch_op.drop_column("project_id")

    op.drop_index(op.f("ix_ai_chat_agents_enabled"), table_name="ai_chat_agents")
    op.drop_table("ai_chat_agents")

    op.drop_index("idx_ai_chat_projects_user_updated", table_name="ai_chat_projects")
    op.drop_table("ai_chat_projects")
