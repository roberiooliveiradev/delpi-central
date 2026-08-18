"""List SLA policies (may be empty until homologated)."""

from __future__ import annotations

from commercial_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class PostgresSlaPolicyRepository(PluginBaseRepository):
    def list_active(self) -> list[dict]:
        rows = self.fetch_all(
            """
            SELECT id, code, name, applies_to, duration_hours, calendar_code, active
              FROM commercial.sla_policies
             WHERE active = TRUE
             ORDER BY code
            """,
        )
        return [
            {
                "id": str(row["id"]),
                "code": row["code"],
                "name": row["name"],
                "appliesTo": row["applies_to"],
                "durationHours": int(row["duration_hours"]),
                "calendarCode": row.get("calendar_code"),
                "active": bool(row["active"]),
            }
            for row in rows
        ]
