from __future__ import annotations

from app.domain.ports.strategic_indicators.summary_settings_port import (
    StrategicIndicatorsSummarySettingsPort,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class PostgresStrategicIndicatorsSummarySettingsRepository(
    PluginBaseRepository,
    StrategicIndicatorsSummarySettingsPort,
):
    def get_summary_settings(self) -> dict:
        query = """
            SELECT
                setting_key,
                payload_json
            FROM strategic_indicators.module_settings
            WHERE is_active = TRUE
              AND setting_key IN (
                'weights.departments',
                'goals.summary',
                'parameters.global',
                'governance.notes',
                'indicators.catalog'
              )
        """

        rows = self.fetch_all(query)

        result = {
            "weights": {"items": []},
            "goals": {"items": []},
            "parameters": {"items": []},
            "governance": {"items": []},
            "indicators": {"items": []},
        }

        for row in rows:
            setting_key = row["setting_key"]
            payload = row.get("payload_json") or {"items": []}

            if setting_key == "weights.departments":
                result["weights"] = payload
            elif setting_key == "goals.summary":
                result["goals"] = payload
            elif setting_key == "parameters.global":
                result["parameters"] = payload
            elif setting_key == "governance.notes":
                result["governance"] = payload
            elif setting_key == "indicators.catalog":
                result["indicators"] = payload

        return result