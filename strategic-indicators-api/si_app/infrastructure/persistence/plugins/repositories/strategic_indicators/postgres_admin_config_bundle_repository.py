from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from si_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


def _json_safe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


class PostgresStrategicIndicatorsAdminConfigBundleRepository(PluginBaseRepository):
    SCHEMA_VERSION = 1

    def export_bundle(self) -> dict:
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
                is_active,
                display_order
            FROM strategic_indicators.departments
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
                performance_direction,
                strategic_description,
                source_key,
                value_unit,
                value_prefix,
                value_suffix,
                value_decimals,
                is_active,
                display_order
            FROM strategic_indicators.department_indicators
            ORDER BY department_id ASC, display_order ASC, indicator_name ASC
            """
        )

        goals = self.fetch_all(
            """
            SELECT
                ig.id,
                ig.indicator_id,
                di.indicator_name,
                di.department_id,
                ig.goal_year,
                ig.goal_label,
                ig.goal_value,
                ig.goal_periodicity,
                ig.goal_mode,
                ig.goal_scope_branch,
                ig.version,
                ig.is_active,
                ig.valid_from,
                ig.valid_to,
                ig.notes
            FROM strategic_indicators.indicator_goals ig
            INNER JOIN strategic_indicators.department_indicators di
                ON di.indicator_id = ig.indicator_id
            WHERE ig.is_active = TRUE
            ORDER BY
                ig.goal_year ASC,
                di.department_id ASC,
                ig.indicator_id ASC,
                ig.goal_scope_branch ASC
            """
        )

        goal_ids = [row["id"] for row in goals]
        monthly_by_goal: dict[str, list[dict]] = {str(goal_id): [] for goal_id in goal_ids}

        if goal_ids:
            monthly_rows = self.fetch_all(
                """
                SELECT
                    igmt.indicator_goal_id,
                    igmt.month_number,
                    igmt.target_value
                FROM strategic_indicators.indicator_goal_monthly_targets igmt
                WHERE igmt.indicator_goal_id = ANY(%s::uuid[])
                ORDER BY igmt.indicator_goal_id ASC, igmt.month_number ASC
                """,
                (goal_ids,),
            )
            for row in monthly_rows:
                goal_id = str(row["indicator_goal_id"])
                monthly_by_goal.setdefault(goal_id, []).append(
                    {
                        "month_number": int(row["month_number"]),
                        "target_value": float(row.get("target_value") or 0),
                    }
                )

        settings_rows = self.fetch_all(
            """
            SELECT setting_key, payload_json
            FROM strategic_indicators.module_settings
            WHERE is_active = TRUE
              AND setting_key IN ('parameters.global', 'governance.notes')
            ORDER BY setting_key ASC
            """
        )

        module_settings: dict[str, Any] = {}
        for row in settings_rows:
            key = row["setting_key"]
            payload = row.get("payload_json") or {}
            if key == "parameters.global":
                module_settings["parameters"] = payload
            elif key == "governance.notes":
                module_settings["governance"] = payload

        serialized_goals = []
        for row in goals:
            goal_id = str(row["id"])
            serialized_goals.append(
                {
                    "indicator_id": row["indicator_id"],
                    "indicator_name": row.get("indicator_name"),
                    "department_id": row.get("department_id"),
                    "goal_year": int(row["goal_year"]),
                    "goal_label": row["goal_label"],
                    "goal_value": float(row.get("goal_value") or 0),
                    "goal_periodicity": row["goal_periodicity"],
                    "goal_mode": row.get("goal_mode") or "standard",
                    "goal_scope_branch": row.get("goal_scope_branch") or "",
                    "version": int(row.get("version") or 1),
                    "is_active": bool(row.get("is_active")),
                    "valid_from": _json_safe(row.get("valid_from")),
                    "valid_to": _json_safe(row.get("valid_to")),
                    "notes": row.get("notes"),
                    "monthly_targets": monthly_by_goal.get(goal_id, []),
                }
            )

        return {
            "schema_version": self.SCHEMA_VERSION,
            "exported_at": datetime.utcnow().isoformat() + "Z",
            "departments": [_json_safe(row) for row in departments],
            "department_indicators": [_json_safe(row) for row in indicators],
            "indicator_goals": serialized_goals,
            "module_settings": module_settings,
        }

    def import_bundle(
        self,
        *,
        bundle: dict,
        actor_user_id: str | None,
        include_goals: bool = True,
    ) -> dict:
        schema_version = int(bundle.get("schema_version") or 0)
        if schema_version != self.SCHEMA_VERSION:
            raise ValueError(
                f"schema_version incompatível: esperado {self.SCHEMA_VERSION}."
            )

        departments = bundle.get("departments") or []
        indicators = bundle.get("department_indicators") or []
        goals = bundle.get("indicator_goals") or [] if include_goals else []
        module_settings = bundle.get("module_settings") or {}

        stats = {
            "departments_upserted": 0,
            "indicators_upserted": 0,
            "goals_created": 0,
            "goals_skipped": 0,
            "module_settings_updated": 0,
        }

        try:
            for row in departments:
                self._upsert_department(row, actor_user_id=actor_user_id)
                stats["departments_upserted"] += 1

            for row in indicators:
                self._upsert_indicator(row, actor_user_id=actor_user_id)
                stats["indicators_upserted"] += 1

            if include_goals:
                for row in goals:
                    if not bool(row.get("is_active", True)):
                        stats["goals_skipped"] += 1
                        continue
                    created = self._import_goal_if_missing(
                        row,
                        actor_user_id=actor_user_id,
                    )
                    if created:
                        stats["goals_created"] += 1
                    else:
                        stats["goals_skipped"] += 1

            stats["module_settings_updated"] = self._import_module_settings(
                module_settings,
                actor_user_id=actor_user_id,
            )

            self.commit()
            return stats
        except Exception:
            self.rollback()
            raise

    def _upsert_department(self, row: dict, *, actor_user_id: str | None) -> None:
        department_id = str(row.get("department_id") or "").strip()
        if not department_id:
            raise ValueError("department_id obrigatório no pacote de importação.")

        self.execute(
            """
            INSERT INTO strategic_indicators.departments (
                department_id,
                department_name,
                short_name,
                strategic_summary,
                headline_goal,
                supporting_focus,
                weight_pct,
                aggregation_mode,
                is_active,
                display_order,
                created_by_user_id,
                updated_by_user_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (department_id) DO UPDATE SET
                department_name = EXCLUDED.department_name,
                short_name = EXCLUDED.short_name,
                strategic_summary = EXCLUDED.strategic_summary,
                headline_goal = EXCLUDED.headline_goal,
                supporting_focus = EXCLUDED.supporting_focus,
                weight_pct = EXCLUDED.weight_pct,
                aggregation_mode = EXCLUDED.aggregation_mode,
                is_active = EXCLUDED.is_active,
                display_order = EXCLUDED.display_order,
                updated_by_user_id = EXCLUDED.updated_by_user_id,
                updated_at = NOW()
            """,
            (
                department_id,
                row.get("department_name") or department_id,
                row.get("short_name") or department_id,
                row.get("strategic_summary") or "",
                row.get("headline_goal") or "",
                row.get("supporting_focus") or "",
                float(row.get("weight_pct") or 0),
                row.get("aggregation_mode") or "consolidated",
                bool(row.get("is_active", True)),
                int(row.get("display_order") or 0),
                actor_user_id,
                actor_user_id,
            ),
        )

    def _upsert_indicator(self, row: dict, *, actor_user_id: str | None) -> None:
        indicator_id = str(row.get("indicator_id") or "").strip()
        department_id = str(row.get("department_id") or "").strip()
        if not indicator_id or not department_id:
            raise ValueError(
                "indicator_id e department_id são obrigatórios no pacote de importação."
            )

        from si_app.shared.goal_scope import supports_branch_goals_for_scope_type

        scope_type = row.get("scope_type") or "consolidated"
        supports_branch_goals = supports_branch_goals_for_scope_type(scope_type)

        self.execute(
            """
            INSERT INTO strategic_indicators.department_indicators (
                indicator_id,
                department_id,
                indicator_name,
                weight_pct,
                scope_type,
                performance_direction,
                strategic_description,
                source_key,
                value_unit,
                value_prefix,
                value_suffix,
                value_decimals,
                supports_branch_goals,
                is_active,
                display_order,
                created_by_user_id,
                updated_by_user_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (indicator_id) DO UPDATE SET
                department_id = EXCLUDED.department_id,
                indicator_name = EXCLUDED.indicator_name,
                weight_pct = EXCLUDED.weight_pct,
                scope_type = EXCLUDED.scope_type,
                performance_direction = EXCLUDED.performance_direction,
                strategic_description = EXCLUDED.strategic_description,
                source_key = EXCLUDED.source_key,
                value_unit = EXCLUDED.value_unit,
                value_prefix = EXCLUDED.value_prefix,
                value_suffix = EXCLUDED.value_suffix,
                value_decimals = EXCLUDED.value_decimals,
                supports_branch_goals = EXCLUDED.supports_branch_goals,
                is_active = EXCLUDED.is_active,
                display_order = EXCLUDED.display_order,
                updated_by_user_id = EXCLUDED.updated_by_user_id,
                updated_at = NOW()
            """,
            (
                indicator_id,
                department_id,
                row.get("indicator_name") or indicator_id,
                float(row.get("weight_pct") or 0),
                scope_type,
                row.get("performance_direction") or "higher_is_better",
                row.get("strategic_description") or "",
                row.get("source_key"),
                row.get("value_unit"),
                row.get("value_prefix"),
                row.get("value_suffix"),
                int(row.get("value_decimals") or 2),
                supports_branch_goals,
                bool(row.get("is_active", True)),
                int(row.get("display_order") or 0),
                actor_user_id,
                actor_user_id,
            ),
        )

    def _import_goal_if_missing(
        self,
        row: dict,
        *,
        actor_user_id: str | None,
    ) -> bool:
        indicator_id = str(row.get("indicator_id") or "").strip()
        goal_year = int(row.get("goal_year") or 0)
        goal_scope_branch = str(row.get("goal_scope_branch") or "").strip()

        if not indicator_id or goal_year < 2020 or goal_year > 2100:
            raise ValueError("Meta inválida no pacote de importação.")

        existing = self.fetch_one(
            """
            SELECT id
            FROM strategic_indicators.indicator_goals
            WHERE indicator_id = %s
              AND goal_year = %s
              AND goal_scope_branch = %s
              AND is_active = TRUE
            LIMIT 1
            """,
            (indicator_id, goal_year, goal_scope_branch),
        )
        if existing:
            return False

        from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_indicator_goals_repository import (
            PostgresStrategicIndicatorsIndicatorGoalsRepository,
        )

        goals_repo = PostgresStrategicIndicatorsIndicatorGoalsRepository(self.connection)
        goals_repo.create_indicator_goal(
            indicator_id=indicator_id,
            goal_year=goal_year,
            goal_label=str(row.get("goal_label") or "").strip(),
            goal_value=float(row.get("goal_value") or 0),
            goal_periodicity=str(row.get("goal_periodicity") or "monthly"),
            goal_mode=str(row.get("goal_mode") or "standard"),
            goal_scope_branch=goal_scope_branch,
            monthly_targets=row.get("monthly_targets") or [],
            valid_from=row.get("valid_from"),
            valid_to=row.get("valid_to"),
            notes=row.get("notes"),
            actor_user_id=actor_user_id,
        )
        return True

    def _import_module_settings(
        self,
        module_settings: dict,
        *,
        actor_user_id: str | None,
    ) -> int:
        updated = 0
        mapping = {
            "parameters.global": module_settings.get("parameters"),
            "governance.notes": module_settings.get("governance"),
        }

        for setting_key, payload in mapping.items():
            if payload is None:
                continue

            self.execute(
                """
                UPDATE strategic_indicators.module_settings
                SET
                    payload_json = %s::jsonb,
                    updated_by_user_id = %s,
                    updated_at = NOW()
                WHERE setting_key = %s
                """,
                (
                    json.dumps(payload, ensure_ascii=False),
                    actor_user_id,
                    setting_key,
                ),
            )
            updated += 1

        return updated
