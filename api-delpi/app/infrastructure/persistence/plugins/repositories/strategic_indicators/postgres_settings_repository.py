from __future__ import annotations

import json

from app.domain.ports.strategic_indicators.settings_repository_port import (
    StrategicIndicatorsSettingsRepositoryPort,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class PostgresStrategicIndicatorsSettingsRepository(
    PluginBaseRepository, StrategicIndicatorsSettingsRepositoryPort
):
    def get_settings(self) -> dict:
        query = """
            SELECT
                setting_key,
                setting_group,
                payload_json,
                updated_at,
                updated_by_email
            FROM strategic_indicators.module_settings
            WHERE is_active = TRUE
            ORDER BY setting_group, setting_key
        """

        rows = self.fetch_all(query)

        settings_map = {
            "weights": {"items": []},
            "goals": {"items": []},
            "parameters": {"items": []},
            "governance": {"items": []},
        }

        latest_updated_at = None
        latest_updated_by_email = None

        for row in rows:
            setting_key = row["setting_key"]
            payload = row.get("payload_json") or {}

            if setting_key == "weights.departments":
                settings_map["weights"] = payload
            elif setting_key == "goals.summary":
                settings_map["goals"] = payload
            elif setting_key == "parameters.global":
                settings_map["parameters"] = payload
            elif setting_key == "governance.notes":
                settings_map["governance"] = payload

            row_updated_at = row.get("updated_at")
            if latest_updated_at is None or (
                row_updated_at is not None and row_updated_at > latest_updated_at
            ):
                latest_updated_at = row_updated_at
                latest_updated_by_email = row.get("updated_by_email")

        return {
            "weights": settings_map["weights"],
            "goals": settings_map["goals"],
            "parameters": settings_map["parameters"],
            "governance": settings_map["governance"],
            "meta": {
                "source": "postgres-plugins",
                "updated_at": latest_updated_at.isoformat() if latest_updated_at else None,
                "updated_by_email": latest_updated_by_email,
            },
        }

    def update_settings(
        self,
        *,
        weights: dict,
        goals: dict,
        parameters: dict,
        governance: dict,
        actor_user_id: str | None,
        actor_email: str | None,
    ) -> dict:
        query = """
            UPDATE strategic_indicators.module_settings
            SET
                payload_json = %s::jsonb,
                updated_by_user_id = %s,
                updated_by_email = %s,
                updated_at = NOW()
            WHERE setting_key = %s
        """

        try:
            self.execute(
                query,
                (
                    json.dumps(weights, ensure_ascii=False),
                    actor_user_id,
                    actor_email,
                    "weights.departments",
                ),
            )
            self.execute(
                query,
                (
                    json.dumps(goals, ensure_ascii=False),
                    actor_user_id,
                    actor_email,
                    "goals.summary",
                ),
            )
            self.execute(
                query,
                (
                    json.dumps(parameters, ensure_ascii=False),
                    actor_user_id,
                    actor_email,
                    "parameters.global",
                ),
            )
            self.execute(
                query,
                (
                    json.dumps(governance, ensure_ascii=False),
                    actor_user_id,
                    actor_email,
                    "governance.notes",
                ),
            )

            self.commit()

            return {
                "message": "Configurações do Strategic Indicators atualizadas com sucesso.",
            }
        except Exception:
            self.rollback()
            raise