from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date

from app.application.dto.strategic_indicators.catalog_models import (
    StrategicDepartmentCalculatedValue,
)
from app.application.dto.strategic_indicators.get_presentation_request import (
    GetStrategicIndicatorsPresentationRequest,
)
from app.application.use_cases.strategic_indicators.period_resolution import (
    ResolvedPeriod,
)
from app.application.services.strategic_indicators.strategic_indicators_snapshot_service import (
    StrategicIndicatorsSnapshotService,
)
from app.domain.ports.strategic_indicators.alerts_summary_port import (
    StrategicIndicatorsAlertsSummaryPort,
)
from app.domain.services.strategic_indicators_calculator import (
    StrategicIndicatorsCalculator,
)


@dataclass(frozen=True)
class _DepartmentContext:
    current: StrategicDepartmentCalculatedValue
    previous: StrategicDepartmentCalculatedValue | None


class GetStrategicIndicatorsPresentationUseCase:
    def __init__(
        self,
        *,
        snapshot_service: StrategicIndicatorsSnapshotService,
        alerts_summary_port: StrategicIndicatorsAlertsSummaryPort,
        calculator: StrategicIndicatorsCalculator,
    ) -> None:
        self._snapshot_service = snapshot_service
        self._alerts_summary_port = alerts_summary_port
        self._calculator = calculator

    def execute(
        self,
        request: GetStrategicIndicatorsPresentationRequest,
    ) -> dict:
        months = max(2, min(request.months, 12))

        comparative = self._snapshot_service.get_current_and_previous_snapshot(
            competence=request.competence,
            start_date=request.start_date,
            end_date=request.end_date,
            department_id=None,
            branch=request.branch,
        )

        current_snapshot = comparative.current
        previous_snapshot = comparative.previous
        catalog_snapshot = comparative.catalog

        previous_departments_by_id = {
            item.department_id: item
            for item in previous_snapshot.calculated_departments
        }

        department_contexts = [
            _DepartmentContext(
                current=current_department,
                previous=previous_departments_by_id.get(current_department.department_id),
            )
            for current_department in current_snapshot.calculated_departments
        ]

        current_catalog_by_indicator_id = {
            item.indicator_id: item
            for item in catalog_snapshot.indicators_catalog
        }

        executive_summary = self._build_executive_summary(
            current_snapshot=current_snapshot,
            previous_snapshot=previous_snapshot,
            goals_by_department=catalog_snapshot.goals_by_department,
        )

        departments_overview = [
            self._build_department_overview_item(ctx)
            for ctx in department_contexts
        ]

        indicators_by_department_id = self._build_indicators_by_department_id(
            current_snapshot=current_snapshot,
        )

        department_details_by_id = {
            ctx.current.department_id: self._build_department_details_item(
                department_context=ctx,
                start_date=current_snapshot.period.start_date,
                end_date=current_snapshot.period.end_date,
                competence=current_snapshot.period.competence,
            )
            for ctx in department_contexts
        }

        alerts = self._build_alerts(
            current_snapshot=current_snapshot,
            catalog_by_indicator_id=current_catalog_by_indicator_id,
        )

        trends = self._build_trends(
            competence=request.competence,
            months=months,
            branch=request.branch,
        )

        errors = self._merge_errors(
            current_errors=current_snapshot.measurement_errors,
            trends_errors=trends["errors"],
        )

        partial_success = len(errors) > 0

        return {
            "executive_summary": executive_summary,
            "departments_overview": departments_overview,
            "department_details_by_id": department_details_by_id,
            "indicators_by_department_id": indicators_by_department_id,
            "alerts": alerts,
            "trends": trends,
            "meta": {
                "partial_success": partial_success,
                "errors": errors,
            },
        }

    def _build_executive_summary(
        self,
        *,
        current_snapshot,
        previous_snapshot,
        goals_by_department: dict[str, str],
    ) -> dict:
        previous_by_id = {
            item.department_id: item
            for item in previous_snapshot.calculated_departments
        }

        variation = self._calculator.calculate_variation(
            current_snapshot.igd_exact,
            previous_snapshot.igd_exact,
            decimals=3,
        )

        return {
            "competence": current_snapshot.period.competence,
            "igd": current_snapshot.igd,
            "igd_exact": current_snapshot.igd_exact,
            "classification": current_snapshot.classification,
            "variation": {
                "value": round(float(variation["value"]), 1),
                "direction": variation["direction"],
                "vs_label": "vs período anterior",
            },
            "departments": [
                self._map_executive_department(
                    current=item,
                    previous=previous_by_id.get(item.department_id),
                    goals_by_department=goals_by_department,
                )
                for item in current_snapshot.calculated_departments
            ],
            "alerts_summary": self._alerts_summary_port.get_alerts_summary(
                departments=current_snapshot.calculated_departments,
                measurement_errors=current_snapshot.measurement_errors,
            ),
            "errors": current_snapshot.measurement_errors,
            "partial_success": len(current_snapshot.measurement_errors) > 0,
        }

    def _map_executive_department(
        self,
        *,
        current,
        previous,
        goals_by_department: dict[str, str],
    ) -> dict:
        previous_score = previous.score if previous is not None else current.score
        trend = self._calculator.resolve_trend_direction(
            current=current.score,
            previous=previous_score,
        )
        variation = self._calculator.calculate_variation(
            current.score,
            previous_score,
            decimals=3,
        )

        return {
            "id": current.department_id,
            "name": current.department_name,
            "short_name": current.short_name,
            "weight_pct": current.weight_pct,
            "score": current.score,
            "contribution": current.contribution,
            "trend": trend,
            "strategic_summary": current.strategic_summary,
            "key_indicators": [
                indicator.indicator_name for indicator in current.indicators[:3]
            ],
            "executive_goal": goals_by_department.get(current.department_id, ""),
            "variation": {
                "value": float(variation["value"]),
                "direction": variation["direction"],
            },
        }

    def _build_department_overview_item(self, context: _DepartmentContext) -> dict:
        current = context.current
        previous = context.previous

        previous_score = previous.score if previous is not None else current.score
        variation = self._calculator.calculate_variation(
            current.score,
            previous_score,
            decimals=3,
        )

        return {
            "id": current.department_id,
            "name": current.department_name,
            "short_name": current.short_name,
            "weight_pct": current.weight_pct,
            "score": current.score,
            "classification": current.classification,
            "contribution": current.contribution,
            "aggregation_mode": current.aggregation_mode,
            "strategic_summary": current.strategic_summary,
            "variation": {
                "value": float(variation["value"]),
                "direction": variation["direction"],
            },
        }

    def _build_department_details_item(
        self,
        *,
        department_context: _DepartmentContext,
        start_date: str | None,
        end_date: str | None,
        competence: str | None,
    ) -> dict:
        current_department = department_context.current
        previous_department = department_context.previous

        previous_indicators_by_id = {
            item.indicator_id: item
            for item in (previous_department.indicators if previous_department else [])
        }

        previous_score = (
            previous_department.score
            if previous_department is not None
            else current_department.score
        )
        department_variation = self._calculator.calculate_variation(
            current_department.score,
            previous_score,
            decimals=3,
        )

        return {
            "id": current_department.department_id,
            "name": current_department.department_name,
            "short_name": current_department.short_name,
            "weight_pct": current_department.weight_pct,
            "score": current_department.score,
            "classification": current_department.classification,
            "contribution": current_department.contribution,
            "aggregation_mode": current_department.aggregation_mode,
            "strategic_summary": current_department.strategic_summary,
            "variation": {
                "value": float(department_variation["value"]),
                "direction": department_variation["direction"],
            },
            "units": self._build_units(
                current_department,
                start_date=start_date,
                end_date=end_date,
                competence=competence,
            ),
            "indicators": [
                self._map_department_indicator(
                    current=indicator,
                    previous=previous_indicators_by_id.get(indicator.indicator_id),
                )
                for indicator in current_department.indicators
            ],
            "errors": [],
            "partial_success": False,
        }

    def _map_department_indicator(self, *, current, previous) -> dict:
        previous_score = previous.score if previous is not None else current.score
        trend = self._calculator.resolve_trend_direction(
            current=current.score,
            previous=previous_score,
        )

        return {
            "id": current.indicator_id,
            "name": current.indicator_name,
            "weight_pct": current.weight_pct,
            "goal_label": current.goal_label,
            "goal_value": current.goal_value,
            "goal_periodicity": current.goal_periodicity,
            "goal_mode": getattr(current, "goal_mode", "standard"),
            "monthly_targets": getattr(current, "monthly_targets", []) or [],
            "strategic_description": current.strategic_description,
            "scope_type": current.scope_type,
            "performance_direction": getattr(
                current,
                "performance_direction",
                "higher_is_better",
            ),
            "realized": current.unit_values or {"consolidated": current.value},
            "score": current.score,
            "gap": current.gap,
            "trend": trend,
        }

    def _build_units(
        self,
        department,
        *,
        start_date: str | None,
        end_date: str | None,
        competence: str | None,
    ) -> list[dict]:
        unit_scores: dict[str, list[float]] = {}

        for indicator in department.indicators:
            if not indicator.unit_values:
                continue

            comparable_goal = self._calculator.calculate_comparable_goal(
                goal_value=indicator.goal_value,
                goal_periodicity=indicator.goal_periodicity,
                goal_mode=getattr(indicator, "goal_mode", "standard"),
                monthly_targets=getattr(indicator, "monthly_targets", None),
                start_date=start_date,
                end_date=end_date,
                competence=competence,
            )

            for unit_id, raw_value in indicator.unit_values.items():
                unit_score = self._calculator.calculate_indicator_score(
                    performance_direction=getattr(
                        indicator,
                        "performance_direction",
                        "higher_is_better",
                    ),
                    comparable_goal=comparable_goal,
                    value=float(raw_value),
                )
                unit_scores.setdefault(unit_id, []).append(unit_score)

        units: list[dict] = []
        for unit_id, scores in unit_scores.items():
            if not scores:
                continue

            avg_score = round(sum(scores) / len(scores), 3)
            units.append(
                {
                    "unit_id": unit_id,
                    "unit_name": self._resolve_unit_name(unit_id),
                    "score": avg_score,
                    "classification": self._calculator.classify_score(avg_score),
                }
            )

        return units

    def _resolve_unit_name(self, unit_id: str) -> str:
        if unit_id == "matrix":
            return "Matriz"
        if unit_id == "branch":
            return "Filial"
        if unit_id == "consolidated":
            return "Consolidado"
        return unit_id

    def _build_indicators_by_department_id(self, *, current_snapshot) -> dict[str, list[dict]]:
        grouped: dict[str, list[dict]] = {}

        departments_by_id = {
            item.department_id: item
            for item in current_snapshot.calculated_departments
        }

        for item in current_snapshot.calculated_indicators:
            department = departments_by_id[item.department_id]

            grouped.setdefault(item.department_id, []).append(
                {
                    "department_id": item.department_id,
                    "department_name": department.department_name,
                    "indicator_id": item.indicator_id,
                    "indicator_name": item.indicator_name,
                    "weight_pct": int(item.weight_pct),
                    "goal_label": item.goal_label,
                    "goal_value": float(item.goal_value),
                    "goal_periodicity": item.goal_periodicity,
                    "goal_mode": getattr(item, "goal_mode", "standard"),
                    "monthly_targets": getattr(item, "monthly_targets", []) or [],
                    "scope_type": item.scope_type,
                    "performance_direction": getattr(
                        item,
                        "performance_direction",
                        "higher_is_better",
                    ),
                    "value": float(item.value),
                    "score": float(item.score),
                    "gap": float(item.gap),
                    "trend": item.trend,
                    "classification": item.classification,
                    "source": item.source,
                }
            )

        for department_id in departments_by_id.keys():
            grouped.setdefault(department_id, [])

        return grouped

    def _build_alerts(
        self,
        *,
        current_snapshot,
        catalog_by_indicator_id: dict,
    ) -> dict:
        executive_alerts = self._alerts_summary_port.get_alerts_summary(
            departments=current_snapshot.calculated_departments,
            measurement_errors=current_snapshot.measurement_errors,
        )

        department_alerts = self._build_department_alerts(
            current_snapshot.calculated_departments
        )
        indicator_alerts = self._build_indicator_alerts(
            current_snapshot.calculated_departments,
            catalog_by_indicator_id,
        )

        return {
            "competence": current_snapshot.period.competence,
            "executive_alerts": executive_alerts,
            "department_alerts": department_alerts,
            "indicator_alerts": indicator_alerts,
            "errors": current_snapshot.measurement_errors,
            "partial_success": len(current_snapshot.measurement_errors) > 0,
        }

    def _build_department_alerts(self, departments) -> list[dict]:
        ordered = sorted(departments, key=lambda item: item.score)
        alerts: list[dict] = []

        for department in ordered[:5]:
            if department.score >= 8:
                continue

            severity = "high" if department.score < 7 else "medium"

            alerts.append(
                {
                    "department_id": department.department_id,
                    "department_name": department.department_name,
                    "severity": severity,
                    "score": department.score,
                    "classification": department.classification,
                    "contribution": department.contribution,
                    "message": (
                        f"{department.department_name} está com score "
                        f"{department.score:.1f} e exige acompanhamento."
                    ),
                }
            )

        return alerts

    def _build_indicator_alerts(
        self,
        departments,
        catalog_by_indicator_id: dict,
    ) -> list[dict]:
        candidates: list[dict] = []

        for department in departments:
            for indicator in department.indicators:
                if indicator.score >= 8:
                    continue

                severity = "high" if indicator.score < 7 else "medium"
                catalog_item = catalog_by_indicator_id.get(indicator.indicator_id)

                candidates.append(
                    {
                        "department_id": department.department_id,
                        "department_name": department.department_name,
                        "indicator_id": indicator.indicator_id,
                        "indicator_name": indicator.indicator_name,
                        "severity": severity,
                        "score": indicator.score,
                        "gap": indicator.gap,
                        "classification": indicator.classification,
                        "source": indicator.source,
                        "goal_label": catalog_item.goal_label if catalog_item else None,
                        "goal_value": catalog_item.goal_value if catalog_item else None,
                        "goal_periodicity": (
                            catalog_item.goal_periodicity if catalog_item else None
                        ),
                        "goal_mode": (
                            getattr(catalog_item, "goal_mode", "standard")
                            if catalog_item
                            else "standard"
                        ),
                        "monthly_targets": (
                            getattr(catalog_item, "monthly_targets", []) or []
                            if catalog_item
                            else []
                        ),
                        "performance_direction": (
                            getattr(
                                catalog_item,
                                "performance_direction",
                                "higher_is_better",
                            )
                            if catalog_item
                            else "higher_is_better"
                        ),
                        "message": (
                            f"{indicator.indicator_name} está abaixo do esperado em "
                            f"{department.department_name}."
                        ),
                    }
                )

        candidates.sort(key=lambda item: item["score"])
        return candidates[:8]

    def _build_trends(
        self,
        *,
        competence: str | None,
        months: int,
        branch: str | None,
    ) -> dict:
        reference = self._parse_competence(competence)
        periods = self._build_periods(reference, months)

        snapshots = self._snapshot_service.get_series_snapshot(
            periods=periods,
            department_id=None,
            branch=branch,
        )

        monthly_points: list[dict] = []
        monthly_departments: dict[str, list[dict]] = {}
        errors: list[dict] = []

        for snapshot in snapshots:
            monthly_points.append(
                {
                    "period": snapshot.period.competence,
                    "value": snapshot.igd,
                    "classification": snapshot.classification,
                }
            )

            for department in snapshot.calculated_departments:
                monthly_departments.setdefault(department.department_id, []).append(
                    {
                        "period": snapshot.period.competence,
                        "score": department.score,
                        "name": department.department_name,
                        "classification": department.classification,
                        "contribution": department.contribution,
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

            best_point = max(series, key=lambda item: item["score"])
            worst_point = min(series, key=lambda item: item["score"])

            interval_direction = self._resolve_direction(
                current["score"],
                first["score"],
            )

            last_step_direction = self._resolve_direction(
                current["score"],
                previous["score"],
            )

            departments.append(
                {
                    "id": department_id,
                    "name": current["name"],
                    "current": current["score"],
                    "previous": previous["score"],
                    "direction": interval_direction,
                    "last_step_direction": last_step_direction,
                    "net_variation": round(current["score"] - first["score"], 3),
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

        return {
            "competence": current_point["period"],
            "current_igd": current_point["value"],
            "previous_igd": previous_point["value"],
            "current_classification": current_point["classification"],
            "igd_series": monthly_points,
            "departments": departments,
            "errors": errors,
            "partial_success": len(errors) > 0,
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

    def _merge_errors(
        self,
        *,
        current_errors: list[dict],
        trends_errors: list[dict],
    ) -> list[dict]:
        merged: list[dict] = []

        for error in current_errors:
            merged.append(
                {
                    "scope": "current_period",
                    "competence": None,
                    "department_id": error.get("department_id"),
                    "source": error.get("source"),
                    "message": error.get("message"),
                }
            )

        for error in trends_errors:
            merged.append(
                {
                    "scope": "trend_series",
                    "competence": error.get("competence"),
                    "department_id": error.get("department_id"),
                    "source": error.get("source"),
                    "message": error.get("message"),
                }
            )

        return merged