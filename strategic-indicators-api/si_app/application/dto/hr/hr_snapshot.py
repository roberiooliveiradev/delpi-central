from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class HrBranchSnapshot:
    branch_code: str
    absenteeism_pct: float | None
    turnover_pct: float | None
    training_hours_per_collaborator: float | None
    active_pdi_count: float | None = None
    active_pdi_pct: float | None = None
    performance_reviews_completion_pct: float | None = None
    internal_satisfaction_pct: float | None = None


@dataclass(frozen=True)
class HrMetricsSnapshot:
    start_date: str | None
    end_date: str | None
    branches: list[HrBranchSnapshot]
    internal_satisfaction_pct: float | None = None
    active_pdi_count: float | None = None
    active_pdi_pct: float | None = None
    performance_reviews_completion_pct: float | None = None


def _opt_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_branch_snapshot(raw: dict[str, Any]) -> HrBranchSnapshot:
    return HrBranchSnapshot(
        branch_code=str(raw.get("branch_code") or ""),
        absenteeism_pct=_opt_float(raw.get("absenteeism_pct")),
        turnover_pct=_opt_float(raw.get("turnover_pct")),
        training_hours_per_collaborator=_opt_float(
            raw.get("training_hours_per_collaborator")
        ),
        active_pdi_count=_opt_float(raw.get("active_pdi_count")),
        active_pdi_pct=_opt_float(raw.get("active_pdi_pct")),
        performance_reviews_completion_pct=_opt_float(
            raw.get("performance_reviews_completion_pct")
        ),
        internal_satisfaction_pct=_opt_float(raw.get("internal_satisfaction_pct")),
    )


def parse_hr_snapshot_payload(data: dict[str, Any]) -> HrMetricsSnapshot:
    branches = [
        _parse_branch_snapshot(item)
        for item in (data.get("branches") or [])
        if isinstance(item, dict)
    ]
    return HrMetricsSnapshot(
        start_date=data.get("start_date"),
        end_date=data.get("end_date"),
        branches=branches,
        internal_satisfaction_pct=_opt_float(data.get("internal_satisfaction_pct")),
        active_pdi_count=_opt_float(data.get("active_pdi_count")),
        active_pdi_pct=_opt_float(data.get("active_pdi_pct")),
        performance_reviews_completion_pct=_opt_float(
            data.get("performance_reviews_completion_pct")
        ),
    )
