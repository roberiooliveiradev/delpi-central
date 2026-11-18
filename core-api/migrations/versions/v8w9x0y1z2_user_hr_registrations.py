"""GLPI #887: explicit Core user <-> Portal RH registration mapping.

Revision ID: v8w9x0y1z2
Revises: u7v8w9x0y1

The HR manager hierarchy remains live in Portal RH; only the manually
verified cross-system identity association is persisted in Core.
"""

from alembic import op
import sqlalchemy as sa

revision = "v8w9x0y1z2"
down_revision = "u7v8w9x0y1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_hr_registrations",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("registration", sa.String(length=30), nullable=False),
        sa.Column("verified_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("user_id"),
        sa.UniqueConstraint("registration", name="uq_user_hr_registrations_registration"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["verified_by_user_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.CheckConstraint(
            "length(registration) BETWEEN 1 AND 30",
            name="ck_user_hr_registrations_length",
        ),
    )


def downgrade():
    op.drop_table("user_hr_registrations")
