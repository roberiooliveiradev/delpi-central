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
        sql = """
            SELECT
                department_id,
                department_name,
                short_name,
                weight_pct,
                strategic_summary,
                aggregation_mode
            FROM strategic_indicators.departments
            WHERE is_active = TRUE
            ORDER BY display_order ASC, department_name ASC
        """
        rows = self.fetch_all(sql)

        return [
            StrategicDepartmentCatalogItem(
                department_id=row["department_id"],
                department_name=row["department_name"],
                short_name=row["short_name"],
                weight_pct=float(row.get("weight_pct") or 0),
                strategic_summary=row.get("strategic_summary") or "",
                aggregation_mode=row.get("aggregation_mode") or "consolidated",
            )
            for row in rows
        ]

    def list_indicators_catalog(self) -> list[StrategicIndicatorCatalogItem]:
        return self.list_structural_indicators_catalog()

    def list_structural_indicators_catalog(
        self,
        *,
        department_id: str | None = None,
    ) -> list[StrategicIndicatorCatalogItem]:
        sql = """
            SELECT
                di.indicator_id,
                di.department_id,
                di.indicator_name,
                di.weight_pct,
                di.scope_type,
                di.strategic_description,
                di.source_key
            FROM strategic_indicators.department_indicators di
            INNER JOIN strategic_indicators.departments d
                ON d.department_id = di.department_id
            WHERE di.is_active = TRUE
              AND d.is_active = TRUE
        """
        params: list = []

        if department_id:
            sql += " AND di.department_id = %s"
            params.append(department_id)

        sql += """
            ORDER BY
                d.display_order ASC,
                di.display_order ASC,
                di.indicator_name ASC
        """

        rows = self.fetch_all(sql, tuple(params))

        return [
            StrategicIndicatorCatalogItem(
                indicator_id=row["indicator_id"],
                department_id=row["department_id"],
                indicator_name=row["indicator_name"],
                weight_pct=float(row.get("weight_pct") or 0),
                goal_label="",
                goal_value=0.0,
                goal_periodicity="monthly",
                scope_type=row.get("scope_type") or "consolidated",
                strategic_description=row.get("strategic_description") or "",
                source_key=row.get("source_key"),
            )
            for row in rows
        ]

    def list_indicators_catalog_by_department(
        self,
        department_id: str,
    ) -> list[StrategicIndicatorCatalogItem]:
        return self.list_structural_indicators_catalog(department_id=department_id)

    def get_department_goal_summary(self) -> dict[str, str]:
        sql = """
            SELECT
                department_id,
                headline_goal
            FROM strategic_indicators.departments
            WHERE is_active = TRUE
            ORDER BY display_order ASC, department_name ASC
        """
        rows = self.fetch_all(sql)

        return {
            row["department_id"]: row.get("headline_goal") or ""
            for row in rows
        }