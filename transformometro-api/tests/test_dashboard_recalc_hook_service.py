from __future__ import annotations

from unittest.mock import MagicMock, patch

from tm_app.application.services.dashboard_recalc_hook_service import DashboardRecalcHookService


def test_after_processo_triggers_incremental_recalc():
    recalc = MagicMock()
    recalc.recalculate.return_value = {"mode": "incremental"}

    with (
        patch.object(DashboardRecalcHookService, "__init__", lambda self: None),
        patch(
            "tm_app.application.services.dashboard_recalc_hook_service.settings"
        ) as mock_settings,
    ):
        mock_settings.TM_DASHBOARD_AUTO_RECALC = True
        svc = DashboardRecalcHookService()
        svc._recalc = recalc

        result = svc.after_processo("proc-1")

    assert result == {"mode": "incremental"}
    recalc.recalculate.assert_called_once_with(processo_id="proc-1")


def test_after_revisao_with_processo_id_prefers_processo_scope():
    recalc = MagicMock()
    recalc.recalculate.return_value = {"mode": "incremental"}

    with (
        patch.object(DashboardRecalcHookService, "__init__", lambda self: None),
        patch(
            "tm_app.application.services.dashboard_recalc_hook_service.settings"
        ) as mock_settings,
    ):
        mock_settings.TM_DASHBOARD_AUTO_RECALC = True
        svc = DashboardRecalcHookService()
        svc._recalc = recalc

        svc.after_revisao("rev-1", processo_id="proc-1")

    recalc.recalculate.assert_called_once_with(processo_id="proc-1")


def test_after_global_resource_change_runs_full_recalc():
    recalc = MagicMock()
    recalc.recalculate.return_value = {"mode": "full"}

    with (
        patch.object(DashboardRecalcHookService, "__init__", lambda self: None),
        patch(
            "tm_app.application.services.dashboard_recalc_hook_service.settings"
        ) as mock_settings,
    ):
        mock_settings.TM_DASHBOARD_AUTO_RECALC = True
        svc = DashboardRecalcHookService()
        svc._recalc = recalc

        svc.after_global_resource_change()

    recalc.recalculate.assert_called_once_with()


def test_hook_disabled_skips_recalc():
    recalc = MagicMock()

    with (
        patch.object(DashboardRecalcHookService, "__init__", lambda self: None),
        patch(
            "tm_app.application.services.dashboard_recalc_hook_service.settings"
        ) as mock_settings,
    ):
        mock_settings.TM_DASHBOARD_AUTO_RECALC = False
        svc = DashboardRecalcHookService()
        svc._recalc = recalc

        assert svc.after_processo("proc-1") is None

    recalc.recalculate.assert_not_called()
