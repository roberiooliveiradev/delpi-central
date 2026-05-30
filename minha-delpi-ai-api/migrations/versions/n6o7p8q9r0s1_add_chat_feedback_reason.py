"""add optional structured reason to chat message feedback

Revision ID: n6o7p8q9r0s1
Revises: m5n6o7p8q9r0
Create Date: 2026-05-30 22:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "n6o7p8q9r0s1"
down_revision = "m5n6o7p8q9r0"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "ai_chat_message_feedback",
        sa.Column("reason", sa.String(length=64), nullable=True),
    )


def downgrade():
    op.drop_column("ai_chat_message_feedback", "reason")
