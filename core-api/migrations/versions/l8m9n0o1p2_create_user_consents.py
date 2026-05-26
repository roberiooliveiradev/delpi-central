"""create user_consents table

Revision ID: l8m9n0o1p2
Revises: k7l8m9n0o2
Create Date: 2026-05-26

"""
from alembic import op
import sqlalchemy as sa

revision = "l8m9n0o1p2"
down_revision = "k7l8m9n0o2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_consents",
        sa.Column("id", sa.Uuid(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("purpose", sa.String(100), nullable=False),
        sa.Column("granted", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "purpose", name="uq_user_consents_user_purpose"),
    )
    op.create_index("ix_user_consents_user_id", "user_consents", ["user_id"])
    op.create_index("ix_user_consents_purpose", "user_consents", ["purpose"])


def downgrade():
    op.drop_table("user_consents")
