"""user_person_profiles for portal photo, job title and contacts

Revision ID: s5t6u7v8w9
Revises: r4s5t6u7v8
Create Date: 2026-09-08

"""

from alembic import op
import sqlalchemy as sa


revision = "s5t6u7v8w9"
down_revision = "r4s5t6u7v8"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_person_profiles",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("job_title", sa.Text(), nullable=True),
        sa.Column("phone_e164", sa.Text(), nullable=True),
        sa.Column("mobile_e164", sa.Text(), nullable=True),
        sa.Column("whatsapp_e164", sa.Text(), nullable=True),
        sa.Column("photo_storage_key", sa.Text(), nullable=True),
        sa.Column("photo_file_name", sa.Text(), nullable=True),
        sa.Column("photo_content_type", sa.Text(), nullable=True),
        sa.Column("photo_byte_size", sa.Integer(), nullable=True),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )


def downgrade():
    op.drop_table("user_person_profiles")
