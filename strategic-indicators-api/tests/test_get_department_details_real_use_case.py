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


def test_department_details_units_use_per_branch_comparable_goal() -> None:
    """Cada unidade usa a meta comparable da própria filial — não a meta primária."""
    from si_app.application.dto.strategic_indicators.catalog_models import (
        StrategicIndicatorCatalogItem,
    )

    snapshot_service = MagicMock()
    calculator = StrategicIndicatorsCalculator()

    # Realizado igual nas duas filiais; metas distintas → scores distintos.
    rol = SimpleNamespace(
        indicator_id="commercial-rol",
        indicator_name="ROL",
        department_id="commercial",
        weight_pct=40,
        goal_label="meta",
        goal_value=100_000.0,  # cadastro "primário" (01) — não deve valer para 02
        goal_periodicity="monthly",
        goal_mode="standard",
        monthly_targets=[],
        strategic_description="",
        scope_type="per_unit",
        performance_direction="higher_is_better",
        unit_values={"01": 80_000.0, "02": 80_000.0},
        unit_goals={"01": 100_000.0, "02": 200_000.0},
        value=80_000.0,
        classification="Alto Desempenho",
        score=7.0,
        gap=-20_000.0,
        unit_gaps={"01": -20_000.0, "02": -120_000.0},
        value_unit="currency",
    )
    catalog_item = StrategicIndicatorCatalogItem(
        indicator_id="commercial-rol",
        department_id="commercial",
        indicator_name="ROL",
        weight_pct=40.0,
        goal_label="meta",
        goal_value=100_000.0,
        goal_periodicity="monthly",
        goal_mode="standard",
        scope_type="per_unit",
        value_unit="currency",
        branch_value_aggregation="sum",
        branch_goals={
            "01": {
                "goal_value": 100_000.0,
                "goal_periodicity": "monthly",
                "goal_mode": "standard",
                "monthly_targets": [],
            },
            "02": {
                "goal_value": 200_000.0,
                "goal_periodicity": "monthly",
                "goal_mode": "standard",
                "monthly_targets": [],
            },
        },
    )
    dept = SimpleNamespace(
        department_id="commercial",
        department_name="Comercial",
        short_name="COM",
        weight_pct=20,
        score=7.0,
        classification="Alto Desempenho",
        contribution=1.4,
        aggregation_mode="average_of_units",
        strategic_summary="",
        indicators=[rol],
    )
    period = SimpleNamespace(
        competence="2026-04",
        start_date="01-04-2026",
        end_date="30-04-2026",
    )
    current = MagicMock(spec=StrategicIndicatorsPeriodSnapshot)
    current.period = period
    current.calculated_departments = [dept]
    current.measurement_errors = []
    current.calculated_indicators = [rol]
    previous = MagicMock(spec=StrategicIndicatorsPeriodSnapshot)
    previous.calculated_departments = []
    catalog = MagicMock(spec=StrategicIndicatorsCatalogSnapshot)
    catalog.indicators_catalog = [catalog_item]
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
            department_id="commercial",
            competence="2026-04",
        )
    )

    units = {u["unit_id"]: u for u in result["units"]}
    assert units["01"]["score"] != units["02"]["score"]
    # Com realizado 80k: meta 100k → score maior que meta 200k
    assert units["01"]["score"] > units["02"]["score"]

