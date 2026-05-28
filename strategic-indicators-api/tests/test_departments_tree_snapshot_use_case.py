from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_models import (
    StrategicIndicatorsCatalogSnapshot,
    StrategicIndicatorsComparativeSnapshot,
    StrategicIndicatorsPeriodSnapshot,
)
from si_app.application.use_cases.strategic_indicators.get_departments_tree_snapshot_use_case import (
    GetDepartmentsTreeSnapshotRequest,
    GetDepartmentsTreeSnapshotUseCase,
)
from si_app.application.use_cases.strategic_indicators.get_departments_tree_use_case import (
    _TreeScopeConfig,
)


def test_snapshot_uses_comparative_snapshot_not_period_series() -> None:
    snapshot_service = MagicMock()
    tree_use_case = MagicMock()

    period = SimpleNamespace(competence="2026-05")
    current = MagicMock(spec=StrategicIndicatorsPeriodSnapshot)
    current.period = period
    current.igd = 5.0
    current.igd_exact = 5.0
    current.classification = "Crítico"
    current.calculated_departments = []
    current.measurement_errors = []

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

    tree_use_case._resolve_scopes.return_value = [
        _TreeScopeConfig(
            scope_key="consolidated",
            scope_label="Consolidado",
            branch=None,
        )
    ]
    tree_use_case._scope_sort_key.return_value = 0
    tree_use_case._map_departments.return_value = {"items": []}
    tree_use_case._map_indicators.return_value = {"items": []}

    result = GetDepartmentsTreeSnapshotUseCase(
        tree_use_case=tree_use_case,
        snapshot_service=snapshot_service,
    ).execute(
        GetDepartmentsTreeSnapshotRequest(
            view_mode="consolidated",
            competence="2026-05",
        )
    )

    snapshot_service.get_current_and_previous_snapshot.assert_called_once()
    assert not hasattr(snapshot_service, "load_period_snapshots") or (
        not snapshot_service.load_period_snapshots.called
    )
    assert result["competence"] == "2026-05"
    assert result["igd"] == 5.0
    tree_use_case._map_indicators.assert_called_once()
    _args, kwargs = tree_use_case._map_indicators.call_args
    assert kwargs.get("catalog") is catalog
