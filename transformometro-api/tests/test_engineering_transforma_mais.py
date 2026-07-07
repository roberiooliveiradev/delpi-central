import json
from pathlib import Path
from unittest.mock import patch

from tm_app.application.integrations.engineering_transforma_mais import (
    EngineeringProcessFilters,
    EngineeringTransformaMaisService,
)
from tm_app.domain.raw_data import TransformometroRawData

FIXTURES = Path(__file__).parent / "fixtures"

_LOAD_RAW = "tm_app.application.integrations.engineering_transforma_mais.load_raw_cached"
_LIVE_SERVICE = "tm_app.application.integrations.engineering_transforma_mais.DashboardLiveService"
_COUNT_FILIAIS = "tm_app.application.integrations.engineering_transforma_mais.count_active_filiais"


def _load_fixture(name: str) -> TransformometroRawData:
    payload = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return TransformometroRawData(**payload)


def _ranking_row(**overrides):
    base = {
        "processo_id": "p1",
        "codigo_processo": "PROC-1",
        "nome_processo": "Processo teste",
        "filial_id": "01",
        "setor_id": "engenharia",
        "economia_diaria": 12.5,
        "data_implantacao": "2025-02-01",
    }
    base.update(overrides)
    return base


@patch(_LIVE_SERVICE)
@patch(_LOAD_RAW)
def test_list_processes_legacy_contract(mock_load, mock_live_cls):
    mock_load.return_value = _load_fixture("golden_baseline_melhoria.json")
    mock_live_cls.return_value.query_ranking_processos.return_value = [_ranking_row()]

    result = EngineeringTransformaMaisService().list_processes(
        EngineeringProcessFilters(start_date="2025-02-01", end_date="2025-02-28")
    )

    assert result["total"] == 1
    item = result["items"][0]
    assert item["id"] == item["processo_id"] == "p1"
    assert item["name_process"] == "Processo teste"
    assert item["daily_savings"] == 12.5
    mock_live_cls.return_value.query_ranking_processos.assert_called_once()
    call_kwargs = mock_live_cls.return_value.query_ranking_processos.call_args.kwargs
    assert call_kwargs["competencia_inicio"] == "2025-02-01"
    assert call_kwargs["competencia_fim"] == "2025-02-28"


@patch(_LIVE_SERVICE)
@patch(_LOAD_RAW)
def test_list_processes_one_row_per_processo_with_multiple_instancias(mock_load, mock_live_cls):
    mock_load.return_value = TransformometroRawData(
        processos=[
            {
                "processo_id": "p1",
                "codigo_processo": "PROC-1",
                "nome_processo": "Processo multi",
                "status_processo": "ativo",
            }
        ],
        processo_instancias=[
            {"instancia_id": "i1", "processo_id": "p1", "codigo_filial": "01"},
            {"instancia_id": "i2", "processo_id": "p1", "codigo_filial": "02"},
        ],
    )
    mock_live_cls.return_value.query_ranking_processos.return_value = [
        _ranking_row(
            nome_processo="Processo multi",
            economia_diaria=215.0,
        )
    ]

    result = EngineeringTransformaMaisService().list_processes(
        EngineeringProcessFilters(start_date="2025-06-01", end_date="2025-06-30")
    )

    assert result["total"] == 1
    item = result["items"][0]
    assert item["id"] == "p1"
    assert item["processo_id"] == "p1"
    assert item["instancia_id"] == "p1"
    assert item["daily_savings"] == 215.0


@patch(_COUNT_FILIAIS, return_value=1)
@patch(_LOAD_RAW)
def test_summary_legacy_contract_fields(mock_load, _mock_filiais):
    mock_load.return_value = _load_fixture("golden_baseline_melhoria.json")

    data = EngineeringTransformaMaisService().get_summary(
        filial_id=None,
        start_date="2025-02-01",
        end_date="2025-02-28",
    )

    assert "implemented_solutions_count" in data
    assert "total_gross_savings_in_period" in data
    assert "monthly_breakdown" in data
    assert isinstance(data["monthly_breakdown"], list)
    if data["monthly_breakdown"]:
        month = data["monthly_breakdown"][0]
        assert "gross_savings_month" in month
        assert "net_savings_month" in month


@patch(_LIVE_SERVICE)
@patch(_LOAD_RAW)
def test_list_processes_filter_by_filial(mock_load, mock_live_cls):
    mock_load.return_value = _load_fixture("golden_baseline_melhoria.json")
    mock_live_cls.return_value.query_ranking_processos.return_value = [_ranking_row(filial_id="01")]

    empty = EngineeringTransformaMaisService().list_processes(
        EngineeringProcessFilters(filial_id="99")
    )
    assert empty["total"] == 0

    hit = EngineeringTransformaMaisService().list_processes(
        EngineeringProcessFilters(
            filial_id="01",
            start_date="2025-02-01",
            end_date="2025-02-28",
        )
    )
    assert hit["total"] == 1


@patch(_COUNT_FILIAIS, return_value=1)
@patch(_LOAD_RAW)
def test_summary_supports_day_level_period(mock_load, _mock_filiais):
    """Fonte única (live) suporta faixa de tempo por dia — não só competência mensal."""
    mock_load.return_value = _load_fixture("golden_baseline_melhoria.json")

    svc = EngineeringTransformaMaisService()
    full_month = svc.get_summary(
        filial_id=None, start_date="2025-02-01", end_date="2025-02-28"
    )
    half_month = svc.get_summary(
        filial_id=None, start_date="2025-02-01", end_date="2025-02-14"
    )

    assert (
        half_month["total_gross_savings_in_period"]
        <= full_month["total_gross_savings_in_period"]
    )
