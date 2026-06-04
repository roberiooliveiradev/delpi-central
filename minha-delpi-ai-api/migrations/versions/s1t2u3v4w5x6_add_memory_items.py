"""add ai_memory_items

Memória persistente do usuário/projeto (playbook §30, Fase 3): preferências,
correções e fatos estáveis cross-sessão, com governança (status + esquecer).
A coluna embedding fica reservada para recuperação semântica futura.

Revision ID: s1t2u3v4w5x6
Revises: r0s1t2u3v4w5
Create Date: 2026-06-04 09:30:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "s1t2u3v4w5x6"
down_revision = "r0s1t2u3v4w5"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ai_memory_items",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("scope", sa.String(length=16), nullable=False, server_default="user"),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_norm", sa.String(length=320), nullable=False),
        sa.Column("content_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("embedding", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=True),
        sa.Column("evidence_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("source", sa.String(length=48), nullable=False, server_default="auto"),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="active"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ai_memory_items_lookup",
        "ai_memory_items",
        ["user_id", "scope", "status"],
        unique=False,
    )
    op.create_index(
        "ix_ai_memory_items_project",
        "ai_memory_items",
        ["project_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_ai_memory_items_dedup",
        "ai_memory_items",
        ["user_id", "scope", "type", "content_norm"],
        unique=False,
    )
    op.create_index(
        "ix_ai_memory_items_created_at",
        "ai_memory_items",
        ["created_at"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_ai_memory_items_created_at", table_name="ai_memory_items")
    op.drop_index("ix_ai_memory_items_dedup", table_name="ai_memory_items")
    op.drop_index("ix_ai_memory_items_project", table_name="ai_memory_items")
    op.drop_index("ix_ai_memory_items_lookup", table_name="ai_memory_items")
    op.drop_table("ai_memory_items")
