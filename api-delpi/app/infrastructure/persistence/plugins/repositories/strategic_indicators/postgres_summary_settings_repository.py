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
        result = {
            "weights": {"items": []},
            "goals": {"items": []},
            "parameters": {"items": []},
            "governance": {"items": []},
            "indicators": {"items": []},
        }

        departments = self.fetch_all(
            """
            SELECT
                department_id,
                department_name,
                short_name,
                strategic_summary,
                headline_goal,
                supporting_focus,
                weight_pct,
                aggregation_mode,
                display_order
            FROM strategic_indicators.departments
            WHERE is_active = TRUE
            ORDER BY display_order ASC, department_name ASC
            """
        )

        indicators = self.fetch_all(
            """
            SELECT
                indicator_id,
                department_id,
                indicator_name,
                weight_pct,
                scope_type,
                strategic_description,
                source_key,
                display_order
            FROM strategic_indicators.department_indicators
            WHERE is_active = TRUE
            ORDER BY department_id ASC, display_order ASC, indicator_name ASC
            """
        )

        settings_rows = self.fetch_all(
            """
            SELECT
                setting_key,
                payload_json
            FROM strategic_indicators.module_settings
            WHERE is_active = TRUE
              AND setting_key IN (
                'parameters.global',
                'governance.notes'
              )
            """
        )

        result["weights"] = {
            "items": [
                {
                    "department_id": row["department_id"],
                    "department_name": row["department_name"],
                    "weight_pct": float(row.get("weight_pct") or 0),
                }
                for row in departments
            ]
        }

        result["goals"] = {
            "items": [
                {
                    "department_id": row["department_id"],
                    "department_name": row["department_name"],
                    "headline_goal": row.get("headline_goal") or "",
                    "supporting_focus": row.get("supporting_focus") or "",
                }
                for row in departments
            ]
        }

        indicators_by_department: dict[str, list[dict]] = {}
        for row in indicators:
            indicators_by_department.setdefault(row["department_id"], []).append(
                {
                    "id": row["indicator_id"],
                    "name": row["indicator_name"],
                    "weight_pct": float(row.get("weight_pct") or 0),
                    "scope_type": row.get("scope_type") or "consolidated",
                    "strategic_description": row.get("strategic_description") or "",
                    "source_key": row.get("source_key"),
                }
            )

        result["indicators"] = {
            "items": [
                {
                    "department_id": row["department_id"],
                    "department_name": row["department_name"],
                    "short_name": row["short_name"],
                    "department_weight_pct": float(row.get("weight_pct") or 0),
                    "aggregation_mode": row.get("aggregation_mode") or "consolidated",
                    "strategic_summary": row.get("strategic_summary") or "",
                    "indicators": indicators_by_department.get(row["department_id"], []),
                }
                for row in departments
            ]
        }

        for row in settings_rows:
            setting_key = row["setting_key"]
            payload = row.get("payload_json") or {"items": []}

            if setting_key == "parameters.global":
                result["parameters"] = payload
            elif setting_key == "governance.notes":
                result["governance"] = payload

        return result