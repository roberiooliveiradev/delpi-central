from __future__ import annotations

from unittest.mock import MagicMock, patch

from tm_app.application.services.dashboard_snapshot_read_service import (
    DashboardSnapshotReadService,
)


def test_meta_exposes_cache_freshness():
    repo = MagicMock()
    repo.count.return_value = 42
    repo.latest_calculated_at.return_value = "2026-06-09T12:00:00+00:00"

    with patch.object(DashboardSnapshotReadService, "__init__", lambda self: None):
        svc = DashboardSnapshotReadService()
        svc._repo = repo

        meta = svc.meta()

    assert meta["row_count"] == 42
    assert meta["source"] == "dashboard_calculos"
    assert meta["aggregated_view"] == "processo_competencia_snapshot"


def test_processos_delegates_to_repository():
    repo = MagicMock()
    repo.count.return_value = 1
    repo.latest_calculated_at.return_value = None
    repo.query_processo_competencia_snapshot.return_value = [{"processo_id": "p1"}]

    with patch.object(DashboardSnapshotReadService, "__init__", lambda self: None):
        svc = DashboardSnapshotReadService()
        svc._repo = repo

        data = svc.processos(filial_id="01", limit=10)

    assert data["total"] == 1
    assert data["items"][0]["processo_id"] == "p1"
    repo.query_processo_competencia_snapshot.assert_called_once()
