from __future__ import annotations

from app.domain.ports.strategic_indicators.departments_catalog_port import (
    StrategicIndicatorsDepartmentsCatalogPort,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class PostgresStrategicIndicatorsDepartmentsCatalogRepository(
    PluginBaseRepository,
    StrategicIndicatorsDepartmentsCatalogPort,
):
    def get_departments_catalog(self) -> list[dict]:
        query = """
            SELECT
                department_id,
                department_name,
                short_name,
                strategic_summary,
                headline_goal,
                supporting_focus,
                weight_pct,
                aggregation_mode,
                is_active,
                display_order
            FROM strategic_indicators.departments
            WHERE is_active = TRUE
            ORDER BY display_order ASC, department_name ASC
        """

        rows = self.fetch_all(query)

        return [
            {
                "department_id": row["department_id"],
                "department_name": row["department_name"],
                "short_name": row["short_name"],
                "strategic_summary": row.get("strategic_summary") or "",
                "headline_goal": row.get("headline_goal") or "",
                "supporting_focus": row.get("supporting_focus") or "",
                "weight_pct": float(row.get("weight_pct") or 0),
                "aggregation_mode": row.get("aggregation_mode") or "consolidated",
                "is_active": bool(row.get("is_active", True)),
                "display_order": int(row.get("display_order") or 0),
            }
            for row in rows
        ]