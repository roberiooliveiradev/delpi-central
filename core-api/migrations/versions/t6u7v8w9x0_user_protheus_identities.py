"""user_protheus_identities — Core ownership of portal↔Protheus mapping

Revision ID: t6u7v8w9x0
Revises: s5t6u7v8w9
Create Date: 2026-10-19

Platform-owned association between Minha DELPI users and Protheus SYS_USR
identities (USR_ID / USR_CODIGO). Does not modify purchase_requests schema.
"""

from alembic import op
import sqlalchemy as sa


revision = "t6u7v8w9x0"
down_revision = "s5t6u7v8w9"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_protheus_identities",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("protheus_user_id", sa.Text(), nullable=True),
        sa.Column("protheus_user_code", sa.Text(), nullable=True),
        sa.Column(
            "mapping_status",
            sa.Text(),
            nullable=False,
            server_default="unmapped",
        ),
        sa.Column("mapping_source", sa.Text(), nullable=True),
        sa.Column(
            "verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("updated_by_user_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "mapping_status IN ('mapped', 'unmapped', 'ambiguous')",
            name="ck_user_protheus_identities_status",
        ),
        sa.CheckConstraint(
            "mapping_source IS NULL OR mapping_source IN "
            "('manual', 'email_match', 'login_match')",
            name="ck_user_protheus_identities_source",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["updated_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_index(
        "idx_user_protheus_identities_protheus_user_mapped",
        "user_protheus_identities",
        ["protheus_user_id"],
        unique=True,
        postgresql_where=sa.text(
            "protheus_user_id IS NOT NULL AND mapping_status = 'mapped'"
        ),
    )


def downgrade():
    op.drop_index(
        "idx_user_protheus_identities_protheus_user_mapped",
        table_name="user_protheus_identities",
    )
    op.drop_table("user_protheus_identities")
