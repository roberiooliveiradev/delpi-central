from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any

from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)
from app.infrastructure.persistence.plugins.repositories.quality_labels.postgres_quality_labels_repository import (
    unit_name,
)

_COLUMNS = (
    "id, event_type, label_id, production_order, product_code, branch, result, "
    "actor_user_id, actor_name, detail, created_at"
)


class PostgresQualityLabelsAuditRepository(PluginBaseRepository):
    """Trilha de auditoria do módulo de Etiquetas da Qualidade."""

    def insert_event(
        self,
        *,
        event_type: str,
        label_id: str | None = None,
        production_order: str | None = None,
        product_code: str | None = None,
        branch: str | None = None,
        result: str | None = None,
        actor_user_id: str | None = None,
        actor_name: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        self.execute(
            """
            INSERT INTO quality_labels.audit_events (
                event_type, label_id, production_order, product_code, branch,
                result, actor_user_id, actor_name, detail
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
            """,
            (
                event_type,
                label_id,
                production_order,
                product_code,
                branch,
                result,
                actor_user_id,
                actor_name,
                json.dumps(detail or {}),
            ),
        )

    def list_events(
        self,
        *,
        search: str | None,
        event_types: list[str] | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        clauses: list[str] = []
        params: list[Any] = []
        if search:
            clauses.append(
                "(production_order ILIKE %s OR product_code ILIKE %s "
                "OR actor_name ILIKE %s OR event_type ILIKE %s)"
            )
            like = f"%{search}%"
            params.extend([like, like, like, like])
        if event_types:
            placeholders = ",".join(["%s"] * len(event_types))
            clauses.append(f"event_type IN ({placeholders})")
            params.extend(event_types)

        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""

        total_row = self.fetch_one(
            f"SELECT COUNT(*) AS total FROM quality_labels.audit_events{where}",
            tuple(params),
        )
        total = int(total_row["total"]) if total_row else 0

        rows = self.fetch_all(
            f"""
            SELECT {_COLUMNS}
              FROM quality_labels.audit_events{where}
             ORDER BY created_at DESC
             LIMIT %s OFFSET %s
            """,
            tuple(params + [limit, offset]),
        )
        return rows, total

    def count_by_type(self) -> dict[str, int]:
        rows = self.fetch_all(
            """
            SELECT event_type, COUNT(*) AS total
              FROM quality_labels.audit_events
             GROUP BY event_type
            """
        )
        return {str(row["event_type"]): int(row["total"]) for row in rows}

    @staticmethod
    def _iso(value: Any) -> Any:
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        return value

    @staticmethod
    def _detail(row: dict[str, Any]) -> dict[str, Any]:
        raw = row.get("detail")
        if isinstance(raw, dict):
            return raw
        if isinstance(raw, str):
            try:
                parsed = json.loads(raw)
                return parsed if isinstance(parsed, dict) else {}
            except json.JSONDecodeError:
                return {}
        return {}

    @classmethod
    def to_payload(cls, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": str(row.get("id")),
            "eventType": row.get("event_type"),
            "labelId": str(row["label_id"]) if row.get("label_id") else None,
            "productionOrder": row.get("production_order"),
            "productCode": row.get("product_code"),
            "branch": row.get("branch"),
            "branchName": unit_name(row.get("branch")),
            "result": row.get("result"),
            "actorUserId": row.get("actor_user_id"),
            "actorName": row.get("actor_name"),
            "detail": cls._detail(row),
            "createdAt": cls._iso(row.get("created_at")),
        }
