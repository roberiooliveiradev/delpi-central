from __future__ import annotations

from calendar import monthrange
from collections import defaultdict
from datetime import date

from app.application.dto.strategic_indicators.catalog_models import (
    StrategicIndicatorCalculatedValue,
)
from app.application.dto.strategic_indicators.get_trends_real_request import (
    GetStrategicIndicatorsTrendsRealRequest,
)
from app.application.services.strategic_indicators.strategic_indicators_snapshot_service import (
    StrategicIndicatorsPeriodSnapshot,
    StrategicIndicatorsSnapshotService,
)
from app.application.use_cases.strategic_indicators.period_resolution import (
    ResolvedPeriod,
)


class GetStrategicIndicatorsTrendsRealUseCase:
    def __init__(
        self,
        *,
        snapshot_service: StrategicIndicatorsSnapshotService,
    ) -> None:
        self._snapshot_service = snapshot_service

    def execute(
        self,
        request: GetStrategicIndicatorsTrendsRealRequest,
    ) -> dict:
        months = max(2, min(request.months, 12))
        reference = self._parse_competence(request.competence)
        periods = self._build_periods(reference, months)

        snapshots = self._snapshot_service.get_series_snapshot_optimized(
            periods=periods,
            department_id=request.department_id,
            branch=request.branch,
        )

        monthly_points: list[dict] = []
        monthly_departments: dict[str, list[dict]] = {}
        errors: list[dict] = []

        for snapshot in snapshots:
            monthly_points.append(
                {
                    "period": snapshot.period.competence,
                    "value": self._safe_float(snapshot.igd),
                    "classification": snapshot.classification,
                }
            )

            for department in snapshot.calculated_departments:
                monthly_departments.setdefault(department.department_id, []).append(
                    {
                        "period": snapshot.period.competence,
                        "score": self._safe_float(department.score),
                        "name": department.department_name,
                        "classification": department.classification,
                        "contribution": self._safe_float(department.contribution),
                    }
                )

            for error in snapshot.measurement_errors:
                errors.append(
                    {
                        "competence": snapshot.period.competence,
                        "department_id": error["department_id"],
                        "source": error["source"],
                        "message": error["message"],
                    }
                )

        current_point = monthly_points[-1]
        previous_point = (
            monthly_points[-2] if len(monthly_points) >= 2 else monthly_points[-1]
        )

        departments = []
        for department_id, series in monthly_departments.items():
            if not series:
                continue

            first = series[0]
            current = series[-1]
            previous = series[-2] if len(series) >= 2 else series[-1]

            best_point = max(series, key=lambda item: self._safe_float(item["score"]))
            worst_point = min(series, key=lambda item: self._safe_float(item["score"]))

            interval_direction = self._resolve_direction(
                current=self._safe_float(current["score"]),
                previous=self._safe_float(first["score"]),
            )

            last_step_direction = self._resolve_direction(
                current=self._safe_float(current["score"]),
                previous=self._safe_float(previous["score"]),
            )

            departments.append(
                {
                    "id": department_id,
                    "name": current["name"],
                    "current": current["score"],
                    "previous": previous["score"],
                    "direction": last_step_direction,
                    "last_step_direction": last_step_direction,
                    "net_variation": round(current["score"] - previous["score"], 3),
                    "best_score": round(best_point["score"], 3),
                    "worst_score": round(worst_point["score"], 3),
                    "current_classification": current["classification"],
                    "current_contribution": round(
                        float(current.get("contribution") or 0), 3
                    ),
                    "series": [
                        {
                            "period": point["period"],
                            "score": round(float(point["score"]), 3),
                            "classification": point["classification"],
                            "contribution": round(
                                float(point.get("contribution") or 0), 3
                            ),
                        }
                        for point in series
                    ],
                }
            )

        departments.sort(key=lambda item: item["name"])

        indicator_series_by_department_id = self._build_indicator_series_by_department_id(
            snapshots
        )

        return {
            "competence": current_point["period"],
            "current_igd": self._safe_float(current_point["value"]),
            "previous_igd": self._safe_float(previous_point["value"]),
            "current_classification": current_point["classification"],
            "igd_series": monthly_points,
            "departments": departments,
            "indicator_series_by_department_id": indicator_series_by_department_id,
            "errors": errors,
            "partial_success": len(errors) > 0,
        }

    def _build_indicator_series_by_department_id(
        self,
        snapshots: list[StrategicIndicatorsPeriodSnapshot],
    ) -> dict[str, list[dict]]:
        grouped: dict[str, dict[str, dict]] = defaultdict(dict)

        for snapshot in snapshots:
            period_label = snapshot.period.competence

            for indicator in snapshot.calculated_indicators:
                department_bucket = grouped[indicator.department_id]
                existing = department_bucket.get(indicator.indicator_id)

                point = self._build_indicator_series_point(
                    period_label=period_label,
                    indicator=indicator,
                )

                if existing is None:
                    department_bucket[indicator.indicator_id] = {
                        "indicator_id": indicator.indicator_id,
                        "indicator_name": indicator.indicator_name,
                        "weight_pct": indicator.weight_pct,
                        "goal_label": indicator.goal_label,
                        "goal_value": self._safe_float(indicator.goal_value),
                        "goal_periodicity": indicator.goal_periodicity,
                        "goal_mode": getattr(indicator, "goal_mode", "standard"),
                        "monthly_targets": getattr(indicator, "monthly_targets", []) or [],
                        "scope_type": indicator.scope_type,
                        "performance_direction": getattr(
                            indicator,
                            "performance_direction",
                            "higher_is_better",
                        ),
                        "strategic_description": indicator.strategic_description,
                        "source": indicator.source,
                        "series": [point],
                    }
                    continue

                existing["series"].append(point)

        for department_bucket in grouped.values():
            for item in department_bucket.values():
                item["series"] = sorted(
                    item["series"],
                    key=lambda entry: entry["period"],
                )

        return {
            department_id: list(indicators.values())
            for department_id, indicators in grouped.items()
        }

    def _build_indicator_series_point(
        self,
        *,
        period_label: str,
        indicator: StrategicIndicatorCalculatedValue,
    ) -> dict:
        return {
            "period": period_label,
            "value": self._safe_round(indicator.value, 3),
            "score": self._safe_round(indicator.score, 3),
            "gap": self._safe_round(indicator.gap, 3),
            "classification": indicator.classification,
            "trend": indicator.trend,
        }

    def _parse_competence(self, competence: str | None) -> date:
        if competence:
            year_str, month_str = competence.split("-")
            return date(int(year_str), int(month_str), 1)

        today = date.today()
        return date(today.year, today.month, 1)

    def _build_periods(self, reference: date, months: int) -> list[ResolvedPeriod]:
        periods: list[ResolvedPeriod] = []

        year = reference.year
        month = reference.month

        for offset in range(months - 1, -1, -1):
            current_year = year
            current_month = month - offset

            while current_month <= 0:
                current_month += 12
                current_year -= 1

            while current_month > 12:
                current_month -= 12
                current_year += 1

            competence = f"{current_year}-{str(current_month).zfill(2)}"
            first_day = f"01-{str(current_month).zfill(2)}-{current_year}"
            last_day = monthrange(current_year, current_month)[1]
            last_date = (
                f"{str(last_day).zfill(2)}-{str(current_month).zfill(2)}-{current_year}"
            )

            periods.append(
                ResolvedPeriod(
                    competence=competence,
                    start_date=first_day,
                    end_date=last_date,
                )
            )

        return periods

    def _resolve_direction(self, current: float, previous: float) -> str:
        delta = current - previous

        if delta > 0.09:
            return "up"
        if delta < -0.09:
            return "down"
        return "stable"

    def _safe_float(self, value) -> float:
        if value is None:
            return 0.0
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _safe_round(self, value, digits: int) -> float:
        return round(self._safe_float(value), digits)