from __future__ import annotations

from unittest.mock import MagicMock, patch

from tm_app.application.services.dashboard_recalc_hook_service import DashboardRecalcHookService


def _make_service(recalc: MagicMock) -> DashboardRecalcHookService:
    with patch.object(DashboardRecalcHookService, "__init__", lambda self: None):
        svc = DashboardRecalcHookService()
        svc._recalc = recalc
    return svc


def test_after_processo_invalidates_cache_and_skips_persist_by_default():
    recalc = MagicMock()
    with (
        patch("tm_app.application.services.dashboard_recalc_hook_service.settings") as mock_settings,
        patch(
            "tm_app.application.services.dashboard_recalc_hook_service.dashboard_query_cache"
        ) as mock_cache,
    ):
        mock_settings.TM_DASHBOARD_AUTO_RECALC = True
        mock_settings.TM_DASHBOARD_PERSIST_CACHE = False
        mock_cache.invalidate.return_value = 3

        svc = _make_service(recalc)
        result = svc.after_processo("proc-1")

    mock_cache.invalidate.assert_called_once()
    recalc.recalculate.assert_not_called()
    assert result["cache_invalidated"] is True
    assert result["persisted"] is False
    assert result["cache_entries_cleared"] == 3


def test_after_processo_persists_when_enabled():
    recalc = MagicMock()
    recalc.recalculate.return_value = {"mode": "incremental", "rows_upserted": 5}
    with (
        patch("tm_app.application.services.dashboard_recalc_hook_service.settings") as mock_settings,
        patch(
            "tm_app.application.services.dashboard_recalc_hook_service.dashboard_query_cache"
        ) as mock_cache,
    ):
        mock_settings.TM_DASHBOARD_AUTO_RECALC = True
        mock_settings.TM_DASHBOARD_PERSIST_CACHE = True
        mock_cache.invalidate.return_value = 0

        svc = _make_service(recalc)
        result = svc.after_processo("proc-1")

    mock_cache.invalidate.assert_called_once()
    recalc.recalculate.assert_called_once_with(processo_id="proc-1")
    assert result["persisted"] is True
    assert result["rows_upserted"] == 5


def test_after_revisao_with_processo_id_prefers_processo_scope():
    recalc = MagicMock()
    recalc.recalculate.return_value = {"mode": "incremental"}
    with (
        patch("tm_app.application.services.dashboard_recalc_hook_service.settings") as mock_settings,
        patch(
            "tm_app.application.services.dashboard_recalc_hook_service.dashboard_query_cache"
        ) as mock_cache,
    ):
        mock_settings.TM_DASHBOARD_AUTO_RECALC = True
        mock_settings.TM_DASHBOARD_PERSIST_CACHE = True
        mock_cache.invalidate.return_value = 0

        svc = _make_service(recalc)
        svc.after_revisao("rev-1", processo_id="proc-1")

    recalc.recalculate.assert_called_once_with(processo_id="proc-1")


def test_after_global_resource_change_runs_full_recalc_when_enabled():
    recalc = MagicMock()
    recalc.recalculate.return_value = {"mode": "full"}
    with (
        patch("tm_app.application.services.dashboard_recalc_hook_service.settings") as mock_settings,
        patch(
            "tm_app.application.services.dashboard_recalc_hook_service.dashboard_query_cache"
        ) as mock_cache,
    ):
        mock_settings.TM_DASHBOARD_AUTO_RECALC = True
        mock_settings.TM_DASHBOARD_PERSIST_CACHE = True
        mock_cache.invalidate.return_value = 0

        svc = _make_service(recalc)
        svc.after_global_resource_change()

    recalc.recalculate.assert_called_once_with()


def test_invalidate_runs_even_when_auto_recalc_disabled():
    recalc = MagicMock()
    with (
        patch("tm_app.application.services.dashboard_recalc_hook_service.settings") as mock_settings,
        patch(
            "tm_app.application.services.dashboard_recalc_hook_service.dashboard_query_cache"
        ) as mock_cache,
    ):
        mock_settings.TM_DASHBOARD_AUTO_RECALC = False
        mock_settings.TM_DASHBOARD_PERSIST_CACHE = True
        mock_cache.invalidate.return_value = 1

        svc = _make_service(recalc)
        result = svc.after_processo("proc-1")

    # Cache sempre invalidado; persistência só quando AUTO_RECALC E PERSIST_CACHE.
    mock_cache.invalidate.assert_called_once()
    recalc.recalculate.assert_not_called()
    assert result["persisted"] is False
