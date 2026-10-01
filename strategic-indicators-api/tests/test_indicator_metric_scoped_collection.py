"""PERF-003 — coleta escopada para métrica escalar de indicador.

Prova, com contagem de chamadas, que uma requisição escalar
(`GetDashboardIndicatorMetricUseCase`) executa apenas o collector do
departamento dono do indicador — em vez do fan-out global (7 departamentos ×
período atual + anterior) — preservando o resultado calculado e o caminho
materializado global quando disponível.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from si_app.application.dto.strategic_indicators.catalog_models import (
    StrategicDepartmentCatalogItem,
    StrategicIndicatorCatalogItem,
)
from si_app.application.services.strategic_indicators.snapshot_shared_cache import (
    clear_in_process_snapshot_cache,
)
from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_service import (
    StrategicIndicatorsSnapshotService,
)
from si_app.application.use_cases.strategic_indicators.get_dashboard_indicator_metric_use_case import (
    GetDashboardIndicatorMetricUseCase,
)
from si_app.domain.services.strategic_indicators_calculator import (
    StrategicIndicatorsCalculator,
)
from si_app.infrastructure.providers.strategic_indicators.real_indicator_measurements_provider import (
    RealStrategicIndicatorsMeasurementsProvider,
)

DEPARTMENTS = (
    "engineering",
    "production",
    "commercial",
    "quality",
    "hr",
    "financial",
    "supplies",
)


def _department_catalog_item(department_id: str) -> StrategicDepartmentCatalogItem:
    return StrategicDepartmentCatalogItem(
        department_id=department_id,
        department_name=department_id.title(),
        short_name=department_id.title(),
        weight_pct=10.0,
        strategic_summary="",
        aggregation_mode="consolidated",
    )


def _indicator_catalog_item(
    indicator_id: str,
    department_id: str,
) -> StrategicIndicatorCatalogItem:
    return StrategicIndicatorCatalogItem(
        indicator_id=indicator_id,
        department_id=department_id,
        indicator_name=indicator_id,
        weight_pct=10.0,
        goal_label="Meta",
        goal_value=100.0,
        goal_periodicity="monthly",
        goal_mode="standard",
        value_unit="count",
    )


def _build_environment() -> tuple[
    GetDashboardIndicatorMetricUseCase,
    StrategicIndicatorsSnapshotService,
    dict[str, MagicMock],
]:
    """Serviço real + provider real + ports departamentais mockados.

    Cada port retorna medições apenas dos indicadores do próprio departamento,
    espelhando o invariante de produção (measurement.department_id == collector).
    """
    indicator_ids = {
        department: f"{department}-indicator" for department in DEPARTMENTS
    }
    ports: dict[str, MagicMock] = {}
    for department in DEPARTMENTS:
        port = MagicMock()
        getattr(
            port, f"get_{department}_indicators_snapshot"
        ).return_value = {
            "items": [
                {
                    "indicator_id": indicator_ids[department],
                    "department_id": department,
                    "value": 90.0,
                    "source": f"{department}_snapshot",
                    "unit_values": {"consolidated": 90.0},
                }
            ],
            "errors": [],
        }
        ports[department] = port

    measurements_provider = RealStrategicIndicatorsMeasurementsProvider(
        engineering_snapshot_port=ports["engineering"],
        production_snapshot_port=ports["production"],
        commercial_snapshot_port=ports["commercial"],
        quality_snapshot_port=ports["quality"],
        hr_snapshot_port=ports["hr"],
        financial_snapshot_port=ports["financial"],
        supplies_snapshot_port=ports["supplies"],
    )

    departments_repository = MagicMock()
    departments_repository.list_departments_catalog.return_value = [
        _department_catalog_item(department) for department in DEPARTMENTS
    ]
    departments_repository.get_department_goal_summary.return_value = {}

    all_indicators = [
        _indicator_catalog_item(indicator_ids[department], department)
        for department in DEPARTMENTS
    ]
    catalog_repository = MagicMock()

    def _list_indicators(**kwargs):
        department_id = kwargs.get("department_id")
        if department_id:
            return [
                item
                for item in all_indicators
                if item.department_id == department_id
            ]
        return list(all_indicators)

    catalog_repository.list_resolved_indicators_catalog.side_effect = (
        _list_indicators
    )

    snapshot_service = StrategicIndicatorsSnapshotService(
        departments_catalog_repository=departments_repository,
        resolved_indicators_catalog_repository=catalog_repository,
        measurements_port=measurements_provider,
        calculator=StrategicIndicatorsCalculator(),
        period_scores_repository=None,
        calculation_snapshots_repository=None,
    )

    use_case = GetDashboardIndicatorMetricUseCase(
        snapshot_service=snapshot_service,
        calculator=StrategicIndicatorsCalculator(),
    )
    return use_case, snapshot_service, ports


def _collector_calls(ports: dict[str, MagicMock]) -> dict[str, int]:
    return {
        department: getattr(
            port, f"get_{department}_indicators_snapshot"
        ).call_count
        for department, port in ports.items()
    }


@pytest.fixture(autouse=True)
def _clean_caches():
    clear_in_process_snapshot_cache()
    yield
    clear_in_process_snapshot_cache()


def test_scalar_metric_collects_only_indicator_department() -> None:
    use_case, _service, ports = _build_environment()

    result = use_case.execute(
        indicator_id="quality-indicator",
        kind="realized",
        competence="2026-04",
    )

    assert result is not None
    assert result["indicator_id"] == "quality-indicator"
    assert result["department_id"] == "quality"
    assert result["value"] == 90.0
    assert result["has_value"] is True

    calls = _collector_calls(ports)
    assert calls == {
        "engineering": 0,
        "production": 0,
        "commercial": 0,
        "quality": 1,
        "hr": 0,
        "financial": 0,
        "supplies": 0,
    }


def test_scalar_metric_matches_global_computation() -> None:
    """O valor calculado no caminho escopado é idêntico ao da base global."""
    use_case, service, _ports = _build_environment()

    result = use_case.execute(
        indicator_id="quality-indicator",
        kind="realized",
        competence="2026-04",
    )

    clear_in_process_snapshot_cache()
    comparative = service.get_current_and_previous_snapshot(
        competence="2026-04",
        department_id=None,
    )
    global_calculated = next(
        indicator
        for department in comparative.current.calculated_departments
        for indicator in department.indicators
        if indicator.indicator_id == "quality-indicator"
    )

    assert result is not None
    assert result["value"] == global_calculated.value
    assert result["score"] == global_calculated.score
    assert result["realized"] == dict(global_calculated.unit_values)


def test_scalar_metric_preserves_branch_scoped_collection() -> None:
    use_case, _service, ports = _build_environment()

    result = use_case.execute(
        indicator_id="quality-indicator",
        kind="realized",
        competence="2026-04",
        branch="01",
    )

    assert result is not None
    quality_fetch = ports["quality"].get_quality_indicators_snapshot
    assert quality_fetch.call_count == 1
    assert quality_fetch.call_args.kwargs["branch"] == "01"
    for department, port in ports.items():
        if department == "quality":
            continue
        fetch = getattr(port, f"get_{department}_indicators_snapshot")
        assert fetch.call_count == 0


def test_unknown_indicator_keeps_404_semantics_without_invented_scope() -> None:
    use_case, _service, ports = _build_environment()

    result = use_case.execute(
        indicator_id="unknown-indicator",
        kind="realized",
        competence="2026-04",
    )

    assert result is None


def test_stored_global_snapshot_serves_scalar_without_collectors() -> None:
    """Com `period_scores` global fresco, nenhum collector deve executar."""
    use_case, service, ports = _build_environment()

    stored = SimpleNamespace(
        period=SimpleNamespace(
            competence="2026-04",
            start_date="01-04-2026",
            end_date="30-04-2026",
        ),
        measurement_errors=[],
        calculated_departments=[],
        calculated_indicators=[],
        measurements=[],
        igd=None,
        igd_exact=None,
        classification="",
    )
    service._load_stored_period_snapshot = MagicMock(return_value=stored)  # noqa: SLF001

    result = use_case.execute(
        indicator_id="quality-indicator",
        kind="realized",
        competence="2026-04",
    )

    assert result is not None
    assert result["value"] is None
    assert _collector_calls(ports) == {department: 0 for department in DEPARTMENTS}
