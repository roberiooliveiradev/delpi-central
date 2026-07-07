from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from si_app.application.dto.strategic_indicators.catalog_models import (
    StrategicDepartmentCalculatedValue,
)
from si_app.application.services.strategic_indicators.period_resolution import (
    resolve_period,
)
from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_models import (
    StrategicIndicatorsPeriodSnapshot,
)
from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_service import (
    StrategicIndicatorsSnapshotService,
)


def _department(department_id: str, score: float) -> StrategicDepartmentCalculatedValue:
    return StrategicDepartmentCalculatedValue(
        department_id=department_id,
        department_name=department_id.title(),
        short_name=department_id[:3].upper(),
        weight_pct=10.0,
        strategic_summary="",
        aggregation_mode="consolidated",
        score=score,
        contribution=1.0,
        classification="Alto Desempenho",
        trend="stable",
        indicators=[],
    )


def test_dashboard_department_snapshot_uses_global_cache_when_available() -> None:
    period = resolve_period(competence="2026-07", start_date=None, end_date=None)
    engineering = _department("engineering", 7.4)
    stored = MagicMock(spec=StrategicIndicatorsPeriodSnapshot)
    stored.measurement_errors = []
    stored.calculated_departments = [engineering]

    service = StrategicIndicatorsSnapshotService(
        departments_catalog_repository=MagicMock(),
        resolved_indicators_catalog_repository=MagicMock(),
        measurements_port=MagicMock(),
        calculator=MagicMock(),
        period_scores_repository=MagicMock(),
    )
    service._load_stored_period_snapshot = MagicMock(return_value=stored)  # type: ignore[method-assign]
    service.get_period_snapshot = MagicMock()  # type: ignore[method-assign]

    department, errors = service.get_dashboard_department_snapshot(
        department_id="engineering",
        competence=period.competence,
        start_date=period.start_date,
        end_date=period.end_date,
    )

    assert department is engineering
    assert errors == []
    service.get_period_snapshot.assert_not_called()


def test_dashboard_department_snapshot_computes_scoped_on_cache_miss() -> None:
    period = resolve_period(
        competence="2026-07",
        start_date="01-07-2026",
        end_date="07-07-2026",
    )
    engineering = _department("engineering", 6.5)
    computed = MagicMock(spec=StrategicIndicatorsPeriodSnapshot)
    computed.calculated_departments = [engineering]
    computed.measurement_errors = []

    service = StrategicIndicatorsSnapshotService(
        departments_catalog_repository=MagicMock(),
        resolved_indicators_catalog_repository=MagicMock(),
        measurements_port=MagicMock(),
        calculator=MagicMock(),
        period_scores_repository=MagicMock(),
    )
    service._load_stored_period_snapshot = MagicMock(return_value=None)  # type: ignore[method-assign]
    service.get_period_snapshot = MagicMock(return_value=computed)  # type: ignore[method-assign]

    department, errors = service.get_dashboard_department_snapshot(
        department_id="engineering",
        competence=period.competence,
        start_date=period.start_date,
        end_date=period.end_date,
    )

    assert department is engineering
    assert errors == []
    service.get_period_snapshot.assert_called_once_with(
        competence=period.competence,
        start_date=period.start_date,
        end_date=period.end_date,
        department_id="engineering",
        branch=None,
        force_compute=True,
    )
