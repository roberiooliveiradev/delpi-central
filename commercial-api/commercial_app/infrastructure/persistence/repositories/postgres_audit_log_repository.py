from __future__ import annotations

import json
from typing import Any

from commercial_app.domain.ports.customer_avatar_repository_port import AuditLogRepositoryPort
from commercial_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class PostgresAuditLogRepository(PluginBaseRepository, AuditLogRepositoryPort):
    def append(
        self,
        *,
        actor_user_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        payload: dict[str, Any],
    ) -> None:
        self.execute(
            """
            INSERT INTO commercial.audit_log (
                actor_user_id, action, entity_type, entity_id, payload
            ) VALUES (%s, %s, %s, %s, %s::jsonb)
            """,
            (
                actor_user_id,
                action,
                entity_type,
                entity_id,
                json.dumps(payload or {}),
            ),
        )

    def list_for_entity(
        self,
        *,
        entity_type: str,
        entity_id: str,
        page: int = 1,
        page_size: int = 20,
        related_target_key: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        safe_page = max(1, int(page or 1))
        safe_size = min(100, max(1, int(page_size or 20)))
        offset = (safe_page - 1) * safe_size

        if related_target_key:
            where = """
                entity_type = %s
                AND (
                    entity_id = %s
                    OR COALESCE(payload->>%s, '') = %s
                )
            """
            params_base: tuple[Any, ...] = (
                entity_type,
                entity_id,
                related_target_key,
                entity_id,
            )
        else:
            where = "entity_type = %s AND entity_id = %s"
            params_base = (entity_type, entity_id)

        count_row = self.fetch_one(
            f"SELECT COUNT(*)::int AS total FROM commercial.audit_log WHERE {where}",
            params_base,
        )
        total = int((count_row or {}).get("total") or 0)

        rows = self.fetch_all(
            f"""
            SELECT
                id::text AS id,
                actor_user_id,
                action,
                entity_type,
                entity_id,
                payload,
                created_at
            FROM commercial.audit_log
            WHERE {where}
            ORDER BY created_at DESC, id DESC
            LIMIT %s OFFSET %s
            """,
            (*params_base, safe_size, offset),
        )
        return rows, total
