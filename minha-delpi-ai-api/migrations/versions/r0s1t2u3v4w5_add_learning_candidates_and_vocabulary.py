"""add ai_learning_candidates and ai_vocabulary_terms

Camada de aprendizagem contínua (playbook): candidatos de conhecimento
revisáveis e glossário/typos aprendidos por escopo.

Revision ID: r0s1t2u3v4w5
Revises: q9r0s1t2u3v4
Create Date: 2026-06-04 09:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "r0s1t2u3v4w5"
down_revision = "q9r0s1t2u3v4"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ai_learning_candidates",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("candidate_type", sa.String(length=32), nullable=False),
        sa.Column("term", sa.String(length=160), nullable=True),
        sa.Column("input_text", sa.Text(), nullable=False),
        sa.Column("proposed_rule", sa.String(length=240), nullable=True),
        sa.Column("proposed_meaning", sa.Text(), nullable=True),
        sa.Column("evidence_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=True),
        sa.Column("evidence_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("risk_level", sa.String(length=16), nullable=False, server_default="low"),
        sa.Column("scope", sa.String(length=16), nullable=False, server_default="global"),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="pending"),
        sa.Column("source", sa.String(length=48), nullable=False, server_default="auto"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("promoted_term_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ai_learning_candidates_status",
        "ai_learning_candidates",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_ai_learning_candidates_dedup",
        "ai_learning_candidates",
        ["candidate_type", "term", "scope", "status"],
        unique=False,
    )
    op.create_index(
        "ix_ai_learning_candidates_created_at",
        "ai_learning_candidates",
        ["created_at"],
        unique=False,
    )

    op.create_table(
        "ai_vocabulary_terms",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("term", sa.String(length=160), nullable=False),
        sa.Column("normalized_term", sa.String(length=160), nullable=False),
        sa.Column("meaning", sa.Text(), nullable=True),
        sa.Column("type", sa.String(length=32), nullable=False, server_default="typo"),
        sa.Column("scope", sa.String(length=16), nullable=False, server_default="global"),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source", sa.String(length=48), nullable=False, server_default="promotion"),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=True),
        sa.Column("evidence_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("approved", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ai_vocabulary_terms_lookup",
        "ai_vocabulary_terms",
        ["scope", "approved", "active", "type"],
        unique=False,
    )
    op.create_index(
        "ix_ai_vocabulary_terms_term",
        "ai_vocabulary_terms",
        ["term"],
        unique=False,
    )
    op.create_index(
        "ix_ai_vocabulary_terms_dedup",
        "ai_vocabulary_terms",
        ["normalized_term", "scope", "project_id"],
        unique=True,
    )


def downgrade():
    op.drop_index("ix_ai_vocabulary_terms_dedup", table_name="ai_vocabulary_terms")
    op.drop_index("ix_ai_vocabulary_terms_term", table_name="ai_vocabulary_terms")
    op.drop_index("ix_ai_vocabulary_terms_lookup", table_name="ai_vocabulary_terms")
    op.drop_table("ai_vocabulary_terms")
    op.drop_index("ix_ai_learning_candidates_created_at", table_name="ai_learning_candidates")
    op.drop_index("ix_ai_learning_candidates_dedup", table_name="ai_learning_candidates")
    op.drop_index("ix_ai_learning_candidates_status", table_name="ai_learning_candidates")
    op.drop_table("ai_learning_candidates")
