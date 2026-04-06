from __future__ import annotations

import json

from app.domain.ports.strategic_indicators.settings_audit_repository_port import (
    StrategicIndicatorsSettingsAuditRepositoryPort,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class PostgresStrategicIndicatorsSettingsAuditRepository(
    PluginBaseRepository,
    StrategicIndicatorsSettingsAuditRepositoryPort,
):
    def insert_audit_event(
        self,
        *,
        entity_key: str,
        payload_before: dict | None,
        payload_after: dict | None,
        changed_by_user_id: str | None,
        changed_by_email: str | None,
    ) -> None:
        query = """
            INSERT INTO strategic_indicators.settings_audit (
                event_type,
                entity_key,
                payload_before,
                payload_after,
                changed_by_user_id,
                changed_by_email
            )
            VALUES (%s, %s, %s::jsonb, %s::jsonb, %s, %s)
        """

        self.execute(
            query,
            (
                "settings.updated",
                entity_key,
                json.dumps(payload_before, ensure_ascii=False)
                if payload_before is not None
                else None,
                json.dumps(payload_after, ensure_ascii=False)
                if payload_after is not None
                else None,
                changed_by_user_id,
                changed_by_email,
            ),
        )

    def list_recent_events(
        self,
        limit: int = 20,
        entity_key: str | None = None,
    ) -> list[dict]:
        base_query = """
            SELECT
                id,
                event_type,
                entity_key,
                payload_before,
                payload_after,
                changed_by_user_id,
                changed_by_email,
                created_at
            FROM strategic_indicators.settings_audit
        """

        params = []
        conditions = []

        if entity_key:
            conditions.append("entity_key = %s")
            params.append(entity_key)

        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)

        base_query += """
            ORDER BY created_at DESC
            LIMIT %s
        """
        params.append(limit)

        return self.fetch_all(base_query, tuple(params))