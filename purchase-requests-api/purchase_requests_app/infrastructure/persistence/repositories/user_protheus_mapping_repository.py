from __future__ import annotations

from typing import Any

from purchase_requests_app.infrastructure.persistence.plugins_postgres_connection import (
    plugins_connection,
)


class UserProtheusMappingRepository:
    def get_mapping(self, user_id: str) -> dict[str, Any] | None:
        sql = """
        SELECT user_id, protheus_user_id, protheus_user_code, mapping_status,
               mapping_source, verified, created_at, updated_at
        FROM purchase_requests.user_protheus_mappings
        WHERE user_id = %s
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (user_id,))
                row = cur.fetchone()
        return dict(row) if row else None

    def upsert_mapping(
        self,
        *,
        user_id: str,
        protheus_user_id: str | None,
        protheus_user_code: str | None,
        mapping_status: str,
        mapping_source: str | None,
        verified: bool,
    ) -> dict[str, Any]:
        sql = """
        INSERT INTO purchase_requests.user_protheus_mappings
            (user_id, protheus_user_id, protheus_user_code, mapping_status, mapping_source, verified)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE SET
            protheus_user_id = EXCLUDED.protheus_user_id,
            protheus_user_code = EXCLUDED.protheus_user_code,
            mapping_status = EXCLUDED.mapping_status,
            mapping_source = EXCLUDED.mapping_source,
            verified = EXCLUDED.verified,
            updated_at = NOW()
        RETURNING user_id, protheus_user_id, protheus_user_code, mapping_status,
                  mapping_source, verified, created_at, updated_at
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    (
                        user_id,
                        protheus_user_id,
                        protheus_user_code,
                        mapping_status,
                        mapping_source,
                        verified,
                    ),
                )
                row = cur.fetchone()
            conn.commit()
        return dict(row)

    def get_mapping_by_protheus_user_id(
        self,
        protheus_user_id: str,
    ) -> dict[str, Any] | None:
        normalized = (protheus_user_id or "").strip()
        if not normalized:
            return None
        sql = """
        SELECT user_id, protheus_user_id, protheus_user_code, mapping_status,
               mapping_source, verified, created_at, updated_at
        FROM purchase_requests.user_protheus_mappings
        WHERE mapping_status = 'mapped'
          AND BTRIM(protheus_user_id) = %s
        LIMIT 1
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (normalized,))
                row = cur.fetchone()
        return dict(row) if row else None

    def list_mappings(self) -> list[dict[str, Any]]:
        sql = """
        SELECT user_id, protheus_user_id, protheus_user_code, mapping_status,
               mapping_source, verified, created_at, updated_at
        FROM purchase_requests.user_protheus_mappings
        ORDER BY updated_at DESC
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()
        return [dict(row) for row in rows]
