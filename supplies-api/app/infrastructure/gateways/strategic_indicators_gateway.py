from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
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

UNIT_SCOPE_KEYS = ("consolidated", "01", "02")
STRATEGIC_KPI_IDS = frozenset(SI_INDICATOR_BY_KPI)


class StrategicIndicatorsGatewayError(RuntimeError):
    pass


def _as_optional_int(raw: Any) -> int | None:
    if isinstance(raw, bool) or raw is None:
        return None
    if isinstance(raw, int):
        return raw
    if isinstance(raw, float):
        return int(raw)
    return None


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


def _scope_number_map(raw: Any, visible_keys: tuple[str, ...]) -> dict[str, float | None]:
    if not isinstance(raw, dict):
        return {}
    mapped: dict[str, float | None] = {}
    for key in visible_keys:
        if key not in raw:
            continue
        mapped[key] = _as_optional_float(raw.get(key))
    return mapped


def _optional_text(raw: Any) -> str | None:
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


def _metrics_from_item(
    item: dict[str, Any] | None,
    *,
    branch: str | None,
    visible_keys: tuple[str, ...] | None,
) -> dict[str, dict[str, Any]]:
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
        comparable = _as_optional_float(row.get("comparable_goal"))
        if comparable is None:
            comparable = _pick_comparable_goal(row.get("goals"), branch=branch)
        if comparable is None:
            comparable = goal_value
        goal_mode = str(row.get("goal_mode") or "standard").strip().lower() or "standard"
        reference = _as_optional_float(row.get("reference_goal"))
        if reference is None:
            reference = goal_value
        metric: dict[str, Any] = {
            "indicator_id": indicator_id,
            "present": bool(row),
            "goal_value": goal_value,
            "comparable_goal": comparable,
            "reference_goal": reference,
            "score": _as_optional_float(row.get("score")),
            "performance_direction": _normalize_direction(row.get("performance_direction")),
            "goal_mode": goal_mode,
            "goal_period_kind": _optional_text(row.get("goal_period_kind")),
            "goal_period_partial": row.get("goal_period_partial")
            if isinstance(row.get("goal_period_partial"), bool)
            else None,
            "value_unit": _optional_text(row.get("value_unit")),
            "value_prefix": row.get("value_prefix") if isinstance(row.get("value_prefix"), str) else None,
            "value_suffix": row.get("value_suffix") if isinstance(row.get("value_suffix"), str) else None,
            "value_decimals": _as_optional_int(row.get("value_decimals")),
            "goal": goal_value,
        }
        if visible_keys is not None:
            metric["realized"] = _scope_number_map(row.get("realized"), visible_keys)
            metric["goals_by_unit"] = _scope_number_map(row.get("goals"), visible_keys)
        metrics[kpi_id] = metric
    return metrics


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
        item = self._fetch_department_item(
            access_token=access_token,
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )
        return _metrics_from_item(item, branch=branch, visible_keys=None)

    def compose_strategic(
        self,
        *,
        access_token: str,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> dict[str, Any]:
        """Department IDD + per-indicator realized/goals. Does not recalculate scores."""
        view_branch = branch if branch in {"01", "02"} else None
        fetches: tuple[tuple[str, str | None], ...] = (
            ((view_branch, view_branch),)
            if view_branch
            else (("consolidated", None), ("01", "01"), ("02", "02"))
        )
        items: dict[str, dict[str, Any]] = {}
        errors: list[str] = []
        with ThreadPoolExecutor(max_workers=len(fetches)) as pool:
            futures = {
                pool.submit(
                    self._fetch_department_item,
                    access_token=access_token,
                    branch=fetch_branch,
                    start_date=start_date,
                    end_date=end_date,
                ): scope_key
                for scope_key, fetch_branch in fetches
            }
            for future in as_completed(futures):
                scope_key = futures[future]
                try:
                    item = future.result()
                except StrategicIndicatorsGatewayError as exc:
                    errors.append(f"{scope_key}: {exc}")
                    continue
                if isinstance(item, dict):
                    items[scope_key] = item

        primary_key = view_branch or "consolidated"
        if primary_key not in items and not items:
            raise StrategicIndicatorsGatewayError("strategic indicators unavailable")

        visible = (view_branch,) if view_branch else UNIT_SCOPE_KEYS
        metrics = _metrics_from_item(
            items.get(primary_key),
            branch=view_branch,
            visible_keys=visible,
        )
        scores: dict[str, dict[str, Any]] = {}
        partial = bool(errors)
        for scope_key, item in items.items():
            if scope_key not in visible:
                continue
            raw_score = item.get("score")
            if raw_score is None:
                raw_score = item.get("idd")
            classification = item.get("classification")
            scores[scope_key] = {
                "score": _as_optional_float(raw_score),
                "classification": classification if isinstance(classification, str) else None,
            }
            if item.get("partial_success") is True:
                partial = True
        return {
            "metrics": metrics,
            "context": {
                "departmentId": "supplies",
                "scores": scores,
                "partialSuccess": partial,
            },
            "errors": errors,
        }

    def _fetch_department_item(
        self,
        *,
        access_token: str,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> dict[str, Any] | None:
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
        except Exception as exc:  # noqa: BLE001 — caller records partial failure
            logger.warning("si_department_unavailable branch=%s error=%s", branch or "all", exc)
            raise StrategicIndicatorsGatewayError("strategic indicators unavailable") from exc
        data = unwrap_delpi_envelope(raw)
        item = data.get("item") if isinstance(data, dict) else None
        return item if isinstance(item, dict) else None

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
