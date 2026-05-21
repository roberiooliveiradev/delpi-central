from __future__ import annotations

from dataclasses import asdict
from typing import Any

from si_app.application.dto.strategic_indicators.catalog_models import (
    StrategicDepartmentCatalogItem,
    StrategicIndicatorCatalogItem,
    StrategicIndicatorMeasuredValue,
)
from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_models import (
    StrategicIndicatorsCatalogSnapshot,
)
from si_app.application.use_cases.strategic_indicators.period_resolution import (
    ResolvedPeriod,
)
from si_app.application.services.strategic_indicators.period_scores_serialization import (
    _optional_float,
)
from si_app.shared.json_encoding import to_json_safe

CALCULATION_SNAPSHOT_SCHEMA_VERSION = 1


def serialize_calculation_inputs(
    *,
    period: ResolvedPeriod,
    catalog: StrategicIndicatorsCatalogSnapshot,
    measurements: list[StrategicIndicatorMeasuredValue],
    measurement_errors: list[dict],
) -> dict[str, Any]:
    return to_json_safe(
        {
            "schema_version": CALCULATION_SNAPSHOT_SCHEMA_VERSION,
            "competence": period.competence,
            "start_date": period.start_date,
            "end_date": period.end_date,
            "departments_catalog": [
                asdict(department) for department in catalog.departments_catalog
            ],
            "indicators_catalog": [
                asdict(indicator) for indicator in catalog.indicators_catalog
            ],
            "goals_by_department": dict(catalog.goals_by_department),
            "measurements": [asdict(measurement) for measurement in measurements],
            "measurement_errors": list(measurement_errors),
        }
    )


def deserialize_calculation_inputs(row: dict[str, Any]) -> tuple[
    ResolvedPeriod,
    StrategicIndicatorsCatalogSnapshot,
    list[StrategicIndicatorMeasuredValue],
    list[dict],
]:
    period = ResolvedPeriod(
        competence=row["competence"],
        start_date=row["start_date"],
        end_date=row["end_date"],
    )

    departments_catalog = [
        StrategicDepartmentCatalogItem(
            department_id=item["department_id"],
            department_name=item.get("department_name", ""),
            short_name=item.get("short_name", ""),
            weight_pct=float(item.get("weight_pct") or 0),
            strategic_summary=item.get("strategic_summary", ""),
            aggregation_mode=item.get("aggregation_mode", "consolidated"),
        )
        for item in row.get("departments_catalog") or []
    ]

    indicators_catalog = [
        StrategicIndicatorCatalogItem(
            indicator_id=item["indicator_id"],
            department_id=item["department_id"],
            indicator_name=item.get("indicator_name", ""),
            weight_pct=float(item.get("weight_pct") or 0),
            goal_label=item.get("goal_label", ""),
            goal_value=float(item.get("goal_value") or 0),
            goal_periodicity=item.get("goal_periodicity", ""),
            goal_mode=item.get("goal_mode", "standard"),
            monthly_targets=list(item.get("monthly_targets") or []),
            scope_type=item.get("scope_type", "consolidated"),
            performance_direction=item.get("performance_direction", "higher_is_better"),
            strategic_description=item.get("strategic_description", ""),
            source_key=item.get("source_key"),
            value_unit=item.get("value_unit"),
            value_prefix=item.get("value_prefix"),
            value_suffix=item.get("value_suffix"),
            value_decimals=int(item.get("value_decimals") or 2),
            branch_goals=dict(item.get("branch_goals") or {}),
        )
        for item in row.get("indicators_catalog") or []
    ]

    catalog = StrategicIndicatorsCatalogSnapshot(
        departments_catalog=departments_catalog,
        indicators_catalog=indicators_catalog,
        goals_by_department=dict(row.get("goals_by_department") or {}),
    )

    measurements = [
        StrategicIndicatorMeasuredValue(
            indicator_id=item["indicator_id"],
            department_id=item["department_id"],
            value=_optional_float(item.get("value")),
            source=item.get("source", ""),
            unit_values=item.get("unit_values"),
        )
        for item in row.get("measurements") or []
    ]

    return period, catalog, measurements, list(row.get("measurement_errors") or [])
