from __future__ import annotations

import logging
from typing import Any

from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGateway
from app.infrastructure.gateways.delpi_envelope import unwrap_delpi_envelope

logger = logging.getLogger("supplies-api.strategic_indicators")

# Canonical SI indicator ids for supplies department (dashboard-supplies).
SI_INDICATOR_BY_KPI = {
    "KPI-OTD": "supplies-otd",
    "KPI-STOCK-VALUE": "supplies-stock-value",
    "KPI-TURNOVER": "supplies-stock-turnover",
    "KPI-CPV": "supplies-cpv",
    "KPI-SAVINGS": "supplies-negotiation-savings",
}


class StrategicIndicatorsGatewayError(RuntimeError):
    pass


def _as_optional_float(raw: Any) -> float | None:
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _pick_comparable_goal(
    goals: Any,
    *,
    branch: str | None,
) -> float | None:
    """SI `goals` map holds period-comparable metas (not cadastral goal_value)."""
    if not isinstance(goals, dict) or not goals:
        return None
    if branch:
        picked = _as_optional_float(goals.get(branch))
        if picked is not None:
            return picked
        # TOTVS branch sometimes arrives zero-padded inconsistently.
        alt = branch.lstrip("0") or "0"
        picked = _as_optional_float(goals.get(alt))
        if picked is not None:
            return picked
        padded = branch.zfill(2)
        picked = _as_optional_float(goals.get(padded))
        if picked is not None:
            return picked
    consolidated = _as_optional_float(goals.get("consolidated"))
    if consolidated is not None:
        return consolidated
    for key, value in goals.items():
        if key in {"01", "02", "consolidated"}:
            continue
        parsed = _as_optional_float(value)
        if parsed is not None:
            return parsed
    for key in ("01", "02"):
        parsed = _as_optional_float(goals.get(key))
        if parsed is not None:
            return parsed
    return None


def _normalize_direction(raw: Any) -> str | None:
    if raw is None:
        return None
    text = str(raw).strip().lower()
    if text in {"higher_is_better", "lower_is_better"}:
        return text
    return None


class StrategicIndicatorsGateway:
    """Reads SI goal triad + IDD scores via api-delpi department-indicators."""

    def __init__(self, delpi: DelpiApiGateway | None = None) -> None:
        self.delpi = delpi or DelpiApiGateway()

    def metrics_by_kpi(
        self,
        *,
        access_token: str,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> dict[str, dict[str, Any]]:
        """
        Returns per KPI:
        - goal_value: cadastral meta
        - comparable_goal: period meta from SI `goals` map
        - reference_goal: month/reference (standard ≈ goal_value)
        - score: Nota IDD
        - performance_direction / goal_mode when present
        """
        params: dict[str, Any] = {"department_id": "supplies"}
        if branch:
            params["branch"] = branch
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        try:
            raw = self.delpi.get(
                "/dashboard/department-indicators",
                access_token=access_token,
                params=params,
            )
        except Exception as exc:  # noqa: BLE001 — degrade to empty metas
            logger.warning("si_goals_unavailable error=%s", exc)
            raise StrategicIndicatorsGatewayError("strategic indicators unavailable") from exc

        data = unwrap_delpi_envelope(raw)
        item = data.get("item") if isinstance(data, dict) else None
        indicators = item.get("indicators") if isinstance(item, dict) else None
        by_id: dict[str, Any] = {}
        if isinstance(indicators, list):
            for row in indicators:
                if isinstance(row, dict) and row.get("indicator_id"):
                    by_id[str(row["indicator_id"])] = row

        metrics: dict[str, dict[str, Any]] = {}
        for kpi_id, indicator_id in SI_INDICATOR_BY_KPI.items():
            row = by_id.get(indicator_id) or {}
            goal_value = _as_optional_float(row.get("goal_value"))
            # Prefer SI top-level triad when department-indicators exposes it.
            comparable = _as_optional_float(row.get("comparable_goal"))
            if comparable is None:
                comparable = _pick_comparable_goal(row.get("goals"), branch=branch)
            if comparable is None:
                comparable = goal_value
            goal_mode = str(row.get("goal_mode") or "standard").strip().lower() or "standard"
            reference = _as_optional_float(row.get("reference_goal"))
            if reference is None:
                # Standard mode fallback: cadastral goal_value (rollup when SI sends it).
                reference = goal_value
            metrics[kpi_id] = {
                "goal_value": goal_value,
                "comparable_goal": comparable,
                "reference_goal": reference,
                "score": _as_optional_float(row.get("score")),
                "performance_direction": _normalize_direction(
                    row.get("performance_direction")
                ),
                "goal_mode": goal_mode,
                # Legacy alias used by goals_by_kpi / older callers.
                "goal": goal_value,
            }
        return metrics

    def goals_by_kpi(
        self,
        *,
        access_token: str,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> dict[str, float | None]:
        """Backward-compatible: cadastral SI goal_value per KPI."""
        metrics = self.metrics_by_kpi(
            access_token=access_token,
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )
        return {kpi_id: row.get("goal_value") for kpi_id, row in metrics.items()}
