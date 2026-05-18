"""user birth_date for birthday automation

Revision ID: g3b4c5d6e7f8
Revises: f2a3b4c5d6e7
Create Date: 2026-05-18

"""

from alembic import op
import sqlalchemy as sa


revision = "g3b4c5d6e7f8"
down_revision = "f2a3b4c5d6e7"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("birth_date", sa.Date(), nullable=True))
    op.create_index("ix_users_birth_date", "users", ["birth_date"])


def downgrade():
    op.drop_index("ix_users_birth_date", table_name="users")
    op.drop_column("users", "birth_date")
