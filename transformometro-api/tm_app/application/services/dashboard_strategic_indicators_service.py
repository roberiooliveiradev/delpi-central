"""Compose public SI signals for the Transforma+ Overview.

Does not calculate IDD, target or comparable_goal. Passes SI fields through.
"""

from __future__ import annotations

from typing import Any

from tm_app.application.ports.strategic_indicators_port import StrategicIndicatorsPort
from tm_app.domain.strategic_indicators_context import (
    DEPARTMENT_DISPLAY_LABEL,
    GROSS_SAVINGS_INDICATOR_ID,
    GROSS_SAVINGS_SOURCE_KEY,
    STRATEGIC_INDICATORS_DEPARTMENT_ID,
)


def normalize_si_branch(branch: str | None) -> str | None:
    raw = (branch or "").strip()
    if not raw or raw.lower() in {"all", "consolidated", "*"}:
        return None
    return raw


def _to_optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if numeric != numeric:  # NaN
        return None
    return numeric


def flatten_si_goal_fields(goal: dict[str, Any] | None) -> dict[str, Any]:
    """Select public SI goal fields. No formula — copy only."""
    if not goal:
        return {
            "goal_label": None,
            "goal_value": None,
            "comparable_goal": None,
            "reference_goal": None,
            "target": None,
            "has_goal": False,
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
        }

    comparable = _to_optional_float(goal.get("comparable_goal"))
    has_goal = goal.get("has_goal")
    if has_goal is None:
        has_goal = comparable is not None or _to_optional_float(goal.get("goal_value")) is not None
    return {
        "goal_label": goal.get("goal_label"),
        "goal_value": _to_optional_float(goal.get("goal_value")),
        "comparable_goal": comparable,
        "reference_goal": _to_optional_float(goal.get("reference_goal")),
        "target": comparable,
        "has_goal": bool(has_goal),
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
    }


def _pick_goal_item(payload: dict[str, Any] | None, source_key: str) -> dict[str, Any] | None:
    if not payload:
        return None
    items = payload.get("items")
    if not isinstance(items, list):
        return None
    for item in items:
        if not isinstance(item, dict):
            continue
        if str(item.get("source_key") or "").strip() == source_key:
            return item
    return None


def _indicator_score_items(payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not payload:
        return []
    raw = payload.get("indicators")
    if not isinstance(raw, list):
        return []
    items: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        indicator_id = str(item.get("indicator_id") or "").strip()
        if not indicator_id:
            continue
        items.append(
            {
                "indicator_id": indicator_id,
                "score": _to_optional_float(item.get("score")),
                "name": item.get("name"),
            }
        )
    return items


def _department_idd_fields(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not payload:
        return None
    score = _to_optional_float(payload.get("score") if payload.get("score") is not None else payload.get("idd"))
    classification = payload.get("classification")
    if score is None and not (isinstance(classification, str) and classification.strip()):
        return None
    return {
        "department_id": payload.get("department_id") or STRATEGIC_INDICATORS_DEPARTMENT_ID,
        "department_name": payload.get("department_name"),
        "score": score,
        "classification": classification.strip() if isinstance(classification, str) else None,
        "partial_success": bool(payload.get("partial_success")),
    }


class DashboardStrategicIndicatorsService:
    def __init__(self, port: StrategicIndicatorsPort) -> None:
        self._port = port

    def get_program_context(
        self,
        *,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
    ) -> dict[str, Any]:
        normalized_branch = normalize_si_branch(branch)
        period = {
            "competence": (competence or "").strip() or None,
            "start_date": (start_date or "").strip() or None,
            "end_date": (end_date or "").strip() or None,
            "branch": normalized_branch,
        }

        score_payload = self._port.get_department_score(
            department_id=STRATEGIC_INDICATORS_DEPARTMENT_ID,
            competence=period["competence"],
            start_date=period["start_date"],
            end_date=period["end_date"],
            branch=normalized_branch,
        )
        indicators_payload = self._port.get_department_indicators(
            department_id=STRATEGIC_INDICATORS_DEPARTMENT_ID,
            competence=period["competence"],
            start_date=period["start_date"],
            end_date=period["end_date"],
            branch=normalized_branch,
        )
        goals_payload = self._port.list_dashboard_goals(
            source_keys=[GROSS_SAVINGS_SOURCE_KEY],
            competence=period["competence"],
            start_date=period["start_date"],
            end_date=period["end_date"],
            branch=normalized_branch,
            department_id=STRATEGIC_INDICATORS_DEPARTMENT_ID,
        )

        department_idd = _department_idd_fields(score_payload) or _department_idd_fields(
            indicators_payload
        )
        indicators = _indicator_score_items(indicators_payload)
        goal_item = _pick_goal_item(goals_payload, GROSS_SAVINGS_SOURCE_KEY)
        goal_fields = flatten_si_goal_fields(goal_item) if goal_item else flatten_si_goal_fields(None)

        indicator_score = next(
            (
                item.get("score")
                for item in indicators
                if item.get("indicator_id") == GROSS_SAVINGS_INDICATOR_ID
            ),
            None,
        )

        gross_savings = None
        if goal_item or indicator_score is not None:
            gross_savings = {
                "indicator_id": GROSS_SAVINGS_INDICATOR_ID,
                "source_key": GROSS_SAVINGS_SOURCE_KEY,
                "score": indicator_score,
                **goal_fields,
            }
            if not gross_savings.get("indicator_id"):
                gross_savings["indicator_id"] = GROSS_SAVINGS_INDICATOR_ID

        available = any(
            (
                department_idd is not None,
                bool(indicators),
                goal_item is not None,
            )
        )
        return {
            "available": available,
            "strategic_indicators_department": STRATEGIC_INDICATORS_DEPARTMENT_ID,
            "department_label": DEPARTMENT_DISPLAY_LABEL,
            **period,
            "department_idd": department_idd,
            "indicators": indicators,
            "gross_savings": gross_savings,
        }
