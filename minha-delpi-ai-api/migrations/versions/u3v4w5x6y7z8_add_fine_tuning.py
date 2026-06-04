"""add fine-tuning datasets, samples and runs

Fine-tuning offline (playbook Fase 7): curadoria, anonimização, exportação e jobs.

Revision ID: u3v4w5x6y7z8
Revises: t2u3v4w5x6y7
Create Date: 2026-06-04 14:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "u3v4w5x6y7z8"
down_revision = "t2u3v4w5x6y7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ai_fine_tuning_datasets",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="draft"),
        sa.Column("target_model", sa.String(length=64), nullable=False, server_default="intent_classifier"),
        sa.Column("dataset_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ai_fine_tuning_datasets_status",
        "ai_fine_tuning_datasets",
        ["status"],
        unique=False,
    )

    op.create_table(
        "ai_fine_tuning_samples",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("dataset_id", sa.BigInteger(), nullable=True),
        sa.Column("category", sa.String(length=32), nullable=False, server_default="routing"),
        sa.Column("source", sa.String(length=48), nullable=False),
        sa.Column("source_ref", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="captured"),
        sa.Column("messages_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("intent_label", sa.String(length=80), nullable=True),
        sa.Column("quality_score", sa.Numeric(4, 3), nullable=True),
        sa.Column("anonymized", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("risk_level", sa.String(length=16), nullable=True),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["dataset_id"], ["ai_fine_tuning_datasets.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ai_fine_tuning_samples_status",
        "ai_fine_tuning_samples",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_ai_fine_tuning_samples_dataset",
        "ai_fine_tuning_samples",
        ["dataset_id"],
        unique=False,
    )
    op.create_index(
        "ix_ai_fine_tuning_samples_source_ref",
        "ai_fine_tuning_samples",
        ["source", "source_ref"],
        unique=False,
    )

    op.create_table(
        "ai_fine_tuning_runs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("dataset_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="pending"),
        sa.Column("target_model", sa.String(length=64), nullable=False),
        sa.Column("export_format", sa.String(length=16), nullable=False, server_default="jsonl"),
        sa.Column("export_stats", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("active_deploy", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["dataset_id"], ["ai_fine_tuning_datasets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ai_fine_tuning_runs_dataset_status",
        "ai_fine_tuning_runs",
        ["dataset_id", "status"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_ai_fine_tuning_runs_dataset_status", table_name="ai_fine_tuning_runs")
    op.drop_table("ai_fine_tuning_runs")
    op.drop_index("ix_ai_fine_tuning_samples_source_ref", table_name="ai_fine_tuning_samples")
    op.drop_index("ix_ai_fine_tuning_samples_dataset", table_name="ai_fine_tuning_samples")
    op.drop_index("ix_ai_fine_tuning_samples_status", table_name="ai_fine_tuning_samples")
    op.drop_table("ai_fine_tuning_samples")
    op.drop_index("ix_ai_fine_tuning_datasets_status", table_name="ai_fine_tuning_datasets")
    op.drop_table("ai_fine_tuning_datasets")
