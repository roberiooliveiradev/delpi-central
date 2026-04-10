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
        settings_map = self._load_global_settings_blocks()

        departments_rows = self.fetch_all(
            """
            SELECT
                department_id,
                department_name,
                headline_goal,
                supporting_focus,
                weight_pct,
                updated_at,
                updated_by_email
            FROM strategic_indicators.departments
            WHERE is_active = TRUE
            ORDER BY display_order ASC, department_name ASC
            """
        )

        latest_updated_at = None
        latest_updated_by_email = None

        for row in departments_rows:
            row_updated_at = row.get("updated_at")
            if latest_updated_at is None or (
                row_updated_at is not None and row_updated_at > latest_updated_at
            ):
                latest_updated_at = row_updated_at
                latest_updated_by_email = row.get("updated_by_email")

        for row in settings_map["_meta_rows"]:
            row_updated_at = row.get("updated_at")
            if latest_updated_at is None or (
                row_updated_at is not None and row_updated_at > latest_updated_at
            ):
                latest_updated_at = row_updated_at
                latest_updated_by_email = row.get("updated_by_email")

        return {
            "weights": {
                "items": [
                    {
                        "department_id": row["department_id"],
                        "department_name": row["department_name"],
                        "weight_pct": float(row.get("weight_pct") or 0),
                    }
                    for row in departments_rows
                ]
            },
            "goals": {
                "items": [
                    {
                        "department_id": row["department_id"],
                        "department_name": row["department_name"],
                        "headline_goal": row.get("headline_goal") or "",
                        "supporting_focus": row.get("supporting_focus") or "",
                    }
                    for row in departments_rows
                ]
            },
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
        from app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_settings_audit_repository import (
            PostgresStrategicIndicatorsSettingsAuditRepository,
        )

        audit_repository = PostgresStrategicIndicatorsSettingsAuditRepository(self.connection)

        select_settings_query = """
            SELECT setting_key, payload_json
            FROM strategic_indicators.module_settings
            WHERE setting_key = %s
            LIMIT 1
        """

        update_settings_query = """
            UPDATE strategic_indicators.module_settings
            SET
                payload_json = %s::jsonb,
                updated_by_user_id = %s,
                updated_by_email = %s,
                updated_at = NOW()
            WHERE setting_key = %s
        """

        try:
            self._update_departments_weights_and_goals(
                weights=weights,
                goals=goals,
                actor_user_id=actor_user_id,
                actor_email=actor_email,
                audit_repository=audit_repository,
            )

            for setting_key, payload_after in [
                ("parameters.global", parameters),
                ("governance.notes", governance),
            ]:
                row_before = self.fetch_one(select_settings_query, (setting_key,))
                payload_before = row_before["payload_json"] if row_before else None

                self.execute(
                    update_settings_query,
                    (
                        json.dumps(payload_after, ensure_ascii=False),
                        actor_user_id,
                        actor_email,
                        setting_key,
                    ),
                )

                audit_repository.insert_audit_event(
                    entity_key=setting_key,
                    payload_before=payload_before,
                    payload_after=payload_after,
                    changed_by_user_id=actor_user_id,
                    changed_by_email=actor_email,
                )

            self.commit()

            return {
                "message": "Configurações do Strategic Indicators atualizadas com sucesso.",
            }
        except Exception:
            self.rollback()
            raise

    def _load_global_settings_blocks(self) -> dict:
        query = """
            SELECT
                setting_key,
                payload_json,
                updated_at,
                updated_by_email
            FROM strategic_indicators.module_settings
            WHERE is_active = TRUE
              AND setting_key IN ('parameters.global', 'governance.notes')
            ORDER BY setting_key
        """

        rows = self.fetch_all(query)

        settings_map = {
            "parameters": {"items": []},
            "governance": {"items": []},
            "_meta_rows": rows,
        }

        for row in rows:
            setting_key = row["setting_key"]
            payload = row.get("payload_json") or {}

            if setting_key == "parameters.global":
                settings_map["parameters"] = payload
            elif setting_key == "governance.notes":
                settings_map["governance"] = payload

        return settings_map

    def _update_departments_weights_and_goals(
        self,
        *,
        weights: dict,
        goals: dict,
        actor_user_id: str | None,
        actor_email: str | None,
        audit_repository,
    ) -> None:
        weights_by_department = {
            item["department_id"]: float(item.get("weight_pct") or 0)
            for item in weights.get("items", [])
        }
        goals_by_department = {
            item["department_id"]: {
                "headline_goal": item.get("headline_goal") or "",
                "supporting_focus": item.get("supporting_focus") or "",
            }
            for item in goals.get("items", [])
        }

        before_rows = self.fetch_all(
            """
            SELECT
                department_id,
                department_name,
                weight_pct,
                headline_goal,
                supporting_focus,
                strategic_summary,
                short_name,
                aggregation_mode,
                is_active,
                display_order
            FROM strategic_indicators.departments
            ORDER BY display_order ASC, department_name ASC
            """
        )

        before_map = {
            row["department_id"]: row
            for row in before_rows
        }

        department_ids = sorted(
            set(weights_by_department.keys()) | set(goals_by_department.keys())
        )

        for department_id in department_ids:
            before_row = before_map.get(department_id)
            if not before_row:
                raise ValueError(
                    f"Departamento não encontrado para atualização: {department_id}"
                )

            new_weight = weights_by_department.get(
                department_id,
                float(before_row.get("weight_pct") or 0),
            )
            new_goal = goals_by_department.get(
                department_id,
                {
                    "headline_goal": before_row.get("headline_goal") or "",
                    "supporting_focus": before_row.get("supporting_focus") or "",
                },
            )

            payload_before = {
                "department_id": before_row["department_id"],
                "department_name": before_row["department_name"],
                "weight_pct": float(before_row.get("weight_pct") or 0),
                "headline_goal": before_row.get("headline_goal") or "",
                "supporting_focus": before_row.get("supporting_focus") or "",
            }

            payload_after = {
                "department_id": before_row["department_id"],
                "department_name": before_row["department_name"],
                "weight_pct": new_weight,
                "headline_goal": new_goal["headline_goal"],
                "supporting_focus": new_goal["supporting_focus"],
            }

            self.execute(
                """
                UPDATE strategic_indicators.departments
                SET
                    weight_pct = %s,
                    headline_goal = %s,
                    supporting_focus = %s,
                    updated_by_user_id = %s,
                    updated_by_email = %s,
                    updated_at = NOW()
                WHERE department_id = %s
                """,
                (
                    new_weight,
                    new_goal["headline_goal"],
                    new_goal["supporting_focus"],
                    actor_user_id,
                    actor_email,
                    department_id,
                ),
            )

            audit_repository.insert_audit_event(
                entity_key=f"departments.{department_id}",
                payload_before=payload_before,
                payload_after=payload_after,
                changed_by_user_id=actor_user_id,
                changed_by_email=actor_email,
            )