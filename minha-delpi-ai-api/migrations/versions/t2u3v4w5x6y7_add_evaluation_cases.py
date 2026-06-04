"""add ai_evaluation_cases

Casos de regressão para aprendizagem contínua (playbook Fase 6):
validação automática e bloqueio de promoção que quebra roteamento/normalização.

Revision ID: t2u3v4w5x6y7
Revises: s1t2u3v4w5x6
Create Date: 2026-06-04 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "t2u3v4w5x6y7"
down_revision = "s1t2u3v4w5x6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ai_evaluation_cases",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("input", sa.Text(), nullable=False),
        sa.Column("expected_intent", sa.String(length=80), nullable=True),
        sa.Column("expected_answer", sa.Text(), nullable=True),
        sa.Column("expected_normalized", sa.String(length=240), nullable=True),
        sa.Column("must_not_use_tools", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("must_not_use_rag", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("source_feedback_id", sa.BigInteger(), nullable=True),
        sa.Column("linked_candidate_id", sa.BigInteger(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="active"),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_passed", sa.Boolean(), nullable=True),
        sa.Column("last_failure_reason", sa.Text(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ai_evaluation_cases_category_status",
        "ai_evaluation_cases",
        ["category", "status"],
        unique=False,
    )
    op.create_index(
        "ix_ai_evaluation_cases_created_at",
        "ai_evaluation_cases",
        ["created_at"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_ai_evaluation_cases_created_at", table_name="ai_evaluation_cases")
    op.drop_index(
        "ix_ai_evaluation_cases_category_status",
        table_name="ai_evaluation_cases",
    )
    op.drop_table("ai_evaluation_cases")
