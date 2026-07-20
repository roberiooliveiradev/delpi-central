from __future__ import annotations

from typing import Literal

from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_service import (
    StrategicIndicatorsSnapshotService,
)
from si_app.domain.services.strategic_indicators_calculator import (
    StrategicIndicatorsCalculator,
)

MetricKind = Literal["realized", "meta"]


class GetDashboardIndicatorMetricUseCase:
    """Meta ou realizado de um indicador SI (integração dashboards / TV)."""

    def __init__(
        self,
        *,
        snapshot_service: StrategicIndicatorsSnapshotService,
        calculator: StrategicIndicatorsCalculator,
    ) -> None:
        self._snapshot_service = snapshot_service
        self._calculator = calculator

    def execute(
        self,
        *,
        indicator_id: str,
        kind: MetricKind,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
    ) -> dict | None:
        normalized_id = (indicator_id or "").strip()
        if not normalized_id:
            return None

        snapshot = self._snapshot_service.get_current_and_previous_snapshot(
            competence=competence,
            start_date=start_date,
            end_date=end_date,
            department_id=None,
            branch=branch,
        )
        catalog_by_id = {
            item.indicator_id: item
            for item in snapshot.catalog.indicators_catalog
        }
        catalog_item = catalog_by_id.get(normalized_id)
        period = snapshot.current.period

        calculated = None
        for department in snapshot.current.calculated_departments:
            for indicator in department.indicators:
                if indicator.indicator_id == normalized_id:
                    calculated = indicator
                    break
            if calculated is not None:
                break

        if calculated is None and catalog_item is None:
            return None

        source_key = None
        if catalog_item is not None:
            source_key = getattr(catalog_item, "source_key", None)
        if not source_key and calculated is not None:
            source_key = getattr(calculated, "source", None)

        name = (
            calculated.indicator_name
            if calculated is not None
            else getattr(catalog_item, "indicator_name", normalized_id)
        )
        department_id = (
            calculated.department_id
            if calculated is not None
            else getattr(catalog_item, "department_id", None)
        )
        formatting_source = calculated if calculated is not None else catalog_item

        base = {
            "indicator_id": normalized_id,
            "source_key": source_key,
            "name": name,
            "department_id": department_id,
            "value_unit": getattr(formatting_source, "value_unit", None),
            "value_prefix": getattr(formatting_source, "value_prefix", None),
            "value_suffix": getattr(formatting_source, "value_suffix", None),
            "value_decimals": int(
                getattr(formatting_source, "value_decimals", 2) or 2
            ),
            "partial_success": len(snapshot.current.measurement_errors) > 0,
        }

        if kind == "realized":
            value = calculated.value if calculated is not None else None
            realized = (
                self._calculator.build_realized_payload(
                    unit_values=calculated.unit_values,
                    value=calculated.value,
                    department_id=calculated.department_id,
                )
                if calculated is not None
                else {}
            )
            return {
                **base,
                "value": value,
                "has_value": self._calculator.indicator_has_value(value),
                "realized": realized,
                "score": calculated.score if calculated is not None else None,
            }

        goal_value = (
            calculated.goal_value
            if calculated is not None
            else getattr(catalog_item, "goal_value", None)
        )
        goal_label = (
            calculated.goal_label
            if calculated is not None
            else getattr(catalog_item, "goal_label", None)
        )
        goals: dict = {}
        comparable_goal = None
        if calculated is not None:
            goals = self._calculator.resolve_goals_payload_for_calculated(
                calculated=calculated,
                catalog_item=catalog_item,
                start_date=period.start_date,
                end_date=period.end_date,
                competence=period.competence,
            )
            if calculated.goal_value is not None:
                comparable_goal = self._calculator.calculate_comparable_goal(
                    goal_value=float(calculated.goal_value),
                    goal_periodicity=calculated.goal_periodicity or "monthly",
                    goal_mode=getattr(calculated, "goal_mode", "standard") or "standard",
                    monthly_targets=getattr(calculated, "monthly_targets", None),
                    start_date=period.start_date,
                    end_date=period.end_date,
                    competence=period.competence,
                )

        if comparable_goal is None and goals:
            for key in ("consolidated", "01", "02"):
                if goals.get(key) is not None:
                    comparable_goal = goals[key]
                    break
            if comparable_goal is None:
                comparable_goal = next(
                    (v for v in goals.values() if v is not None),
                    None,
                )

        return {
            **base,
            "value": comparable_goal,
            "comparable_goal": comparable_goal,
            "goal_value": goal_value,
            "goal_label": goal_label,
            "goals": goals,
            "has_value": comparable_goal is not None,
        }
