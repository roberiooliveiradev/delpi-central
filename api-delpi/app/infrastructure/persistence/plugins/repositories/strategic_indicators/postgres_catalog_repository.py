from __future__ import annotations

from app.application.dto.strategic_indicators.catalog_models import (
    StrategicDepartmentCatalogItem,
    StrategicIndicatorCatalogItem,
)
from app.domain.ports.strategic_indicators.departments_catalog_repository_port import (
    StrategicIndicatorsDepartmentsCatalogRepositoryPort,
)
from app.domain.ports.strategic_indicators.indicators_catalog_repository_port import (
    StrategicIndicatorsIndicatorsCatalogRepositoryPort,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class PostgresStrategicIndicatorsCatalogRepository(
    PluginBaseRepository,
    StrategicIndicatorsDepartmentsCatalogRepositoryPort,
    StrategicIndicatorsIndicatorsCatalogRepositoryPort,
):
    def list_departments_catalog(self) -> list[StrategicDepartmentCatalogItem]:
        catalog = self._load_indicators_catalog_payload()
        items = catalog.get("items", [])

        return [
            StrategicDepartmentCatalogItem(
                department_id=item["department_id"],
                department_name=item["department_name"],
                short_name=item.get("short_name", item["department_name"][:3].upper()),
                weight_pct=float(item.get("department_weight_pct", 0)),
                strategic_summary=item.get("strategic_summary", ""),
                aggregation_mode=item.get("aggregation_mode", "consolidated"),
            )
            for item in items
        ]

    def list_indicators_catalog(self) -> list[StrategicIndicatorCatalogItem]:
        catalog = self._load_indicators_catalog_payload()
        items = catalog.get("items", [])

        flattened: list[StrategicIndicatorCatalogItem] = []

        for department in items:
            department_id = department["department_id"]

            for indicator in department.get("indicators", []):
                flattened.append(
                    StrategicIndicatorCatalogItem(
                        indicator_id=indicator["id"],
                        department_id=department_id,
                        indicator_name=indicator["name"],
                        weight_pct=float(indicator["weight_pct"]),
                        goal_label=indicator["goal_label"],
                        goal_value=float(indicator["goal_value"]),
                        goal_periodicity=indicator.get("goal_periodicity", "monthly"),
                        scope_type=indicator.get("scope_type", "consolidated"),
                        strategic_description=indicator.get(
                            "strategic_description",
                            "",
                        ),
                        source_key=indicator.get("source_key"),
                    )
                )

        return flattened

    def list_indicators_catalog_by_department(
        self,
        department_id: str,
    ) -> list[StrategicIndicatorCatalogItem]:
        return [
            item
            for item in self.list_indicators_catalog()
            if item.department_id == department_id
        ]

    def get_department_goal_summary(self) -> dict[str, str]:
        sql = """
            SELECT payload_json
            FROM strategic_indicators.module_settings
            WHERE setting_key = %s
              AND setting_group = %s
              AND is_active = TRUE
            LIMIT 1
        """
        row = self.fetch_one(sql, ("goals.summary", "goals"))
        payload = row["payload_json"] if row else {}
        items = payload.get("items", [])

        return {
            item["department_id"]: item.get("headline_goal", "")
            for item in items
        }

    def _load_indicators_catalog_payload(self) -> dict:
        sql = """
            SELECT payload_json
            FROM strategic_indicators.module_settings
            WHERE setting_key = %s
              AND setting_group = %s
              AND is_active = TRUE
            LIMIT 1
        """
        row = self.fetch_one(sql, ("indicators.catalog", "indicators"))
        if not row:
            return {"items": []}
        return row["payload_json"] or {"items": []}