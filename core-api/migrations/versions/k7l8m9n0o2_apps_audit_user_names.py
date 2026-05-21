"""apps audit user names (display)

Revision ID: k7l8m9n0o2
Revises: j6k7l8m9n0o1
Create Date: 2026-05-21

"""

from alembic import op
import sqlalchemy as sa


revision = "k7l8m9n0o2"
down_revision = "j6k7l8m9n0o1"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "apps",
        sa.Column("created_by_name", sa.String(length=150), nullable=True),
    )
    op.add_column(
        "apps",
        sa.Column("updated_by_name", sa.String(length=150), nullable=True),
    )

    op.execute(
        """
        UPDATE apps AS a
        SET created_by_name = u.name
        FROM users AS u
        WHERE a.created_by_user_id = u.id
          AND a.created_by_name IS NULL
        """
    )

    op.execute(
        """
        UPDATE apps AS a
        SET updated_by_name = u.name
        FROM users AS u
        WHERE a.updated_by_user_id = u.id
          AND a.updated_by_name IS NULL
        """
    )

    op.execute(
        """
        UPDATE apps AS a
        SET created_by_name = u.name
        FROM users AS u
        WHERE a.created_by_name IS NULL
          AND a.created_by_email IS NOT NULL
          AND lower(a.created_by_email) = lower(u.email)
        """
    )

    op.execute(
        """
        UPDATE apps AS a
        SET updated_by_name = u.name
        FROM users AS u
        WHERE a.updated_by_name IS NULL
          AND a.updated_by_email IS NOT NULL
          AND lower(a.updated_by_email) = lower(u.email)
        """
    )


def downgrade():
    op.drop_column("apps", "updated_by_name")
    op.drop_column("apps", "created_by_name")
