from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

from app.application.dto.strategic_indicators.catalog_models import (
    StrategicDepartmentCalculatedValue,
    StrategicDepartmentCatalogItem,
    StrategicIndicatorCalculatedValue,
    StrategicIndicatorCatalogItem,
    StrategicIndicatorMeasuredValue,
)


class StrategicIndicatorsCalculator:
    def build_period_snapshot(
        self,
        *,
        period,
        departments_catalog: list[StrategicDepartmentCatalogItem],
        indicators_catalog: list[StrategicIndicatorCatalogItem],
        measurements_result,
        goals_by_department: dict[str, str] | None = None,
        department_id: str | None = None,
    ):
        measurements, measurement_errors = measurements_result
        goals_by_department = goals_by_department or {}

        calculated_indicators = self.calculate_indicators(
            indicators_catalog=indicators_catalog,
            measurements=measurements,
            department_id=department_id,
            start_date=getattr(period, "start_date", None),
            end_date=getattr(period, "end_date", None),
            competence=getattr(period, "competence", None),
        )

        calculated_departments = self.calculate_departments(
            departments_catalog=departments_catalog,
            indicators_catalog=indicators_catalog,
            measurements=measurements,
            start_date=getattr(period, "start_date", None),
            end_date=getattr(period, "end_date", None),
            competence=getattr(period, "competence", None),
        )

        if department_id:
            calculated_departments = [
                item
                for item in calculated_departments
                if item.department_id == department_id
            ]

        enriched_departments: list[StrategicDepartmentCalculatedValue] = []
        for department in calculated_departments:
            strategic_summary = goals_by_department.get(
                department.department_id,
                department.strategic_summary,
            )

            enriched_departments.append(
                StrategicDepartmentCalculatedValue(
                    department_id=department.department_id,
                    department_name=department.department_name,
                    short_name=department.short_name,
                    weight_pct=department.weight_pct,
                    strategic_summary=strategic_summary,
                    aggregation_mode=department.aggregation_mode,
                    score=department.score,
                    contribution=department.contribution,
                    classification=department.classification,
                    trend=department.trend,
                    indicators=department.indicators,
                )
            )

        igd, igd_exact, igd_classification = self.calculate_igd(enriched_departments)

        return SimpleNamespace(
            competence=getattr(period, "competence", None),
            start_date=getattr(period, "start_date", None),
            end_date=getattr(period, "end_date", None),
            months=getattr(period, "months", None),
            indicators=calculated_indicators,
            departments=enriched_departments,
            measurement_errors=measurement_errors,
            igd=igd,
            igd_exact=igd_exact,
            igd_classification=igd_classification,
        )

    def calculate_indicators(
        self,
        *,
        indicators_catalog: list[StrategicIndicatorCatalogItem],
        measurements: list[StrategicIndicatorMeasuredValue],
        department_id: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        competence: str | None = None,
    ) -> list[StrategicIndicatorCalculatedValue]:
        measurements_by_indicator = {
            item.indicator_id: item for item in measurements
        }

        calculated: list[StrategicIndicatorCalculatedValue] = []

        for indicator in indicators_catalog:
            if department_id and indicator.department_id != department_id:
                continue

            measurement = measurements_by_indicator.get(indicator.indicator_id)
            if measurement is None:
                continue

            comparable_goal = self.calculate_comparable_goal(
                goal_value=indicator.goal_value,
                goal_periodicity=indicator.goal_periodicity,
                goal_mode=getattr(indicator, "goal_mode", "standard"),
                monthly_targets=getattr(indicator, "monthly_targets", None),
                start_date=start_date,
                end_date=end_date,
                competence=competence,
            )

            performance_direction = getattr(
                indicator,
                "performance_direction",
                "higher_is_better",
            )

            score = self.calculate_indicator_score(
                performance_direction=performance_direction,
                comparable_goal=comparable_goal,
                value=measurement.value,
            )
            gap = self.calculate_indicator_gap(
                performance_direction=performance_direction,
                comparable_goal=comparable_goal,
                value=measurement.value,
            )

            calculated.append(
                StrategicIndicatorCalculatedValue(
                    indicator_id=indicator.indicator_id,
                    department_id=indicator.department_id,
                    indicator_name=indicator.indicator_name,
                    weight_pct=indicator.weight_pct,
                    goal_label=indicator.goal_label,
                    goal_value=indicator.goal_value,
                    goal_periodicity=indicator.goal_periodicity,
                    goal_mode=getattr(indicator, "goal_mode", "standard"),
                    monthly_targets=getattr(indicator, "monthly_targets", None),
                    scope_type=indicator.scope_type,
                    performance_direction=performance_direction,
                    strategic_description=indicator.strategic_description,
                    source=measurement.source,
                    value=(
                        round(measurement.value, 2)
                        if measurement.value is not None
                        else None
                    ),
                    score=score,
                    gap=gap,
                    trend="stable",
                    classification=self.classify_score(score),
                    unit_values=measurement.unit_values,
                )
            )

        return calculated

    def calculate_departments(
        self,
        *,
        departments_catalog: list[StrategicDepartmentCatalogItem],
        indicators_catalog: list[StrategicIndicatorCatalogItem],
        measurements: list[StrategicIndicatorMeasuredValue],
        start_date: str | None = None,
        end_date: str | None = None,
        competence: str | None = None,
    ) -> list[StrategicDepartmentCalculatedValue]:
        indicators_by_department: dict[str, list[StrategicIndicatorCalculatedValue]] = {}

        for item in self.calculate_indicators(
            indicators_catalog=indicators_catalog,
            measurements=measurements,
            start_date=start_date,
            end_date=end_date,
            competence=competence,
        ):
            indicators_by_department.setdefault(item.department_id, []).append(item)

        calculated_departments: list[StrategicDepartmentCalculatedValue] = []

        for department in departments_catalog:
            calculated_indicators = indicators_by_department.get(
                department.department_id, []
            )

            department_score = self._calculate_department_score(calculated_indicators)
            contribution = round((department_score * department.weight_pct) / 100.0, 2)

            calculated_departments.append(
                StrategicDepartmentCalculatedValue(
                    department_id=department.department_id,
                    department_name=department.department_name,
                    short_name=department.short_name,
                    weight_pct=department.weight_pct,
                    strategic_summary=department.strategic_summary,
                    aggregation_mode=department.aggregation_mode,
                    score=department_score,
                    contribution=contribution,
                    classification=self.classify_score(department_score),
                    trend="stable",
                    indicators=calculated_indicators,
                )
            )

        return calculated_departments

    def calculate_igd(
        self,
        departments: list[StrategicDepartmentCalculatedValue],
    ) -> tuple[float, float, str]:
        igd_exact = round(sum(item.contribution for item in departments), 2)
        igd = round(igd_exact, 2)
        classification = self.classify_score(igd)
        return igd, igd_exact, classification

    def calculate_comparable_goal(
        self,
        *,
        goal_value: float,
        goal_periodicity: str,
        goal_mode: str = "standard",
        monthly_targets: list[dict] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        competence: str | None = None,
    ) -> float:
        normalized_goal_mode = (goal_mode or "standard").strip().lower()

        if normalized_goal_mode == "monthly_curve":
            return self._calculate_monthly_curve_goal(
                monthly_targets=monthly_targets or [],
                start_date=start_date,
                end_date=end_date,
                competence=competence,
            )

        if goal_value <= 0:
            return 0.0

        periodicity = (goal_periodicity or "monthly").strip().lower()
        months = self._resolve_period_months(
            start_date=start_date,
            end_date=end_date,
            competence=competence,
        )

        if periodicity == "monthly":
            return round(goal_value * months, 2)

        if periodicity == "annual":
            return round((goal_value / 12.0) * months, 2)

        if periodicity == "quarterly":
            return round((goal_value / 3.0) * months, 2)

        if periodicity == "semiannual":
            return round((goal_value / 6.0) * months, 2)

        return round(goal_value, 2)

    def calculate_indicator_score(
        self,
        *,
        performance_direction: str,
        comparable_goal: float,
        value: float | None,
    ) -> float:
        lower_is_better = self._is_lower_better(performance_direction)

        if value is None:
            return 0.0

        if comparable_goal <= 0:
            return 0.0

        if lower_is_better:
            if value <= comparable_goal:
                return 10.0

            ratio = comparable_goal / value
            return round(min(ratio * 10.0, 10.0), 2)

        if value >= comparable_goal:
            return 10.0

        ratio = value / comparable_goal
        return round(min(ratio * 10.0, 10.0), 2)

    def calculate_indicator_gap(
        self,
        *,
        performance_direction: str,
        comparable_goal: float,
        value: float | None,
    ) -> float:
        lower_is_better = self._is_lower_better(performance_direction)

        if comparable_goal <= 0 or value is None:
            return 0.0

        if lower_is_better:
            return round(value - comparable_goal, 2)

        return round(comparable_goal - value, 2)

    def calculate_variation(
        self,
        current: float,
        previous: float,
        *,
        decimals: int = 2,
        tolerance: float = 0.09,
    ) -> dict[str, float | str]:
        delta = round(current - previous, decimals)
        return {
            "value": delta,
            "direction": self.resolve_trend_direction(
                current=current,
                previous=previous,
                tolerance=tolerance,
            ),
        }

    def resolve_trend_direction(
        self,
        *,
        current: float,
        previous: float,
        tolerance: float = 0.09,
    ) -> str:
        delta = current - previous

        if delta > tolerance:
            return "up"
        if delta < -tolerance:
            return "down"
        return "stable"

    def classify_score(self, score: float) -> str:
        if score >= 9:
            return "Excelência Integrada"
        if score >= 8:
            return "Alto Desempenho"
        if score >= 7:
            return "Satisfatório com Alertas"
        if score >= 6:
            return "Regular, Exige Ação"
        return "Crítico"

    def _calculate_department_score(
        self,
        indicators: list[StrategicIndicatorCalculatedValue],
    ) -> float:
        if not indicators:
            return 0.0

        total_weight = sum(item.weight_pct for item in indicators)
        if total_weight <= 0:
            return 0.0

        weighted_sum = sum(item.score * item.weight_pct for item in indicators)
        return round(weighted_sum / total_weight, 2)

    def _calculate_monthly_curve_goal(
        self,
        *,
        monthly_targets: list[dict],
        start_date: str | None,
        end_date: str | None,
        competence: str | None,
    ) -> float:
        if not monthly_targets:
            return 0.0

        targets_by_month: dict[int, float] = {}
        for item in monthly_targets:
            month_number = int(item.get("month_number") or 0)
            if month_number < 1 or month_number > 12:
                continue
            targets_by_month[month_number] = float(item.get("target_value") or 0)

        month_numbers = self._resolve_period_month_numbers(
            start_date=start_date,
            end_date=end_date,
            competence=competence,
        )

        comparable_goal = sum(
            targets_by_month.get(month_number, 0.0)
            for month_number in month_numbers
        )
        return round(comparable_goal, 2)

    def _resolve_period_month_numbers(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        competence: str | None,
    ) -> list[int]:
        normalized_competence = (competence or "").strip()

        if normalized_competence:
            parsed_competence = self._parse_competence_month(normalized_competence)
            if parsed_competence is not None:
                return [parsed_competence.month]

            if len(normalized_competence) >= 4 and normalized_competence[:4].isdigit():
                if start_date and end_date:
                    return self._resolve_month_numbers_from_dates(
                        start_date=start_date,
                        end_date=end_date,
                    )
                return list(range(1, 13))

        if start_date and end_date:
            return self._resolve_month_numbers_from_dates(
                start_date=start_date,
                end_date=end_date,
            )

        return [1]

    def _resolve_month_numbers_from_dates(
        self,
        *,
        start_date: str,
        end_date: str,
    ) -> list[int]:
        start = self._parse_date(start_date)
        end = self._parse_date(end_date)

        if start is None or end is None:
            return [1]

        if start > end:
            start, end = end, start

        month_numbers: list[int] = []
        cursor_year = start.year
        cursor_month = start.month

        while True:
            month_numbers.append(cursor_month)

            if cursor_year == end.year and cursor_month == end.month:
                break

            cursor_month += 1
            if cursor_month > 12:
                cursor_month = 1
                cursor_year += 1

        return month_numbers

    def _parse_competence_month(self, value: str):
        normalized = value.strip()

        known_formats = [
            "%Y-%m",
            "%m/%y",
            "%m/%Y",
            "%Y/%m",
        ]

        for fmt in known_formats:
            try:
                return datetime.strptime(normalized, fmt)
            except ValueError:
                continue

        month_aliases = {
            "jan": 1,
            "fev": 2,
            "mar": 3,
            "abr": 4,
            "mai": 5,
            "jun": 6,
            "jul": 7,
            "ago": 8,
            "set": 9,
            "out": 10,
            "nov": 11,
            "dez": 12,
        }

        lowered = normalized.lower()
        if "/" in lowered:
            maybe_month, maybe_year = lowered.split("/", 1)
            if maybe_month in month_aliases and maybe_year.isdigit():
                year = int(maybe_year)
                if year < 100:
                    year += 2000
                return datetime(
                    year=year,
                    month=month_aliases[maybe_month],
                    day=1,
                )

        return None

    def _resolve_period_months(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        competence: str | None,
    ) -> int:
        if competence and len(competence) == 7:
            return 1

        parsed_competence = self._parse_competence_month(competence or "")
        if parsed_competence is not None:
            return 1

        start = self._parse_date(start_date)
        end = self._parse_date(end_date)

        if start is None or end is None:
            if competence and len(competence) >= 4 and competence[:4].isdigit():
                return 12
            return 1

        months = ((end.year - start.year) * 12) + (end.month - start.month) + 1
        return max(1, months)

    def _parse_date(self, value: str | None):
        if not value:
            return None

        known_formats = [
            "%d-%m-%Y",
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%Y/%m/%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
        ]

        for fmt in known_formats:
            try:
                return datetime.strptime(value.strip(), fmt)
            except ValueError:
                continue

        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            return None

    def _is_lower_better(self, performance_direction: str | None) -> bool:
        return (performance_direction or "higher_is_better") == "lower_is_better"