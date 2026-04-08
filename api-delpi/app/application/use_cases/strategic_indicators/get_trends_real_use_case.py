from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.domain.ports.strategic_indicators.departments_catalog_repository_port import (
    StrategicIndicatorsDepartmentsCatalogRepositoryPort,
)
from app.domain.ports.strategic_indicators.indicator_measurements_port import (
    StrategicIndicatorsIndicatorMeasurementsPort,
)
from app.domain.ports.strategic_indicators.indicators_catalog_repository_port import (
    StrategicIndicatorsIndicatorsCatalogRepositoryPort,
)
from app.domain.services.strategic_indicators_calculator import (
    StrategicIndicatorsCalculator,
)

from app.application.dto.strategic_indicators.get_trends_real_request import (
    GetStrategicIndicatorsTrendsRealRequest,
)


class GetStrategicIndicatorsTrendsRealUseCase:
    def __init__(
        self,
        *,
        departments_catalog_repository: StrategicIndicatorsDepartmentsCatalogRepositoryPort,
        indicators_catalog_repository: StrategicIndicatorsIndicatorsCatalogRepositoryPort,
        measurements_port: StrategicIndicatorsIndicatorMeasurementsPort,
        calculator: StrategicIndicatorsCalculator,
    ) -> None:
        self._departments_catalog_repository = departments_catalog_repository
        self._indicators_catalog_repository = indicators_catalog_repository
        self._measurements_port = measurements_port
        self._calculator = calculator

    def execute(
        self,
        request: GetStrategicIndicatorsTrendsRealRequest,
    ) -> dict:
        months = max(2, min(request.months, 12))
        reference = self._parse_competence(request.competence)

        departments_catalog = (
            self._departments_catalog_repository.list_departments_catalog()
        )
        indicators_catalog = self._indicators_catalog_repository.list_indicators_catalog()

        monthly_points: list[dict] = []
        monthly_departments: dict[str, list[dict]] = {}
        errors: list[dict] = []

        periods = self._build_periods(reference, months)

        for period in periods:
            start_date, end_date = self._build_month_range(period["year"], period["month"])

            measurements, measurement_errors = self._measurements_port.get_indicator_measurements(
                start_date=start_date,
                end_date=end_date,
            )

            calculated_departments = self._calculator.calculate_departments(
                departments_catalog=departments_catalog,
                indicators_catalog=indicators_catalog,
                measurements=measurements,
                start_date=start_date,
                end_date=end_date,
                competence=period["competence"],
            )

            igd, _igd_exact, classification = self._calculator.calculate_igd(
                calculated_departments
            )

            monthly_points.append(
                {
                    "period": period["competence"],
                    "value": igd,
                    "classification": classification,
                }
            )

            for department in calculated_departments:
                monthly_departments.setdefault(department.department_id, []).append(
                    {
                        "period": period["competence"],
                        "score": department.score,
                        "name": department.department_name,
                    }
                )

            for error in measurement_errors:
                errors.append(
                    {
                        "competence": period["competence"],
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

    def _build_periods(self, reference: date, months: int) -> list[dict]:
        periods: list[dict] = []

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

            periods.append(
                {
                    "year": current_year,
                    "month": current_month,
                    "competence": f"{current_year}-{str(current_month).zfill(2)}",
                }
            )

        return periods

    def _build_month_range(self, year: int, month: int) -> tuple[str, str]:
        from calendar import monthrange

        first_day = f"01-{str(month).zfill(2)}-{year}"
        last_day = monthrange(year, month)[1]
        last_date = f"{str(last_day).zfill(2)}-{str(month).zfill(2)}-{year}"
        return first_day, last_date

    def _resolve_direction(self, current: float, previous: float) -> str:
        delta = current - previous

        if delta > 0.09:
            return "up"
        if delta < -0.09:
            return "down"
        return "stable"