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
