from __future__ import annotations

from typing import Any
from uuid import UUID

from app.infrastructure.persistence.migrations_runner import get_connection


class PreferencesRepository:
    def get(self, user_id: UUID) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT user_id, keycloak_sub, default_branch, table_density,
                           created_at, updated_at
                    FROM supplies.supply_user_preferences
                    WHERE user_id = %s
                    """,
                    (str(user_id),),
                )
                row = cur.fetchone()
        return dict(row) if row else None

    def upsert(
        self,
        *,
        user_id: UUID,
        keycloak_sub: str | None,
        default_branch: str | None,
        table_density: str,
    ) -> dict[str, Any]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO supplies.supply_user_preferences (
                        user_id, keycloak_sub, default_branch, table_density
                    ) VALUES (%s, %s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        keycloak_sub = COALESCE(EXCLUDED.keycloak_sub, supplies.supply_user_preferences.keycloak_sub),
                        default_branch = EXCLUDED.default_branch,
                        table_density = EXCLUDED.table_density,
                        updated_at = NOW()
                    RETURNING user_id, keycloak_sub, default_branch, table_density,
                              created_at, updated_at
                    """,
                    (str(user_id), keycloak_sub, default_branch, table_density),
                )
                row = cur.fetchone()
            conn.commit()
        return dict(row)
