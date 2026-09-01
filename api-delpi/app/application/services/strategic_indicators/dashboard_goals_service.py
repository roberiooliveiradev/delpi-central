from __future__ import annotations

import time
from typing import Any

from strategic_indicators_client import StrategicIndicatorsApiClient, StrategicIndicatorsApiError

from app.application.shared.numeric_parsing import to_optional_float
from app.application.services.strategic_indicators.dashboard_goal_dates import (
    normalize_si_branch,
    normalize_si_period_date,
)
from app.utils.logger import log_error


class DashboardGoalsService:
    _CACHE_TTL_SECONDS = 45.0

    def __init__(self, client: StrategicIndicatorsApiClient | None = None) -> None:
        self._client = client or StrategicIndicatorsApiClient()
        self._cache: dict[tuple, tuple[float, dict[str, dict[str, Any]]]] = {}

    def get_goal(
        self,
        *,
        source_key: str,
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
        department_id: str | None = None,
    ) -> dict[str, Any] | None:
        goals_map = self._load_goals_map(
            source_keys=[source_key],
            start_date=normalize_si_period_date(start_date),
            end_date=normalize_si_period_date(end_date),
            branch=normalize_si_branch(branch),
            department_id=department_id,
        )
        return goals_map.get(source_key)

    def attach_goal_fields(
        self,
        payload: dict[str, Any],
        *,
        source_key: str,
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
        department_id: str | None = None,
        recompute_target_pct_from: str | None = None,
        summary_key: str | None = None,
    ) -> dict[str, Any]:
        goal = self.get_goal(
            source_key=source_key,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            department_id=department_id,
        )
        if not goal:
            return payload

        goal_fields = self._flatten_goal(goal)
        if (
            goal_fields.get("comparable_goal") is None
            and not goal_fields.get("goal_label")
            and not goal_fields.get("goal_scope_hint")
        ):
            return payload
        # Period used for SI resolution — MFE uses these for Meta/parcial/acumulada
        # when goal_period_kind is absent (fallback in resolveGoalPeriodKind).
        if start_date:
            goal_fields["start_date"] = start_date
        if end_date:
            goal_fields["end_date"] = end_date
        target_block = payload

        if summary_key and isinstance(payload.get(summary_key), dict):
            target_block = payload[summary_key]
            enriched_block = {**target_block, **goal_fields}
            comparable = to_optional_float(goal_fields.get("comparable_goal"))
            if comparable is not None and comparable > 0 and recompute_target_pct_from:
                realized = self._resolve_realized_value(
                    enriched_block,
                    recompute_target_pct_from=recompute_target_pct_from,
                )
                if realized is not None:
                    enriched_block["target"] = comparable
                    pct_key = f"{recompute_target_pct_from}_target_pct"
                    enriched_block[pct_key] = (realized / comparable) * 100
                    if recompute_target_pct_from == "rol":
                        enriched_block["rol_target_pct"] = enriched_block[pct_key]
            return {**payload, summary_key: enriched_block}

        enriched = {**payload, **goal_fields}
        comparable = to_optional_float(goal_fields.get("comparable_goal"))
        if comparable is not None and comparable > 0 and recompute_target_pct_from:
            realized = self._resolve_realized_value(
                enriched,
                recompute_target_pct_from=recompute_target_pct_from,
            )
            if realized is not None:
                enriched["target"] = comparable
                pct_key = f"{recompute_target_pct_from}_target_pct"
                enriched[pct_key] = (realized / comparable) * 100
                if recompute_target_pct_from == "rol":
                    enriched["rol_target_pct"] = enriched[pct_key]

        return enriched

    @staticmethod
    def _resolve_realized_value(
        block: dict[str, Any],
        *,
        recompute_target_pct_from: str,
    ) -> float | None:
        return to_optional_float(block.get(recompute_target_pct_from))

    def attach_goals_index(
        self,
        payload: dict[str, Any],
        *,
        field_source_keys: dict[str, str],
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
        department_id: str | None = None,
    ) -> dict[str, Any]:
        source_keys = list(dict.fromkeys(field_source_keys.values()))
        goals_map = self._load_goals_map(
            source_keys=source_keys,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            department_id=department_id,
        )

        goals_by_metric: dict[str, dict[str, Any] | None] = {}
        for field, source_key in field_source_keys.items():
            goal = goals_map.get(source_key)
            flattened = self._flatten_goal(goal) if goal else None
            if flattened is not None:
                if start_date:
                    flattened["start_date"] = start_date
                if end_date:
                    flattened["end_date"] = end_date
            goals_by_metric[field] = flattened

        return {**payload, "goals_by_metric": goals_by_metric}

    def _load_goals_map(
        self,
        *,
        source_keys: list[str],
        start_date: str | None,
        end_date: str | None,
        branch: str | None,
        department_id: str | None,
    ) -> dict[str, dict[str, Any]]:
        start_date = normalize_si_period_date(start_date)
        end_date = normalize_si_period_date(end_date)
        branch = normalize_si_branch(branch)

        normalized_keys = tuple(
            sorted({str(key).strip() for key in source_keys if str(key).strip()})
        )
        if not normalized_keys:
            return {}

        cache_key = (
            normalized_keys,
            start_date or "",
            end_date or "",
            branch or "",
            department_id or "",
        )
        cached = self._cache.get(cache_key)
        now = time.monotonic()
        if cached and (now - cached[0]) < self._CACHE_TTL_SECONDS:
            return cached[1]

        try:
            response = self._client.list_dashboard_goals(
                source_keys=list(normalized_keys),
                start_date=start_date,
                end_date=end_date,
                branch=branch,
                department_id=department_id,
            )
        except StrategicIndicatorsApiError as exc:
            log_error(f"Metas SI indisponíveis para dashboards: {exc}")
            return {}

        items = response.get("items") or []
        goals_map: dict[str, dict[str, Any]] = {}
        for item in items:
            source_key = str(item.get("source_key") or "").strip()
            if source_key:
                goals_map[source_key] = item

        self._cache[cache_key] = (now, goals_map)
        return goals_map

    @staticmethod
    def _flatten_goal(goal: dict[str, Any] | None) -> dict[str, Any]:
        if not goal:
            return {
                "goal": None,
                "goal_label": None,
                "goal_value": None,
                "comparable_goal": None,
                "reference_goal": None,
                "target": None,
                "goal_periodicity": None,
                "goal_mode": None,
                "goal_aggregation": None,
                "goal_period_kind": None,
                "goal_period_partial": None,
                "goal_scope_branch": None,
                "goal_scope_label": None,
                "goal_scope_hint": None,
                "scope_type": None,
                "performance_direction": None,
                "indicator_id": None,
                "indicator_name": None,
                "value_unit": None,
                "value_prefix": None,
                "value_suffix": None,
                "value_decimals": None,
                "start_date": None,
                "end_date": None,
                "has_goal": False,
            }

        comparable = to_optional_float(goal.get("comparable_goal"))
        return {
            "goal": goal,
            "goal_label": goal.get("goal_label"),
            "goal_value": to_optional_float(goal.get("goal_value")),
            "comparable_goal": comparable,
            "reference_goal": to_optional_float(goal.get("reference_goal")),
            "target": comparable,
            "goal_periodicity": goal.get("goal_periodicity"),
            "goal_mode": goal.get("goal_mode"),
            "goal_aggregation": goal.get("goal_aggregation"),
            "goal_period_kind": goal.get("goal_period_kind"),
            "goal_period_partial": goal.get("goal_period_partial"),
            "goal_scope_branch": goal.get("goal_scope_branch"),
            "goal_scope_label": goal.get("goal_scope_label"),
            "goal_scope_hint": goal.get("goal_scope_hint"),
            "scope_type": goal.get("scope_type"),
            "performance_direction": goal.get("performance_direction"),
            "indicator_id": goal.get("indicator_id"),
            "indicator_name": goal.get("indicator_name"),
            "value_unit": goal.get("value_unit"),
            "value_prefix": goal.get("value_prefix"),
            "value_suffix": goal.get("value_suffix"),
            "value_decimals": goal.get("value_decimals"),
            "start_date": goal.get("start_date"),
            "end_date": goal.get("end_date"),
            "has_goal": bool(goal.get("has_goal")),
        }


_dashboard_goals_service: DashboardGoalsService | None = None


def get_dashboard_goals_service() -> DashboardGoalsService:
    global _dashboard_goals_service
    if _dashboard_goals_service is None:
        _dashboard_goals_service = DashboardGoalsService()
    return _dashboard_goals_service
