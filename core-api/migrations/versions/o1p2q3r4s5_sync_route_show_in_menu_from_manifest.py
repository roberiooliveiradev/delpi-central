"""sync app_routes.show_in_menu from saved plugin manifests

Revision ID: o1p2q3r4s5
Revises: n0o1p2q3r4
Create Date: 2026-06-12

"""

from alembic import op


revision = "o1p2q3r4s5"
down_revision = "n0o1p2q3r4"
branch_labels = None
depends_on = None


def upgrade():
    # Corrige divergência quando register inicial gravou show_in_menu=true
    # ignorando showInMenu camelCase do manifesto.
    op.execute(
        """
        UPDATE app_routes AS ar
        SET show_in_menu = sub.show_in_menu
        FROM (
            SELECT
                am.app_id,
                route_elem->>'path' AS path,
                COALESCE((route_elem->>'showInMenu')::boolean, true) AS show_in_menu
            FROM app_manifests am,
                 json_array_elements(am.manifest->'routes') AS route_elem
            WHERE route_elem->>'showInMenu' IS NOT NULL
        ) AS sub
        WHERE ar.app_id = sub.app_id
          AND ar.path = sub.path
          AND ar.show_in_menu IS DISTINCT FROM sub.show_in_menu
        """
    )


def downgrade():
    pass
