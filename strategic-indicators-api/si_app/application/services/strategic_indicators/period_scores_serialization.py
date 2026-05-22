from __future__ import annotations

from dataclasses import asdict
from typing import Any

from si_app.application.dto.strategic_indicators.catalog_models import (
    StrategicDepartmentCalculatedValue,
    StrategicIndicatorCalculatedValue,
)
from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_models import (
    StrategicIndicatorsPeriodSnapshot,
)
from si_app.application.use_cases.strategic_indicators.period_resolution import (
    ResolvedPeriod,
)
from si_app.shared.branch_filter import effective_query_branch
from si_app.shared.json_encoding import to_json_safe


def normalize_scope_branch(branch: str | None) -> str:
    effective = effective_query_branch(branch)
    if effective is None:
        return ""
    return effective


def normalize_scope_department_id(department_id: str | None) -> str:
    return (department_id or "").strip()


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None

    return float(value)


def serialize_period_snapshot(
    snapshot: StrategicIndicatorsPeriodSnapshot,
) -> dict[str, Any]:
    return to_json_safe(
        {
            "competence": snapshot.period.competence,
            "start_date": snapshot.period.start_date,
            "end_date": snapshot.period.end_date,
            "igd": snapshot.igd,
            "igd_exact": snapshot.igd_exact,
            "classification": snapshot.classification,
            "calculated_departments": [
                asdict(department) for department in snapshot.calculated_departments
            ],
            "calculated_indicators": [
                asdict(indicator) for indicator in snapshot.calculated_indicators
            ],
            "measurement_errors": list(snapshot.measurement_errors),
        }
    )


def deserialize_period_snapshot(row: dict[str, Any]) -> StrategicIndicatorsPeriodSnapshot:
    period = ResolvedPeriod(
        competence=row["competence"],
        start_date=row["start_date"],
        end_date=row["end_date"],
    )

    calculated_indicators = [
        _indicator_from_dict(item) for item in row.get("calculated_indicators") or []
    ]
    calculated_departments = [
        _department_from_dict(item) for item in row.get("calculated_departments") or []
    ]

    return StrategicIndicatorsPeriodSnapshot(
        period=period,
        measurements=[],
        measurement_errors=list(row.get("measurement_errors") or []),
        calculated_indicators=calculated_indicators,
        calculated_departments=calculated_departments,
        igd=float(row.get("igd") or 0),
        igd_exact=float(row.get("igd_exact") or 0),
        classification=str(row.get("classification") or ""),
    )


def _indicator_from_dict(payload: dict[str, Any]) -> StrategicIndicatorCalculatedValue:
    return StrategicIndicatorCalculatedValue(
        indicator_id=payload["indicator_id"],
        department_id=payload["department_id"],
        indicator_name=payload.get("indicator_name", ""),
        weight_pct=float(payload.get("weight_pct") or 0),
        goal_label=payload.get("goal_label", ""),
        goal_value=float(payload.get("goal_value") or 0),
        goal_periodicity=payload.get("goal_periodicity", ""),
        goal_mode=payload.get("goal_mode", "standard"),
        monthly_targets=list(payload.get("monthly_targets") or []),
        scope_type=payload.get("scope_type", "consolidated"),
        performance_direction=payload.get("performance_direction", "higher_is_better"),
        strategic_description=payload.get("strategic_description", ""),
        source=payload.get("source", ""),
        value=_optional_float(payload.get("value")),
        score=_optional_float(payload.get("score")),
        gap=_optional_float(payload.get("gap")),
        trend=payload.get("trend", "stable"),
        classification=payload.get("classification", ""),
        unit_values=payload.get("unit_values"),
        unit_gaps=payload.get("unit_gaps"),
        value_unit=payload.get("value_unit"),
        value_prefix=payload.get("value_prefix"),
        value_suffix=payload.get("value_suffix"),
        value_decimals=int(payload.get("value_decimals") or 2),
    )


def _department_from_dict(payload: dict[str, Any]) -> StrategicDepartmentCalculatedValue:
    nested_indicators = [
        _indicator_from_dict(item) for item in payload.get("indicators") or []
    ]
    return StrategicDepartmentCalculatedValue(
        department_id=payload["department_id"],
        department_name=payload.get("department_name", ""),
        short_name=payload.get("short_name", ""),
        weight_pct=float(payload.get("weight_pct") or 0),
        strategic_summary=payload.get("strategic_summary", ""),
        aggregation_mode=payload.get("aggregation_mode", ""),
        score=float(payload.get("score") or 0),
        contribution=float(payload.get("contribution") or 0),
        classification=payload.get("classification", ""),
        trend=payload.get("trend", "stable"),
        indicators=nested_indicators,
    )
