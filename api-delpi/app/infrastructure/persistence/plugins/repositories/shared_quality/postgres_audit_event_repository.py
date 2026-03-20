# app/infrastructure/persistence/plugins/repositories/shared_quality/postgres_audit_event_repository.py
from __future__ import annotations

from typing import Any

from app.domain.entities.shared_quality.nonconformity_audit_event import (
    NonconformityAuditEvent,
)
from app.domain.ports.shared_quality.audit_event_repository import (
    AuditEventRepositoryPort,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class PostgresAuditEventRepository(
    PluginBaseRepository,
    AuditEventRepositoryPort,
):
    def create(self, event: NonconformityAuditEvent) -> NonconformityAuditEvent:
        row = self.execute_returning_one(
            """
            INSERT INTO quality.external_nc_audit_events (
                id,
                nonconformity_id,
                event_type,
                actor_user_id,
                payload_json,
                created_at
            ) VALUES (%s, %s, %s, %s, %s::jsonb, %s)
            RETURNING
                id,
                nonconformity_id,
                event_type,
                actor_user_id,
                payload_json,
                created_at
            """,
            (
                event.id,
                event.entity_id,
                event.event_type,
                event.actor_user_id,
                self._to_json(event.payload_json),
                event.created_at,
            ),
            auto_commit=True,
        )

        return self._to_entity(row)

    def _to_entity(self, row: dict[str, Any]) -> NonconformityAuditEvent:
        return NonconformityAuditEvent(
            id=str(row["id"]),
            entity_type="external_nonconformity",
            entity_id=str(row["nonconformity_id"]),
            event_type=row["event_type"],
            actor_user_id=row.get("actor_user_id"),
            payload_json=row.get("payload_json"),
            created_at=row["created_at"],
        )

    def _to_json(self, payload: dict[str, Any] | None) -> str | None:
        if payload is None:
            return None

        import json
        return json.dumps(payload, ensure_ascii=False, default=str)