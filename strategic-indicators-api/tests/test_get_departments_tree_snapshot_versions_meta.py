from __future__ import annotations

from unittest.mock import MagicMock

from si_app.application.use_cases.strategic_indicators.get_departments_tree_snapshot_use_case import (
    GetDepartmentsTreeSnapshotRequest,
    GetDepartmentsTreeSnapshotUseCase,
)


def test_tree_snapshot_meta_includes_measurement_versions() -> None:
    tree_use_case = MagicMock()
    tree_use_case._resolve_scopes.return_value = [
        MagicMock(scope_key="consolidated", scope_label="Consolidado", branch=None),
    ]
    tree_use_case._scope_sort_key.return_value = 0
    tree_use_case._map_departments.return_value = []
    tree_use_case._map_indicators.return_value = []

    current_snapshot = MagicMock()
    current_snapshot.period.competence = "2026-05"
    current_snapshot.measurement_errors = []
    current_snapshot.calculated_departments = []

    snapshot_service = MagicMock()
    snapshot_service.get_current_and_previous_snapshot.return_value = MagicMock(
        current=current_snapshot,
        previous=MagicMock(),
        catalog=MagicMock(),
    )
    snapshot_service.peek_measurement_version_meta.return_value = {
        "serving_version": 2,
        "latest_version": 3,
        "version_count": 3,
        "serving_fallback_from_previous_clean": True,
        "is_clean": False,
    }

    use_case = GetDepartmentsTreeSnapshotUseCase(
        tree_use_case=tree_use_case,
        snapshot_service=snapshot_service,
        alerts_summary_port=MagicMock(get_alerts_summary=MagicMock(return_value=[])),
    )

    result = use_case.execute(
        GetDepartmentsTreeSnapshotRequest(competence="2026-05"),
    )

    assert result["meta"]["measurement_versions"]["serving_version"] == 2
    assert result["meta"]["measurement_versions"]["latest_version"] == 3
