"""add audit trace id

Revision ID: c4d5e6f7a8b9
Revises: b2c3d4e5f6a7
Create Date: 2026-05-18 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "c4d5e6f7a8b9"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "ai_audit_logs",
        sa.Column("trace_id", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_ai_audit_logs_trace_id",
        "ai_audit_logs",
        ["trace_id"],
    )


def downgrade():
    op.drop_index("ix_ai_audit_logs_trace_id", table_name="ai_audit_logs")
    op.drop_column("ai_audit_logs", "trace_id")
