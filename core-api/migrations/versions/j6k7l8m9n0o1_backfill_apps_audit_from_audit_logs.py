"""backfill apps audit columns from audit_logs

Revision ID: j6k7l8m9n0o1
Revises: i5j6k7l8m9n0
Create Date: 2026-05-21

"""

from alembic import op


revision = "j6k7l8m9n0o1"
down_revision = "i5j6k7l8m9n0"
branch_labels = None
depends_on = None


def upgrade():
    # Normaliza auditoria de plugins/apps (entity_id direto ou payload JSON).
    op.execute(
        """
        WITH plugin_audit_rows AS (
            SELECT
                COALESCE(
                    al.entity_id,
                    al.payload->>'pluginId',
                    al.payload->>'appId'
                ) AS app_id,
                al.user_id,
                al.action,
                al.created_at,
                al.id
            FROM audit_logs al
            WHERE al.entity_type IN ('plugins', 'apps')
              AND COALESCE(
                    al.entity_id,
                    al.payload->>'pluginId',
                    al.payload->>'appId'
                  ) IS NOT NULL

            UNION ALL

            SELECT
                ids.app_id,
                al.user_id,
                al.action,
                al.created_at,
                al.id
            FROM audit_logs al
            CROSS JOIN LATERAL jsonb_array_elements_text(
                COALESCE(al.payload::jsonb->'ids', '[]'::jsonb)
            ) AS ids(app_id)
            WHERE al.entity_type = 'plugins'
              AND al.action = 'plugins_activation_changed'
              AND ids.app_id IS NOT NULL
              AND ids.app_id <> ''
        ),
        first_touch AS (
            SELECT DISTINCT ON (app_id)
                app_id,
                user_id,
                created_at
            FROM plugin_audit_rows
            WHERE user_id IS NOT NULL
            ORDER BY app_id, created_at ASC, id ASC
        ),
        last_touch AS (
            SELECT DISTINCT ON (app_id)
                app_id,
                user_id,
                created_at
            FROM plugin_audit_rows
            WHERE user_id IS NOT NULL
            ORDER BY app_id, created_at DESC, id ASC
        )
        UPDATE apps AS a
        SET
            created_by_user_id = COALESCE(a.created_by_user_id, ft.user_id),
            created_by_email = COALESCE(a.created_by_email, cu.email),
            updated_by_user_id = COALESCE(a.updated_by_user_id, lt.user_id),
            updated_by_email = COALESCE(a.updated_by_email, uu.email)
        FROM first_touch ft
        LEFT JOIN last_touch lt ON lt.app_id = ft.app_id
        LEFT JOIN users cu ON cu.id = ft.user_id
        LEFT JOIN users uu ON uu.id = lt.user_id
        WHERE a.id = ft.app_id
          AND (
            a.created_by_user_id IS NULL
            OR a.created_by_email IS NULL
            OR a.updated_by_user_id IS NULL
            OR a.updated_by_email IS NULL
          )
        """
    )


def downgrade():
    pass
