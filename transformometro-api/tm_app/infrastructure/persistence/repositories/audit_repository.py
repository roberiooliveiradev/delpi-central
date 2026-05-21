from __future__ import annotations

import json
from typing import Any

from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class AuditRepository(PluginBaseRepository):
    def log(
        self,
        *,
        entity_type: str,
        entity_id: str,
        action: str,
        user_id: str | None,
        user_email: str | None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self.execute(
            """
            INSERT INTO transformometro.audit_logs (
                entity_type, entity_id, action, user_id, user_email, payload_json
            ) VALUES (%s, %s, %s, %s, %s, %s::jsonb)
            """,
            (
                entity_type,
                entity_id,
                action,
                user_id,
                user_email,
                json.dumps(payload or {}, default=str),
            ),
        )
