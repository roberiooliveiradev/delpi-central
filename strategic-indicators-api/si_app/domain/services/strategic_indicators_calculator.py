from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

from si_app.application.dto.strategic_indicators.catalog_models import (
    StrategicDepartmentCalculatedValue,
    StrategicDepartmentCatalogItem,
    StrategicIndicatorCalculatedValue,
    StrategicIndicatorCatalogItem,
    StrategicIndicatorMeasuredValue,
)
from si_app.shared.branch_filter import (
    consolidated_measurement_value,
    is_consolidated_aggregation_department,
)
from si_app.shared.goal_scope import (
    BRANCH_UNIT_CODES,
    indicator_uses_branch_unit_measurement,
    normalize_goal_scope_branch,
)


class StrategicIndicatorsCalculator:
    MISSING_VALUE_CLASSIFICATION = "Sem dados preenchidos"
    MISSING_GOAL_CLASSIFICATION = "Sem meta para esta visão"

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
        scope_branch: str | None = None,
    ) -> list[StrategicIndicatorCalculatedValue]:
        measurements_by_indicator = {
            item.indicator_id: item for item in measurements
        }

        calculated: list[StrategicIndicatorCalculatedValue] = []
        active_branch = normalize_goal_scope_branch(scope_branch)

        for indicator in indicators_catalog:
            if department_id and indicator.department_id != department_id:
                continue

            measurement = measurements_by_indicator.get(indicator.indicator_id)
            if measurement is None:
                calculated.append(
                    self._build_missing_indicator_value(
                        indicator=indicator,
                        source="",
                        unit_values=None,
                    )
                )
                continue

            if measurement.value is None and not (
                indicator.branch_goals and measurement.unit_values
            ):
                calculated.append(
                    self._build_missing_indicator_value(
                        indicator=indicator,
                        source=measurement.source,
                        unit_values=measurement.unit_values,
                    )
                )
                continue

            performance_direction = getattr(
                indicator,
                "performance_direction",
                "higher_is_better",
            )

            scoring_branch = active_branch
            if (
                active_branch in BRANCH_UNIT_CODES
                and is_consolidated_aggregation_department(indicator.department_id)
            ):
                scoring_branch = ""

            if scoring_branch in BRANCH_UNIT_CODES:
                if not getattr(indicator, "has_resolved_goal", True):
                    calculated.append(
                        self._build_indicator_without_goal_for_view(
                            indicator=indicator,
                            measurement=measurement,
                            source=measurement.source,
                        )
                    )
                    continue

                if indicator_uses_branch_unit_measurement(
                    indicator_branch_goals=indicator.branch_goals,
                    resolved_goal_scope_branch=getattr(
                        indicator,
                        "resolved_goal_scope_branch",
                        "",
                    ),
                    view_branch=scoring_branch,
                ):
                    branch_indicator_score = self._calculate_indicator_for_branch_code(
                        indicator=indicator,
                        measurement=measurement,
                        branch_code=scoring_branch,
                        performance_direction=performance_direction,
                        start_date=start_date,
                        end_date=end_date,
                        competence=competence,
                    )
                    if branch_indicator_score is None:
                        calculated.append(
                            self._build_missing_indicator_value(
                                indicator=indicator,
                                source=measurement.source,
                                unit_values=measurement.unit_values,
                            )
                        )
                        continue

                    score, gap, realized_value = branch_indicator_score
                    unit_values = measurement.unit_values or {}
                    display_branch = active_branch
                    unit_gaps = (
                        {display_branch: gap}
                        if gap is not None
                        else {display_branch: None}
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
                                round(realized_value, 2)
                                if realized_value is not None
                                else None
                            ),
                            score=score,
                            gap=gap,
                            trend="stable",
                            classification=self.classify_score(score),
                            unit_values={
                                key: unit_values.get(key)
                                for key in (display_branch, "consolidated")
                                if key in unit_values
                            }
                            or None,
                            unit_gaps=unit_gaps,
                            value_unit=indicator.value_unit,
                            value_prefix=indicator.value_prefix,
                            value_suffix=indicator.value_suffix,
                            value_decimals=indicator.value_decimals,
                        )
                    )
                    continue

            branch_scoped_score = self._calculate_branch_scoped_indicator_score(
                indicator=indicator,
                measurement=measurement,
                performance_direction=performance_direction,
                start_date=start_date,
                end_date=end_date,
                competence=competence,
            )
            if branch_scoped_score is not None:
                score, gap, realized_value = branch_scoped_score
            else:
                realized_value = measurement.value
                if realized_value is None:
                    calculated.append(
                        self._build_missing_indicator_value(
                            indicator=indicator,
                            source=measurement.source,
                            unit_values=measurement.unit_values,
                        )
                    )
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
                if comparable_goal <= 0:
                    calculated.append(
                        self._build_indicator_without_goal_for_view(
                            indicator=indicator,
                            measurement=measurement,
                            source=measurement.source,
                        )
                    )
                    continue

                score = self.calculate_indicator_score(
                    performance_direction=performance_direction,
                    comparable_goal=comparable_goal,
                    value=realized_value,
                )
                gap = self.calculate_indicator_gap(
                    performance_direction=performance_direction,
                    comparable_goal=comparable_goal,
                    value=realized_value,
                )

            unit_gaps = self._build_unit_gaps(
                indicator=indicator,
                measurement=measurement,
                start_date=start_date,
                end_date=end_date,
                competence=competence,
            )
            unit_goals = self._build_unit_goals(
                indicator=indicator,
                measurement=measurement,
                start_date=start_date,
                end_date=end_date,
                competence=competence,
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
                        round(realized_value, 2)
                        if realized_value is not None
                        else None
                    ),
                    score=score,
                    gap=gap,
                    trend="stable",
                    classification=self.classify_score(score),
                    unit_values=measurement.unit_values,
                    unit_goals=unit_goals,
                    unit_gaps=unit_gaps,
                    value_unit=indicator.value_unit,
                    value_prefix=indicator.value_prefix,
                    value_suffix=indicator.value_suffix,
                    value_decimals=indicator.value_decimals,
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
        scope_branch: str | None = None,
        precalculated_indicators: list[StrategicIndicatorCalculatedValue] | None = None,
    ) -> list[StrategicDepartmentCalculatedValue]:
        indicators_by_department: dict[str, list[StrategicIndicatorCalculatedValue]] = {}

        calculated_indicators = (
            precalculated_indicators
            if precalculated_indicators is not None
            else self.calculate_indicators(
                indicators_catalog=indicators_catalog,
                measurements=measurements,
                start_date=start_date,
                end_date=end_date,
                competence=competence,
                scope_branch=scope_branch,
            )
        )

        for item in calculated_indicators:
            indicators_by_department.setdefault(item.department_id, []).append(item)

        calculated_departments: list[StrategicDepartmentCalculatedValue] = []

        measurements_by_indicator = {
            item.indicator_id: item for item in measurements
        }
        indicators_catalog_by_department: dict[str, list[StrategicIndicatorCatalogItem]] = {}
        for indicator in indicators_catalog:
            indicators_catalog_by_department.setdefault(
                indicator.department_id,
                [],
            ).append(indicator)

        for department in departments_catalog:
            calculated_indicators = indicators_by_department.get(
                department.department_id, []
            )
            department_catalog = indicators_catalog_by_department.get(
                department.department_id,
                [],
            )

            if (department.aggregation_mode or "").strip() == "average_of_units":
                department_score = self._calculate_department_score_average_of_units(
                    indicators_catalog=department_catalog,
                    measurements_by_indicator=measurements_by_indicator,
                    start_date=start_date,
                    end_date=end_date,
                    competence=competence,
                    filter_branch=normalize_goal_scope_branch(scope_branch) or None,
                )
            else:
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
                goal_periodicity=goal_periodicity,
                start_date=start_date,
                end_date=end_date,
                competence=competence,
            )

        return self._calculate_standard_period_goal(
            goal_value=goal_value,
            goal_periodicity=goal_periodicity,
            start_date=start_date,
            end_date=end_date,
            competence=competence,
        )

    def _calculate_standard_period_goal(
        self,
        *,
        goal_value: float,
        goal_periodicity: str,
        start_date: str | None,
        end_date: str | None,
        competence: str | None,
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
        current: float | None,
        previous: float | None,
        tolerance: float = 0.09,
    ) -> str:
        if current is None or previous is None:
            return "stable"

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

    def _calculate_branch_scoped_indicator_score(
        self,
        *,
        indicator: StrategicIndicatorCatalogItem,
        measurement: StrategicIndicatorMeasuredValue,
        performance_direction: str,
        start_date: str | None,
        end_date: str | None,
        competence: str | None,
    ) -> tuple[float, float | None, float | None] | None:
        branch_goals = indicator.branch_goals
        unit_values = measurement.unit_values
        if not branch_goals or not unit_values:
            return None

        branch_scores: list[float] = []
        branch_values: list[float] = []
        branch_gaps: list[float] = []

        for branch_code, branch_goal in branch_goals.items():
            branch_value = unit_values.get(branch_code)
            if branch_value is None:
                continue

            comparable_goal = self.calculate_comparable_goal(
                goal_value=float(branch_goal["goal_value"]),
                goal_periodicity=branch_goal["goal_periodicity"],
                goal_mode=branch_goal.get("goal_mode", "standard"),
                monthly_targets=branch_goal.get("monthly_targets") or [],
                start_date=start_date,
                end_date=end_date,
                competence=competence,
            )
            branch_scores.append(
                self.calculate_indicator_score(
                    performance_direction=performance_direction,
                    comparable_goal=comparable_goal,
                    value=float(branch_value),
                )
            )
            branch_gap = self.calculate_indicator_gap(
                performance_direction=performance_direction,
                comparable_goal=comparable_goal,
                value=float(branch_value),
            )
            if branch_gap is not None:
                branch_gaps.append(branch_gap)
            branch_values.append(float(branch_value))

        if not branch_scores:
            return None

        score = round(sum(branch_scores) / len(branch_scores), 2)
        gap = (
            round(sum(branch_gaps) / len(branch_gaps), 2)
            if branch_gaps
            else None
        )
        realized_value = round(sum(branch_values) / len(branch_values), 2)
        return score, gap, realized_value

    def _score_indicator_for_branch(
        self,
        *,
        indicator: StrategicIndicatorCatalogItem,
        measurement: StrategicIndicatorMeasuredValue,
        branch_code: str,
        start_date: str | None,
        end_date: str | None,
        competence: str | None,
    ) -> float | None:
        performance_direction = getattr(
            indicator,
            "performance_direction",
            "higher_is_better",
        )
        unit_values = measurement.unit_values or {}
        branch_value = unit_values.get(branch_code)
        branch_goal = (indicator.branch_goals or {}).get(branch_code)

        if branch_value is not None:
            comparable_goal = self._comparable_goal_for_branch_view(
                indicator=indicator,
                branch_code=branch_code,
                start_date=start_date,
                end_date=end_date,
                competence=competence,
            )
            if comparable_goal is None:
                return None
            return self.calculate_indicator_score(
                performance_direction=performance_direction,
                comparable_goal=comparable_goal,
                value=float(branch_value),
            )

        return None

    def _calculate_indicator_for_branch_code(
        self,
        *,
        indicator: StrategicIndicatorCatalogItem,
        measurement: StrategicIndicatorMeasuredValue,
        branch_code: str,
        performance_direction: str,
        start_date: str | None,
        end_date: str | None,
        competence: str | None,
    ) -> tuple[float, float | None, float | None] | None:
        unit_values = measurement.unit_values or {}
        realized_value = unit_values.get(branch_code)
        if realized_value is None:
            return None

        comparable_goal = self._comparable_goal_for_branch_view(
            indicator=indicator,
            branch_code=branch_code,
            start_date=start_date,
            end_date=end_date,
            competence=competence,
        )
        if comparable_goal is None:
            return None

        score = self.calculate_indicator_score(
            performance_direction=performance_direction,
            comparable_goal=comparable_goal,
            value=float(realized_value),
        )
        gap = self.calculate_indicator_gap(
            performance_direction=performance_direction,
            comparable_goal=comparable_goal,
            value=float(realized_value),
        )
        return score, gap, float(realized_value)

    def _calculate_department_score_average_of_units(
        self,
        *,
        indicators_catalog: list[StrategicIndicatorCatalogItem],
        measurements_by_indicator: dict[str, StrategicIndicatorMeasuredValue],
        start_date: str | None,
        end_date: str | None,
        competence: str | None,
        filter_branch: str | None = None,
    ) -> float:
        """IDD consolidado = média aritmética do IDD de cada filial (01, 02)."""
        branch_department_scores: list[float] = []
        branch_codes = (
            [filter_branch]
            if filter_branch in BRANCH_UNIT_CODES
            else list(BRANCH_UNIT_CODES)
        )

        for branch_code in branch_codes:
            weighted_scores: list[tuple[float, float]] = []

            for indicator in indicators_catalog:
                measurement = measurements_by_indicator.get(indicator.indicator_id)
                if measurement is None:
                    continue

                branch_score = self._score_indicator_for_branch(
                    indicator=indicator,
                    measurement=measurement,
                    branch_code=branch_code,
                    start_date=start_date,
                    end_date=end_date,
                    competence=competence,
                )
                if branch_score is None:
                    continue

                weighted_scores.append((branch_score, indicator.weight_pct))

            if not weighted_scores:
                continue

            total_weight = sum(weight for _, weight in weighted_scores)
            if total_weight <= 0:
                continue

            branch_department_scores.append(
                round(
                    sum(score * weight for score, weight in weighted_scores)
                    / total_weight,
                    2,
                )
            )

        if not branch_department_scores:
            return 0.0

        return round(
            sum(branch_department_scores) / len(branch_department_scores),
            2,
        )

    def _calculate_department_score(
        self,
        indicators: list[StrategicIndicatorCalculatedValue],
    ) -> float:
        scored_indicators = [
            item
            for item in indicators
            if item.value is not None and item.score is not None
        ]

        if not scored_indicators:
            return 0.0

        total_weight = sum(item.weight_pct for item in scored_indicators)
        if total_weight <= 0:
            return 0.0

        weighted_sum = sum(
            float(item.score) * item.weight_pct for item in scored_indicators
        )
        return round(weighted_sum / total_weight, 2)

    def _department_indicators_for_score(
        self,
        department: StrategicDepartmentCalculatedValue,
        *,
        indicators_by_department: dict[str, list[StrategicIndicatorCalculatedValue]]
        | None = None,
    ) -> list[StrategicIndicatorCalculatedValue]:
        nested = list(department.indicators)
        flat = (
            list(indicators_by_department.get(department.department_id, []))
            if indicators_by_department
            else []
        )

        if not nested:
            return flat

        if not flat:
            return nested

        return self._merge_indicator_scores(nested, flat)

    def _merge_indicator_scores(
        self,
        primary: list[StrategicIndicatorCalculatedValue],
        secondary: list[StrategicIndicatorCalculatedValue],
    ) -> list[StrategicIndicatorCalculatedValue]:
        merged: dict[str, StrategicIndicatorCalculatedValue] = {}

        for item in primary + secondary:
            existing = merged.get(item.indicator_id)
            if existing is None:
                merged[item.indicator_id] = item
                continue

            if existing.score is None and item.score is not None:
                merged[item.indicator_id] = item

        return list(merged.values())

    def _refresh_department_score(
        self,
        department: StrategicDepartmentCalculatedValue,
        *,
        indicators: list[StrategicIndicatorCalculatedValue],
        indicators_catalog: list[StrategicIndicatorCatalogItem] | None = None,
        measurements_by_indicator: dict[str, StrategicIndicatorMeasuredValue] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        competence: str | None = None,
        scope_branch: str | None = None,
    ) -> StrategicDepartmentCalculatedValue:
        aggregation_mode = (department.aggregation_mode or "").strip()

        if aggregation_mode == "average_of_units" and indicators_catalog and measurements_by_indicator:
            department_catalog = [
                item
                for item in indicators_catalog
                if item.department_id == department.department_id
            ]
            department_score = self._calculate_department_score_average_of_units(
                indicators_catalog=department_catalog,
                measurements_by_indicator=measurements_by_indicator,
                start_date=start_date,
                end_date=end_date,
                competence=competence,
                filter_branch=normalize_goal_scope_branch(scope_branch) or None,
            )
        else:
            department_score = self._calculate_department_score(indicators)

        return StrategicDepartmentCalculatedValue(
            department_id=department.department_id,
            department_name=department.department_name,
            short_name=department.short_name,
            weight_pct=department.weight_pct,
            strategic_summary=department.strategic_summary,
            aggregation_mode=department.aggregation_mode,
            score=department_score,
            contribution=round((department_score * department.weight_pct) / 100.0, 2),
            classification=self.classify_score(department_score),
            trend=department.trend,
            indicators=indicators,
        )

    def reconcile_period_snapshot_departments(
        self,
        *,
        calculated_departments: list[StrategicDepartmentCalculatedValue],
        calculated_indicators: list[StrategicIndicatorCalculatedValue] | None = None,
        indicators_catalog: list[StrategicIndicatorCatalogItem] | None = None,
        measurements: list[StrategicIndicatorMeasuredValue] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        competence: str | None = None,
        scope_branch: str | None = None,
    ) -> list[StrategicDepartmentCalculatedValue]:
        """
        Recalcula IDD/contribuição do departamento conforme `aggregation_mode`.

        - `consolidated`: média ponderada das notas dos indicadores já calculados.
        - `average_of_units`: média dos IDDs por filial (ou IDD da filial filtrada).
        """
        indicators_by_department: dict[str, list[StrategicIndicatorCalculatedValue]] = {}
        for item in calculated_indicators or []:
            indicators_by_department.setdefault(item.department_id, []).append(item)

        measurements_by_indicator = {
            item.indicator_id: item for item in (measurements or [])
        }

        reconciled: list[StrategicDepartmentCalculatedValue] = []
        for department in calculated_departments:
            indicators = sorted(
                self._department_indicators_for_score(
                    department,
                    indicators_by_department=indicators_by_department,
                ),
                key=lambda item: item.indicator_name,
            )
            refreshed = self._refresh_department_score(
                department,
                indicators=indicators,
                indicators_catalog=indicators_catalog,
                measurements_by_indicator=measurements_by_indicator,
                start_date=start_date,
                end_date=end_date,
                competence=competence,
                scope_branch=scope_branch,
            )
            reconciled.append(refreshed)

        return reconciled

    def _build_unit_gaps(
        self,
        *,
        indicator: StrategicIndicatorCatalogItem,
        measurement: StrategicIndicatorMeasuredValue,
        start_date: str | None,
        end_date: str | None,
        competence: str | None,
    ) -> dict[str, float | None] | None:
        unit_values = measurement.unit_values
        if not unit_values:
            return None

        branch_keys = [
            branch_code
            for branch_code in BRANCH_UNIT_CODES
            if branch_code in unit_values
        ]
        if not branch_keys and not indicator.branch_goals:
            return None

        if not branch_keys:
            branch_keys = [
                branch_code
                for branch_code in BRANCH_UNIT_CODES
                if branch_code in (indicator.branch_goals or {})
            ]

        if len(branch_keys) < 2:
            return None

        performance_direction = getattr(
            indicator,
            "performance_direction",
            "higher_is_better",
        )
        gaps: dict[str, float | None] = {}

        for branch_code in branch_keys:
            raw_value = unit_values.get(branch_code)
            if raw_value is None:
                gaps[branch_code] = None
                continue

            comparable_goal = self._comparable_goal_for_branch_view(
                indicator=indicator,
                branch_code=branch_code,
                start_date=start_date,
                end_date=end_date,
                competence=competence,
            )
            if comparable_goal is None:
                gaps[branch_code] = None
                continue

            gaps[branch_code] = self.calculate_indicator_gap(
                performance_direction=performance_direction,
                comparable_goal=comparable_goal,
                value=float(raw_value),
            )

        return gaps

    def _build_unit_goals(
        self,
        *,
        indicator: StrategicIndicatorCatalogItem,
        measurement: StrategicIndicatorMeasuredValue,
        start_date: str | None,
        end_date: str | None,
        competence: str | None,
    ) -> dict[str, float | None] | None:
        unit_values = measurement.unit_values
        branch_keys = [
            branch_code
            for branch_code in BRANCH_UNIT_CODES
            if branch_code in (indicator.branch_goals or {})
        ]
        if not branch_keys and unit_values:
            branch_keys = [
                branch_code
                for branch_code in BRANCH_UNIT_CODES
                if branch_code in unit_values
            ]

        if len(branch_keys) < 2:
            return None

        goals: dict[str, float | None] = {}
        for branch_code in branch_keys:
            comparable_goal = self._comparable_goal_for_branch_view(
                indicator=indicator,
                branch_code=branch_code,
                start_date=start_date,
                end_date=end_date,
                competence=competence,
            )
            if comparable_goal is None or comparable_goal <= 0:
                goals[branch_code] = None
                continue
            goals[branch_code] = round(float(comparable_goal), 2)

        return goals if goals else None

    def build_realized_payload(
        self,
        *,
        unit_values: dict[str, float | None] | None,
        value: float | None,
        department_id: str | None = None,
    ) -> dict[str, float | None]:
        if is_consolidated_aggregation_department(department_id):
            return {
                "consolidated": consolidated_measurement_value(
                    value=value,
                    unit_values=unit_values,
                )
            }

        if unit_values:
            return dict(unit_values)

        return {"consolidated": value}

    def build_gaps_payload(
        self,
        *,
        unit_gaps: dict[str, float | None] | None,
        gap: float | None,
        department_id: str | None = None,
    ) -> dict[str, float | None]:
        if is_consolidated_aggregation_department(department_id):
            if gap is None:
                return {}
            return {"consolidated": gap}

        if unit_gaps:
            return dict(unit_gaps)

        if gap is None:
            return {}

        return {"consolidated": gap}

    def resolve_unit_goals_for_response(
        self,
        *,
        calculated: StrategicIndicatorCalculatedValue,
        catalog_item: StrategicIndicatorCatalogItem | None,
        start_date: str | None,
        end_date: str | None,
        competence: str | None,
    ) -> dict[str, float | None] | None:
        stored = getattr(calculated, "unit_goals", None)
        if stored:
            return stored

        if not catalog_item or not (catalog_item.branch_goals or {}):
            return None

        unit_values = calculated.unit_values
        if not unit_values:
            return None

        measurement = StrategicIndicatorMeasuredValue(
            indicator_id=calculated.indicator_id,
            department_id=calculated.department_id,
            value=calculated.value,
            source=getattr(calculated, "source", "") or "",
            unit_values=unit_values,
        )
        return self._build_unit_goals(
            indicator=catalog_item,
            measurement=measurement,
            start_date=start_date,
            end_date=end_date,
            competence=competence,
        )

    def resolve_goals_payload_for_calculated(
        self,
        *,
        calculated: StrategicIndicatorCalculatedValue,
        catalog_item: StrategicIndicatorCatalogItem | None,
        start_date: str | None,
        end_date: str | None,
        competence: str | None,
    ) -> dict[str, float | None]:
        unit_goals = self.resolve_unit_goals_for_response(
            calculated=calculated,
            catalog_item=catalog_item,
            start_date=start_date,
            end_date=end_date,
            competence=competence,
        )
        return self.build_goals_payload(
            unit_goals=unit_goals,
            goal_value=calculated.goal_value,
            department_id=calculated.department_id,
        )

    def build_goals_payload(
        self,
        *,
        unit_goals: dict[str, float | None] | None,
        goal_value: float | None,
        department_id: str | None = None,
    ) -> dict[str, float | None]:
        if is_consolidated_aggregation_department(department_id):
            if goal_value is None:
                return {}
            return {"consolidated": goal_value}

        if unit_goals:
            return dict(unit_goals)

        if goal_value is None:
            return {}

        return {"consolidated": goal_value}

    def indicator_has_value(self, value: float | None) -> bool:
        return value is not None

    def _comparable_goal_for_branch_view(
        self,
        *,
        indicator: StrategicIndicatorCatalogItem,
        branch_code: str,
        start_date: str | None,
        end_date: str | None,
        competence: str | None,
    ) -> float | None:
        branch_goal = (indicator.branch_goals or {}).get(branch_code)
        if branch_goal:
            return self.calculate_comparable_goal(
                goal_value=float(branch_goal["goal_value"]),
                goal_periodicity=branch_goal["goal_periodicity"],
                goal_mode=branch_goal.get("goal_mode", "standard"),
                monthly_targets=branch_goal.get("monthly_targets") or [],
                start_date=start_date,
                end_date=end_date,
                competence=competence,
            )

        resolved_scope = normalize_goal_scope_branch(
            getattr(indicator, "resolved_goal_scope_branch", ""),
        )
        if resolved_scope == normalize_goal_scope_branch(branch_code) and getattr(
            indicator,
            "has_resolved_goal",
            True,
        ):
            return self.calculate_comparable_goal(
                goal_value=indicator.goal_value,
                goal_periodicity=indicator.goal_periodicity,
                goal_mode=getattr(indicator, "goal_mode", "standard"),
                monthly_targets=getattr(indicator, "monthly_targets", None),
                start_date=start_date,
                end_date=end_date,
                competence=competence,
            )

        return None

    def _build_indicator_without_goal_for_view(
        self,
        *,
        indicator: StrategicIndicatorCatalogItem,
        measurement: StrategicIndicatorMeasuredValue,
        source: str,
    ) -> StrategicIndicatorCalculatedValue:
        realized_value = measurement.value
        return StrategicIndicatorCalculatedValue(
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
            performance_direction=getattr(
                indicator,
                "performance_direction",
                "higher_is_better",
            ),
            strategic_description=indicator.strategic_description,
            source=source,
            value=(
                round(realized_value, 2)
                if realized_value is not None
                else None
            ),
            score=None,
            gap=None,
            trend="stable",
            classification=(
                self.MISSING_GOAL_CLASSIFICATION
                if realized_value is not None
                else self.MISSING_VALUE_CLASSIFICATION
            ),
            unit_values=None,
            value_unit=indicator.value_unit,
            value_prefix=indicator.value_prefix,
            value_suffix=indicator.value_suffix,
            value_decimals=indicator.value_decimals,
        )

    def _build_missing_indicator_value(
        self,
        *,
        indicator: StrategicIndicatorCatalogItem,
        source: str,
        unit_values: dict[str, float | None] | None,
    ) -> StrategicIndicatorCalculatedValue:
        return StrategicIndicatorCalculatedValue(
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
            performance_direction=getattr(
                indicator,
                "performance_direction",
                "higher_is_better",
            ),
            strategic_description=indicator.strategic_description,
            source=source,
            value=None,
            score=None,
            gap=None,
            trend="stable",
            classification=self.MISSING_VALUE_CLASSIFICATION,
            unit_values=unit_values,
            value_unit=indicator.value_unit,
            value_prefix=indicator.value_prefix,
            value_suffix=indicator.value_suffix,
            value_decimals=indicator.value_decimals,
        )

    def _calculate_monthly_curve_goal(
        self,
        *,
        monthly_targets: list[dict],
        goal_periodicity: str,
        start_date: str | None,
        end_date: str | None,
        competence: str | None,
    ) -> float:
        if not monthly_targets:
            return 0.0

        from si_app.application.services.strategic_indicators.goal_value_policy import (
            curve_point_indices_for_calendar_months,
            expected_monthly_curve_points,
            parse_year_from_competence,
        )

        max_points = expected_monthly_curve_points(goal_periodicity)
        targets_by_point: dict[int, float] = {}
        for item in monthly_targets:
            point_number = int(item.get("month_number") or 0)
            if point_number < 1 or point_number > max_points:
                continue
            targets_by_point[point_number] = float(item.get("target_value") or 0)

        calendar_months = self._resolve_period_month_numbers(
            start_date=start_date,
            end_date=end_date,
            competence=competence,
        )
        year = parse_year_from_competence(competence)
        if year is None and start_date:
            parsed_start = self._parse_date(start_date)
            if parsed_start is not None:
                year = parsed_start.year

        point_indices = curve_point_indices_for_calendar_months(
            goal_periodicity,
            calendar_months,
            year=year or 2026,
        )

        comparable_goal = sum(
            targets_by_point.get(point_number, 0.0) for point_number in point_indices
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