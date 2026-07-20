from __future__ import annotations

from datetime import datetime
from typing import Any

from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)

ALLOWED_ENTITY_TYPES = frozenset(
    {
        "processo",
        "processo_instancia",
        "revisao",
        "filial",
        "setor",
        "recurso",
        # Salas de listagem / dashboard (sem locks de edição colaborativa)
        "catalog",
    }
)
PRESENCE_TTL_SECONDS = 45
LOCK_TTL_SECONDS = 90


class CollaborationPresenceRepository(PluginBaseRepository):
    def purge_stale(self, *, ttl_seconds: int = PRESENCE_TTL_SECONDS) -> None:
        self.execute(
            """
            DELETE FROM transformometro.collaboration_presence
            WHERE heartbeat_at < NOW() - (%s * INTERVAL '1 second')
            """,
            (ttl_seconds,),
        )

    def upsert_presence(
        self,
        *,
        entity_type: str,
        entity_id: str,
        section_key: str,
        user_id: str,
        user_name: str | None,
        user_email: str | None,
        mode: str,
        lock_expires_at: datetime | None,
    ) -> dict[str, Any]:
        row = self.execute_returning_one(
            """
            INSERT INTO transformometro.collaboration_presence (
                entity_type,
                entity_id,
                section_key,
                user_id,
                user_name,
                user_email,
                mode,
                heartbeat_at,
                lock_expires_at
            ) VALUES (
                %s, %s::uuid, %s, %s, %s, %s, %s, NOW(), %s
            )
            ON CONFLICT (entity_type, entity_id, section_key, user_id) DO UPDATE SET
                user_name = EXCLUDED.user_name,
                user_email = EXCLUDED.user_email,
                mode = EXCLUDED.mode,
                heartbeat_at = NOW(),
                lock_expires_at = EXCLUDED.lock_expires_at
            RETURNING
                presence_id,
                entity_type,
                entity_id,
                section_key,
                user_id,
                user_name,
                user_email,
                mode,
                heartbeat_at,
                lock_expires_at
            """,
            (
                entity_type,
                entity_id,
                section_key,
                user_id,
                user_name,
                user_email,
                mode,
                lock_expires_at,
            ),
        )
        return row or {}

    def list_active(
        self,
        *,
        entity_type: str,
        entity_id: str,
        ttl_seconds: int = PRESENCE_TTL_SECONDS,
    ) -> list[dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT
                presence_id,
                entity_type,
                entity_id,
                section_key,
                user_id,
                user_name,
                user_email,
                mode,
                heartbeat_at,
                lock_expires_at
            FROM transformometro.collaboration_presence
            WHERE entity_type = %s
              AND entity_id = %s::uuid
              AND heartbeat_at >= NOW() - (%s * INTERVAL '1 second')
            ORDER BY heartbeat_at DESC
            """,
            (entity_type, entity_id, ttl_seconds),
        )

    def get_active_lock_holder(
        self,
        *,
        entity_type: str,
        entity_id: str,
        section_key: str,
        exclude_user_id: str | None = None,
    ) -> dict[str, Any] | None:
        params: list[Any] = [entity_type, entity_id, section_key]
        exclude_clause = ""
        if exclude_user_id:
            exclude_clause = "AND user_id <> %s"
            params.append(exclude_user_id)
        return self.fetch_one(
            f"""
            SELECT
                presence_id,
                user_id,
                user_name,
                user_email,
                section_key,
                lock_expires_at
            FROM transformometro.collaboration_presence
            WHERE entity_type = %s
              AND entity_id = %s::uuid
              AND section_key = %s
              AND mode = 'editing'
              AND lock_expires_at IS NOT NULL
              AND lock_expires_at > NOW()
              {exclude_clause}
            ORDER BY lock_expires_at DESC
            LIMIT 1
            """,
            tuple(params),
        )

    def delete_user_presence(
        self,
        *,
        entity_type: str,
        entity_id: str,
        user_id: str,
    ) -> None:
        self.execute(
            """
            DELETE FROM transformometro.collaboration_presence
            WHERE entity_type = %s
              AND entity_id = %s::uuid
              AND user_id = %s
            """,
            (entity_type, entity_id, user_id),
        )

    def release_user_locks(
        self,
        *,
        entity_type: str,
        entity_id: str,
        user_id: str,
        section_key: str | None = None,
    ) -> None:
        if section_key is not None:
            self.execute(
                """
                UPDATE transformometro.collaboration_presence
                SET mode = 'viewing', lock_expires_at = NULL, heartbeat_at = NOW()
                WHERE entity_type = %s
                  AND entity_id = %s::uuid
                  AND section_key = %s
                  AND user_id = %s
                """,
                (entity_type, entity_id, section_key, user_id),
            )
            return
        self.execute(
            """
            UPDATE transformometro.collaboration_presence
            SET mode = 'viewing', lock_expires_at = NULL, heartbeat_at = NOW()
            WHERE entity_type = %s
              AND entity_id = %s::uuid
              AND user_id = %s
            """,
            (entity_type, entity_id, user_id),
        )
