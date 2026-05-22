from __future__ import annotations

from unittest.mock import MagicMock, patch

from tm_app.application.services.dashboard_recalc_service import DashboardRecalcService


def test_recalculate_full_truncates():
    repo = MagicMock()
    repo.replace_all.return_value = 3
    data_repo = MagicMock()
    data_repo.load_raw.return_value = MagicMock()
    calc = MagicMock()
    calc.build_dashboard_rows.return_value = [{"dashboard_calculo_id": "a"}]

    with patch.object(DashboardRecalcService, "__init__", lambda self: None):
        svc = DashboardRecalcService()
        svc._dashboard_repo = repo
        svc._data_repo = data_repo
        svc._calculator = calc

        result = svc.recalculate()

    assert result["mode"] == "full"
    assert result["rows_upserted"] == 3
    repo.replace_all.assert_called_once()
    repo.delete_by_processo.assert_not_called()


def test_recalculate_incremental_by_processo():
    repo = MagicMock()
    repo.delete_by_processo.return_value = 2
    repo.upsert_rows.return_value = 2
    data_repo = MagicMock()
    calc = MagicMock()
    calc.build_dashboard_rows.return_value = [
        {"dashboard_calculo_id": "p1::2025-01", "processo_id": "p1", "revisao_id": "r1", "competencia": "2025-01"},
        {"dashboard_calculo_id": "p2::2025-01", "processo_id": "p2", "revisao_id": "r2", "competencia": "2025-01"},
    ]

    with patch.object(DashboardRecalcService, "__init__", lambda self: None):
        svc = DashboardRecalcService()
        svc._dashboard_repo = repo
        svc._data_repo = data_repo
        svc._calculator = calc

        result = svc.recalculate(processo_id="p1")

    assert result["mode"] == "incremental"
    assert result["rows_deleted"] == 2
    assert result["rows_upserted"] == 2
    repo.delete_by_processo.assert_called_once_with("p1")
    upserted = repo.upsert_rows.call_args[0][0]
    assert len(upserted) == 1
    assert upserted[0]["processo_id"] == "p1"
