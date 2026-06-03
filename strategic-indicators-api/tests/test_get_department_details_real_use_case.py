from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_models import (
    StrategicIndicatorsCatalogSnapshot,
    StrategicIndicatorsComparativeSnapshot,
    StrategicIndicatorsPeriodSnapshot,
)
from si_app.application.use_cases.strategic_indicators.get_department_details_real_use_case import (
    GetStrategicIndicatorsDepartmentDetailsRealRequest,
    GetStrategicIndicatorsDepartmentDetailsRealUseCase,
)
from si_app.domain.services.strategic_indicators_calculator import (
    StrategicIndicatorsCalculator,
)


def _indicator(*, indicator_id: str, unit_values: dict):
    return SimpleNamespace(
        indicator_id=indicator_id,
        indicator_name="CPV",
        department_id="supplies",
        weight_pct=30,
        goal_label="meta",
        goal_value=47.0,
        goal_periodicity="monthly",
        goal_mode="standard",
        monthly_targets=[],
        strategic_description="desc",
        scope_type="per_unit",
        performance_direction="lower_is_better",
        unit_values=unit_values,
        value=49.0,
        classification="Excelência Integrada",
        score=9.98,
        gap=-1.0,
        unit_gaps={"01": 0.1, "02": -3.0},
    )


def test_department_details_reads_global_snapshot_same_as_tree() -> None:
    snapshot_service = MagicMock()
    calculator = StrategicIndicatorsCalculator()

    cpv = _indicator(indicator_id="supplies-cpv", unit_values={"01": 47.13, "02": 50.86})
    supplies_dept = SimpleNamespace(
        department_id="supplies",
        department_name="Suprimentos",
        short_name="SUP",
        weight_pct=12,
        score=9.6,
        classification="Excelência Integrada",
        contribution=1.15,
        aggregation_mode="weighted",
        strategic_summary="Compras",
        indicators=[cpv],
    )

    period = SimpleNamespace(
        competence="2026-05",
        start_date="01-05-2026",
        end_date="31-05-2026",
    )
    current = MagicMock(spec=StrategicIndicatorsPeriodSnapshot)
    current.period = period
    current.calculated_departments = [supplies_dept]
    current.measurement_errors = []
    current.calculated_indicators = [cpv]

    previous = MagicMock(spec=StrategicIndicatorsPeriodSnapshot)
    previous.calculated_departments = []

    catalog = MagicMock(spec=StrategicIndicatorsCatalogSnapshot)
    catalog.indicators_catalog = []

    snapshot_service.get_current_and_previous_snapshot.return_value = (
        StrategicIndicatorsComparativeSnapshot(
            catalog=catalog,
            current=current,
            previous=previous,
        )
    )

    result = GetStrategicIndicatorsDepartmentDetailsRealUseCase(
        snapshot_service=snapshot_service,
        calculator=calculator,
    ).execute(
        GetStrategicIndicatorsDepartmentDetailsRealRequest(
            department_id="supplies",
            competence="2026-05",
        )
    )

    snapshot_service.get_current_and_previous_snapshot.assert_called_once_with(
        competence="2026-05",
        start_date=None,
        end_date=None,
        department_id=None,
        branch=None,
    )

    cpv_item = next(i for i in result["indicators"] if i["id"] == "supplies-cpv")
    assert cpv_item["realized"]["02"] == 50.86
