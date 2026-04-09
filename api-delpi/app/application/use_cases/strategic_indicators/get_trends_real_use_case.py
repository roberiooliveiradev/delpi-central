from __future__ import annotations

from calendar import monthrange
from datetime import date

from app.application.use_cases.strategic_indicators.period_resolution import (
    ResolvedPeriod,
)
from app.application.dto.strategic_indicators.get_trends_real_request import (
    GetStrategicIndicatorsTrendsRealRequest,
)
from app.application.services.strategic_indicators.strategic_indicators_snapshot_service import (
    StrategicIndicatorsSnapshotService,
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

        snapshots = self._snapshot_service.get_series_snapshot(periods=periods)

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
        previous_point = monthly_points[-2] if len(monthly_points) >= 2 else monthly_points[-1]

        departments = []
        for department_id, series in monthly_departments.items():
            current = series[-1]
            previous = series[-2] if len(series) >= 2 else series[-1]
            direction = self._resolve_direction(current["score"], previous["score"])

            departments.append(
                {
                    "id": department_id,
                    "name": current["name"],
                    "current": current["score"],
                    "previous": previous["score"],
                    "direction": direction,
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
            last_date = f"{str(last_day).zfill(2)}-{str(current_month).zfill(2)}-{current_year}"

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