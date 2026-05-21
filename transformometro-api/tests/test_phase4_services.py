import json
from pathlib import Path
from unittest.mock import patch

from tm_app.application.services.dashboard_alerts_service import DashboardAlertsService
from tm_app.application.services.process_revision_compare_service import (
    ProcessRevisionCompareService,
)
from tm_app.application.services.revisao_rateio_diagnostic_service import (
    RevisaoRateioDiagnosticService,
)
from tm_app.domain.raw_data import TransformometroRawData

FIXTURES = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> TransformometroRawData:
    payload = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return TransformometroRawData(**payload)


@patch("tm_app.application.services.dashboard_alerts_service.DashboardCalculoRepository")
def test_alerts_detects_consecutive_negative_months(mock_repo):
    mock_repo.return_value.query_process_monthly_liquida.return_value = [
        {
            "processo_id": "p1",
            "codigo_processo": "PROC-0001",
            "nome_processo": "Teste",
            "filial_id": "01",
            "setor_id": "eng",
            "familia_processo": "ia",
            "agrupador_ferramenta": "chatgpt",
            "competencia": "2025-01",
            "economia_liquida_mes": -100,
        },
        {
            "processo_id": "p1",
            "codigo_processo": "PROC-0001",
            "nome_processo": "Teste",
            "filial_id": "01",
            "setor_id": "eng",
            "familia_processo": "ia",
            "agrupador_ferramenta": "chatgpt",
            "competencia": "2025-02",
            "economia_liquida_mes": -50,
        },
        {
            "processo_id": "p1",
            "codigo_processo": "PROC-0001",
            "nome_processo": "Teste",
            "filial_id": "01",
            "setor_id": "eng",
            "familia_processo": "ia",
            "agrupador_ferramenta": "chatgpt",
            "competencia": "2025-03",
            "economia_liquida_mes": 200,
        },
    ]

    result = DashboardAlertsService(min_consecutive_months=2).list_negative_savings_alerts()
    assert result["total"] == 1
    assert result["items"][0]["months"] == 2
    assert result["items"][0]["economia_liquida_acumulada"] == -150


@patch("tm_app.application.services.process_revision_compare_service.ProcessoRepository")
@patch("tm_app.application.services.process_revision_compare_service.RevisaoRepository")
@patch("tm_app.application.services.process_revision_compare_service.DashboardDataRepository")
def test_revision_compare_returns_items(mock_data, mock_rev, mock_proc):
    raw = _load_fixture("golden_baseline_melhoria.json")
    mock_proc.return_value.get.return_value = raw.processos[0]
    mock_rev.return_value.list_by_processo.return_value = raw.revisoes
    mock_data.return_value.load_raw.return_value = raw

    result = ProcessRevisionCompareService().compare("p1")
    assert result is not None
    assert result["total_revisoes"] == 2
    assert len(result["items"]) == 2


@patch("tm_app.application.services.revisao_rateio_diagnostic_service.RevisaoRepository")
@patch("tm_app.application.services.revisao_rateio_diagnostic_service.DashboardDataRepository")
def test_rateio_diagnostic_ok_when_savings_positive(mock_data, mock_rev):
    raw = _load_fixture("golden_baseline_melhoria.json")
    mock_rev.return_value.get.return_value = raw.revisoes[1]
    mock_data.return_value.load_raw.return_value = raw

    diag = RevisaoRateioDiagnosticService().diagnose("r-melhoria")
    assert diag is not None
    assert diag["rateio_excede_ganho"] is False
