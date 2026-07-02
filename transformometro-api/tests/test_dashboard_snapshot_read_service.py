from __future__ import annotations

from unittest.mock import MagicMock, patch

from tm_app.application.services.dashboard_snapshot_read_service import (
    DashboardSnapshotReadService,
)
from tm_app.application.services.dashboard_view_scope_service import (
    DashboardScopeFilters,
    DashboardView,
)

_SETTINGS = "tm_app.application.services.dashboard_snapshot_read_service.settings"


def _make_service(*, repo=None, live=None):
    with patch.object(DashboardSnapshotReadService, "__init__", lambda self: None):
        svc = DashboardSnapshotReadService()
        svc._repo = repo or MagicMock()
        svc._live = live or MagicMock()
        scope_svc = MagicMock()
        scope_svc.resolve.return_value = DashboardScopeFilters(
            view=DashboardView.FILIAL,
            filial_id="01",
            setor_id=None,
        )
        scope_svc.scope_meta.return_value = {
            "view": "filial",
            "filial_id": "01",
            "setor_id": None,
        }
        svc._scope = scope_svc
    return svc


def test_meta_live_mode_by_default():
    repo = MagicMock()
    with patch(_SETTINGS) as mock_settings:
        mock_settings.TM_DASHBOARD_PERSIST_CACHE = False
        svc = _make_service(repo=repo)
        meta = svc.meta()

    assert meta["mode"] == "live"
    assert meta["source"] == "cadastro_tempo_real"
    repo.count.assert_not_called()


def test_meta_persisted_mode_when_enabled_and_populated():
    repo = MagicMock()
    repo.count.return_value = 42
    repo.latest_calculated_at.return_value = "2026-06-09T12:00:00+00:00"
    with patch(_SETTINGS) as mock_settings:
        mock_settings.TM_DASHBOARD_PERSIST_CACHE = True
        svc = _make_service(repo=repo)
        meta = svc.meta()

    assert meta["mode"] == "persisted"
    assert meta["source"] == "dashboard_calculos"
    assert meta["row_count"] == 42


def test_processos_uses_live_engine_by_default():
    live = MagicMock()
    live.processo_competencia_rows.return_value = [{"processo_id": "p1"}]
    with patch(_SETTINGS) as mock_settings:
        mock_settings.TM_DASHBOARD_PERSIST_CACHE = False
        svc = _make_service(live=live)
        data = svc.processos(filial_id="01", limit=10)

    assert data["total"] == 1
    assert data["items"][0]["processo_id"] == "p1"
    live.processo_competencia_rows.assert_called_once()


def test_processos_uses_persisted_fast_path_when_enabled():
    repo = MagicMock()
    repo.count.return_value = 5
    repo.query_processo_competencia_snapshot.return_value = [{"processo_id": "p9"}]
    with patch(_SETTINGS) as mock_settings:
        mock_settings.TM_DASHBOARD_PERSIST_CACHE = True
        svc = _make_service(repo=repo)
        data = svc.processos(filial_id="01", limit=10)

    assert data["total"] == 1
    assert data["items"][0]["processo_id"] == "p9"
    repo.query_processo_competencia_snapshot.assert_called_once()


def test_resumo_maps_live_summary_keys():
    live = MagicMock()
    live.build_summary.return_value = {
        "solucoes_implementadas": 2,
        "economia_bruta_total": 1000.0,
        "economia_liquida_total": 800.0,
        "investimento_unico_total": 300.0,
        "custo_recorrente_total": 100.0,
        "custo_recursos_compartilhados_total": 0.0,
        "investimento_total": 400.0,
        "horas_economizadas_total": 12.0,
        "evolucao_mensal": [],
        "roi_medio": 2.0,
    }
    with patch(_SETTINGS) as mock_settings:
        mock_settings.TM_DASHBOARD_PERSIST_CACHE = False
        svc = _make_service(live=live)
        data = svc.resumo(filial_id="01")

    summary = data["summary"]
    assert summary["economia_liquida_total"] == 800.0
    assert summary["investimento_total"] == 400.0
    # Não vaza chaves fora do contrato do resumo.
    assert "evolucao_mensal" not in summary
    assert "roi_medio" not in summary
