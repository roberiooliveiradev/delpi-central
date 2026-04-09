from __future__ import annotations

from datetime import datetime

from app.application.dto.strategic_indicators.catalog_models import (
    StrategicDepartmentCalculatedValue,
    StrategicDepartmentCatalogItem,
    StrategicIndicatorCalculatedValue,
    StrategicIndicatorCatalogItem,
    StrategicIndicatorMeasuredValue,
)


class StrategicIndicatorsCalculator:
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
                start_date=start_date,
                end_date=end_date,
                competence=competence,
            )

            score = self.calculate_indicator_score(
                indicator_id=indicator.indicator_id,
                comparable_goal=comparable_goal,
                value=measurement.value,
            )
            gap = self.calculate_indicator_gap(
                indicator_id=indicator.indicator_id,
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
                    scope_type=indicator.scope_type,
                    strategic_description=indicator.strategic_description,
                    source=measurement.source,
                    value=measurement.value,
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
            contribution = round((department_score * department.weight_pct) / 100.0, 3)

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
        igd_exact = round(sum(item.contribution for item in departments), 3)
        igd = round(igd_exact, 1)
        classification = self.classify_score(igd)
        return igd, igd_exact, classification

    def calculate_comparable_goal(
        self,
        *,
        goal_value: float,
        goal_periodicity: str,
        start_date: str | None = None,
        end_date: str | None = None,
        competence: str | None = None,
    ) -> float:
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
        indicator_id: str,
        comparable_goal: float,
        value: float,
    ) -> float:
        lower_is_better = self._is_lower_better(indicator_id)

        if comparable_goal <= 0:
            return 0.0

        if lower_is_better:
            ratio = comparable_goal / value if value > 0 else 10.0
            return round(min(ratio * 10.0, 10.0), 2)

        ratio = value / comparable_goal
        return round(min(ratio * 10.0, 10.0), 2)

    def calculate_indicator_gap(
        self,
        *,
        indicator_id: str,
        comparable_goal: float,
        value: float,
    ) -> float:
        lower_is_better = self._is_lower_better(indicator_id)

        if comparable_goal <= 0:
            return 0.0

        if lower_is_better:
            return round(value - comparable_goal, 2)

        return round(comparable_goal - value, 2)

    def calculate_variation(
        self,
        current: float,
        previous: float,
        *,
        decimals: int = 3,
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
        return round(weighted_sum / total_weight, 3)

    def _resolve_period_months(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        competence: str | None,
    ) -> int:
        if competence and len(competence) == 7:
            return 1

        start = self._parse_date(start_date)
        end = self._parse_date(end_date)

        if start is None or end is None:
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

    def _is_lower_better(self, indicator_id: str) -> bool:
        negative_patterns = [
            "fixed-cost",
            "pmr",
            "absentee",
            "turnover",
            "cost",
            "depreciation",
            "ppm",
            "stock",
            "cpv",
        ]
        normalized = indicator_id.lower()
        return any(pattern in normalized for pattern in negative_patterns)