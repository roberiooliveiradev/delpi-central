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
            SELECT payload_json
            FROM strategic_indicators.module_settings
            WHERE is_active = TRUE
              AND setting_key = 'indicators.catalog'
            LIMIT 1
        """

        row = self.fetch_one(query)

        if row is None:
            return []

        payload = row.get("payload_json") or {}
        return payload.get("items", [])