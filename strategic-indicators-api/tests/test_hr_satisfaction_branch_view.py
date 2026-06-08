from __future__ import annotations

from unittest.mock import MagicMock

from si_app.application.dto.strategic_indicators.catalog_models import (
    StrategicIndicatorCatalogItem,
    StrategicIndicatorMeasuredValue,
)
from si_app.application.dto.hr.hr_snapshot import (
    HrBranchSnapshot,
    HrMetricsSnapshot,
)
from si_app.domain.services.strategic_indicators_calculator import (
    StrategicIndicatorsCalculator,
)
from si_app.infrastructure.providers.strategic_indicators.hr_indicators_snapshot_provider import (
    HrIndicatorsSnapshotProvider,
)


def _branch_snapshot(
    *,
    branch_code: str,
    satisfaction_pct: float | None,
) -> HrBranchSnapshot:
    return HrBranchSnapshot(
        branch_code=branch_code,
        absenteeism_pct=None,
        turnover_pct=None,
        training_hours_per_collaborator=None,
        internal_satisfaction_pct=satisfaction_pct,
    )


def test_hr_satisfaction_provider_maps_unit_values_per_branch() -> None:
    service = MagicMock()
    service.get_snapshot.return_value = HrMetricsSnapshot(
        start_date="01-04-2026",
        end_date="30-04-2026",
        branches=[_branch_snapshot(branch_code="01", satisfaction_pct=74.0)],
        internal_satisfaction_pct=74.0,
    )

    provider = HrIndicatorsSnapshotProvider(hr_metrics_snapshot_service=service)
    branch_01 = provider.get_hr_indicators_snapshot(
        start_date="01-04-2026",
        end_date="30-04-2026",
        branch="01",
    )
    satisfaction = next(
        item for item in branch_01["items"] if item["indicator_id"] == "hr-satisfaction"
    )

    assert satisfaction["value"] == 74.0
    assert satisfaction["unit_values"] == {"01": 74.0}
    assert "consolidated" not in satisfaction["unit_values"]


def test_hr_satisfaction_branch_view_calculates_score_and_gap() -> None:
    calculator = StrategicIndicatorsCalculator()
    indicator = StrategicIndicatorCatalogItem(
        indicator_id="hr-satisfaction",
        department_id="hr",
        indicator_name="Satisfação Interna (Clima/Engajamento)",
        weight_pct=20,
        goal_label="80%",
        goal_value=80.0,
        goal_periodicity="monthly",
        scope_type="consolidated",
        performance_direction="higher_is_better",
        branch_goals={
            "01": {
                "goal_value": 80.0,
                "goal_periodicity": "monthly",
                "goal_mode": "standard",
                "monthly_targets": [],
            },
            "02": {
                "goal_value": 80.0,
                "goal_periodicity": "monthly",
                "goal_mode": "standard",
                "monthly_targets": [],
            },
        },
        resolved_goal_scope_branch="01",
        has_resolved_goal=True,
    )
    measurement = StrategicIndicatorMeasuredValue(
        indicator_id="hr-satisfaction",
        department_id="hr",
        value=73.54,
        source="portal_rh_satisfaction",
        unit_values={"01": 74.0, "02": 73.08},
    )

    branch_01 = calculator.calculate_indicators(
        indicators_catalog=[indicator],
        measurements=[measurement],
        competence="2026-04",
        start_date="01-04-2026",
        end_date="30-04-2026",
        scope_branch="01",
    )

    assert len(branch_01) == 1
    assert branch_01[0].value == 74.0
    assert branch_01[0].score is not None
    assert branch_01[0].gap is not None
    assert branch_01[0].classification != calculator.MISSING_VALUE_CLASSIFICATION


def test_hr_satisfaction_consolidated_unit_values_fail_branch_view() -> None:
    calculator = StrategicIndicatorsCalculator()
    indicator = StrategicIndicatorCatalogItem(
        indicator_id="hr-satisfaction",
        department_id="hr",
        indicator_name="Satisfação Interna (Clima/Engajamento)",
        weight_pct=20,
        goal_label="80%",
        goal_value=80.0,
        goal_periodicity="monthly",
        scope_type="consolidated",
        performance_direction="higher_is_better",
        branch_goals={
            "01": {
                "goal_value": 80.0,
                "goal_periodicity": "monthly",
                "goal_mode": "standard",
                "monthly_targets": [],
            },
            "02": {
                "goal_value": 80.0,
                "goal_periodicity": "monthly",
                "goal_mode": "standard",
                "monthly_targets": [],
            },
        },
        resolved_goal_scope_branch="01",
        has_resolved_goal=True,
    )
    measurement = StrategicIndicatorMeasuredValue(
        indicator_id="hr-satisfaction",
        department_id="hr",
        value=73.54,
        source="portal_rh_satisfaction",
        unit_values={"consolidated": 73.54},
    )

    branch_01 = calculator.calculate_indicators(
        indicators_catalog=[indicator],
        measurements=[measurement],
        competence="2026-04",
        start_date="01-04-2026",
        end_date="30-04-2026",
        scope_branch="01",
    )

    assert len(branch_01) == 1
    assert branch_01[0].classification == calculator.MISSING_VALUE_CLASSIFICATION
