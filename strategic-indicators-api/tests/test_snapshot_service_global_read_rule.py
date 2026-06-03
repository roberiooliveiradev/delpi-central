from __future__ import annotations

from types import SimpleNamespace

from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_models import (
    StrategicIndicatorsCatalogSnapshot,
    StrategicIndicatorsComparativeSnapshot,
    StrategicIndicatorsPeriodSnapshot,
)
from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_service import (
    StrategicIndicatorsSnapshotService,
)


def _period(*, departments: list[str]) -> StrategicIndicatorsPeriodSnapshot:
    period = SimpleNamespace(competence="2026-05")
    return StrategicIndicatorsPeriodSnapshot(
        period=period,
        measurements=[SimpleNamespace(name="m")],
        measurement_errors=[
            {"department_id": "supplies", "source": "s", "message": "x"},
            {"department_id": "hr", "source": "s", "message": "y"},
            {"department_id": "", "source": "global", "message": "z"},
        ],
        calculated_indicators=[
            SimpleNamespace(indicator_id=f"{dep}-i", department_id=dep)
            for dep in departments
        ],
        calculated_departments=[
            SimpleNamespace(department_id=dep, department_name=dep.upper())
            for dep in departments
        ],
        igd=82.5,
        igd_exact=82.531,
        classification="Excelência Integrada",
    )


def test_filter_comparative_keeps_only_requested_department() -> None:
    comparative = StrategicIndicatorsComparativeSnapshot(
        catalog=StrategicIndicatorsCatalogSnapshot(
            departments_catalog=[],
            indicators_catalog=[],
            goals_by_department={},
        ),
        current=_period(departments=["supplies", "hr", "commercial"]),
        previous=_period(departments=["supplies", "hr"]),
    )

    filtered = StrategicIndicatorsSnapshotService._filter_comparative_to_department(
        comparative, "supplies"
    )

    assert [d.department_id for d in filtered.current.calculated_departments] == [
        "supplies"
    ]
    assert [i.department_id for i in filtered.current.calculated_indicators] == [
        "supplies"
    ]
    # IGD permanece global (da empresa), não recalculado para o departamento.
    assert filtered.current.igd == 82.5
    # Erros: mantém o do departamento + globais (department_id vazio).
    assert {e["department_id"] for e in filtered.current.measurement_errors} == {
        "supplies",
        "",
    }
    # Previous também filtrado.
    assert [d.department_id for d in filtered.previous.calculated_departments] == [
        "supplies"
    ]


def test_filter_comparative_handles_missing_previous() -> None:
    comparative = StrategicIndicatorsComparativeSnapshot(
        catalog=StrategicIndicatorsCatalogSnapshot(
            departments_catalog=[],
            indicators_catalog=[],
            goals_by_department={},
        ),
        current=_period(departments=["supplies", "hr"]),
        previous=None,
    )

    filtered = StrategicIndicatorsSnapshotService._filter_comparative_to_department(
        comparative, "hr"
    )

    assert filtered.previous is None
    assert [d.department_id for d in filtered.current.calculated_departments] == ["hr"]
