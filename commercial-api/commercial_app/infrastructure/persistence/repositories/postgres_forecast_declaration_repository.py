from __future__ import annotations

from datetime import datetime, timezone

from commercial_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class PostgresForecastDeclarationRepository(PluginBaseRepository):
    def get(
        self,
        *,
        cycle_year: int,
        cycle_month: int,
        portfolio_id: str,
    ) -> dict | None:
        row = self.fetch_one(
            """
            SELECT cycle_year, cycle_month, portfolio_id, declared_value,
                   updated_by, updated_at
              FROM commercial.forecast_declarations
             WHERE cycle_year = %s AND cycle_month = %s AND portfolio_id = %s
            """,
            (cycle_year, cycle_month, portfolio_id),
        )
        if not row:
            return None
        return self._to_public(row)

    def upsert(
        self,
        *,
        cycle_year: int,
        cycle_month: int,
        portfolio_id: str,
        declared_value: float,
        updated_by: str,
    ) -> dict:
        now = datetime.now(timezone.utc)
        self.execute(
            """
            INSERT INTO commercial.forecast_declarations (
                cycle_year, cycle_month, portfolio_id, declared_value, updated_by, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (cycle_year, cycle_month, portfolio_id)
            DO UPDATE SET
                declared_value = EXCLUDED.declared_value,
                updated_by = EXCLUDED.updated_by,
                updated_at = EXCLUDED.updated_at
            """,
            (cycle_year, cycle_month, portfolio_id, declared_value, updated_by, now),
        )
        return {
            "cycleYear": cycle_year,
            "cycleMonth": cycle_month,
            "portfolioId": portfolio_id,
            "declaredValue": declared_value,
            "updatedBy": updated_by,
            "updatedAt": now.isoformat(),
        }

    def _to_public(self, row: dict) -> dict:
        updated = row.get("updated_at")
        return {
            "cycleYear": int(row["cycle_year"]),
            "cycleMonth": int(row["cycle_month"]),
            "portfolioId": str(row.get("portfolio_id") or ""),
            "declaredValue": float(row.get("declared_value") or 0),
            "updatedBy": str(row.get("updated_by") or ""),
            "updatedAt": updated.isoformat() if hasattr(updated, "isoformat") else str(updated or ""),
        }
