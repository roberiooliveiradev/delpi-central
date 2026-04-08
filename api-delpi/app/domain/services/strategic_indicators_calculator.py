from __future__ import annotations

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

            score = self.calculate_indicator_score(
                indicator_id=indicator.indicator_id,
                goal_text=indicator.goal_2026,
                value=measurement.value,
            )
            gap = self.calculate_indicator_gap(
                indicator_id=indicator.indicator_id,
                goal_text=indicator.goal_2026,
                value=measurement.value,
            )

            calculated.append(
                StrategicIndicatorCalculatedValue(
                    indicator_id=indicator.indicator_id,
                    department_id=indicator.department_id,
                    indicator_name=indicator.indicator_name,
                    weight_pct=indicator.weight_pct,
                    goal_2026=indicator.goal_2026,
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
    ) -> list[StrategicDepartmentCalculatedValue]:
        indicators_by_department: dict[str, list[StrategicIndicatorCalculatedValue]] = {}

        for item in self.calculate_indicators(
            indicators_catalog=indicators_catalog,
            measurements=measurements,
        ):
            indicators_by_department.setdefault(item.department_id, []).append(item)

        calculated_departments: list[StrategicDepartmentCalculatedValue] = []

        for department in departments_catalog:
            calculated_indicators = indicators_by_department.get(department.department_id, [])

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

    def calculate_indicator_score(
        self,
        *,
        indicator_id: str,
        goal_text: str,
        value: float,
    ) -> float:
        goal = self._extract_numeric_goal(goal_text)
        lower_is_better = self._is_lower_better(indicator_id)

        if goal <= 0:
            return 0.0

        if lower_is_better:
            ratio = goal / value if value > 0 else 10.0
            return round(min(ratio * 10.0, 10.0), 2)

        ratio = value / goal
        return round(min(ratio * 10.0, 10.0), 2)

    def calculate_indicator_gap(
        self,
        *,
        indicator_id: str,
        goal_text: str,
        value: float,
    ) -> float:
        goal = self._extract_numeric_goal(goal_text)
        lower_is_better = self._is_lower_better(indicator_id)

        if goal <= 0:
            return 0.0

        if lower_is_better:
            return round(value - goal, 2)

        return round(goal - value, 2)

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

    def _extract_numeric_goal(self, goal_text: str) -> float:
        cleaned = (
            goal_text.replace("R$", "")
            .replace("%", "")
            .replace("PPM", "")
            .replace("dias", "")
            .replace("mês", "")
            .replace("mes", "")
            .replace("ideias", "")
            .replace("novos", "")
            .strip()
        )

        cleaned = cleaned.split()[0] if cleaned else ""
        cleaned = cleaned.replace(".", "").replace(",", ".")

        try:
            return float(cleaned)
        except Exception:
            return 0.0

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