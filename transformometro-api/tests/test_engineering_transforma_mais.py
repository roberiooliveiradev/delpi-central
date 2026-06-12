import json
from pathlib import Path
from unittest.mock import patch

from tm_app.application.integrations.engineering_transforma_mais import (
    EngineeringProcessFilters,
    EngineeringTransformaMaisService,
)
from tm_app.domain.raw_data import TransformometroRawData

FIXTURES = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> TransformometroRawData:
    payload = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return TransformometroRawData(**payload)


def _mock_cache_empty(mock_cache):
    mock_cache.return_value.count.return_value = 0


@patch("tm_app.application.integrations.engineering_transforma_mais.DashboardCalculoRepository")
@patch("tm_app.application.integrations.engineering_transforma_mais.DashboardDataRepository")
def test_list_processes_legacy_contract(mock_repo, mock_cache):
    _mock_cache_empty(mock_cache)
    raw = _load_fixture("golden_baseline_melhoria.json")
    mock_repo.return_value.load_raw.return_value = raw

    result = EngineeringTransformaMaisService().list_processes(EngineeringProcessFilters())

    assert result["total"] == 1
    item = result["items"][0]
    assert item["id"] == "p1"
    assert item["processo_id"] == "p1"
    assert item["instancia_id"] == "p1"
    assert item["name_process"] == "Processo teste"
    assert item["daily_savings"] is not None
    assert item["daily_savings"] > 0


@patch("tm_app.application.integrations.engineering_transforma_mais.DashboardCalculoRepository")
@patch("tm_app.application.integrations.engineering_transforma_mais.DashboardDataRepository")
def test_list_processes_one_row_per_instancia(mock_repo, mock_cache):
    _mock_cache_empty(mock_cache)
    raw = TransformometroRawData(
        processos=[
            {
                "processo_id": "p1",
                "codigo_processo": "PROC-1",
                "nome_processo": "Processo multi",
                "status_processo": "ativo",
            }
        ],
        processo_instancias=[
            {
                "instancia_id": "i1",
                "processo_id": "p1",
                "codigo_filial": "01",
                "codigo_setor": "engenharia",
            },
            {
                "instancia_id": "i2",
                "processo_id": "p1",
                "codigo_filial": "02",
                "codigo_setor": "producao",
            },
        ],
        revisoes=[
            {
                "revisao_id": "r1",
                "processo_id": "p1",
                "instancia_id": "i1",
                "versao_revisao": "1.0",
                "cenario_tipo": "baseline",
                "data_inicio_vigencia": "2025-01-01",
                "revisao_ativa": False,
                "deletado": False,
            },
            {
                "revisao_id": "r2",
                "processo_id": "p1",
                "instancia_id": "i1",
                "versao_revisao": "2.0",
                "cenario_tipo": "melhoria",
                "data_inicio_vigencia": "2025-02-01",
                "revisao_ativa": True,
                "deletado": False,
            },
            {
                "revisao_id": "r3",
                "processo_id": "p1",
                "instancia_id": "i2",
                "versao_revisao": "1.0",
                "cenario_tipo": "baseline",
                "data_inicio_vigencia": "2025-01-01",
                "revisao_ativa": False,
                "deletado": False,
            },
        ],
        medicoes=[
            {
                "revisao_id": "r1",
                "volume_mensal": 100,
                "tempo_medio_execucao_min": 60,
                "percentual_retrabalho": 0.1,
                "custo_hora_mao_obra": 50,
                "deletado": False,
            },
            {
                "revisao_id": "r2",
                "volume_mensal": 100,
                "tempo_medio_execucao_min": 30,
                "percentual_retrabalho": 0.05,
                "custo_hora_mao_obra": 50,
                "deletado": False,
            },
            {
                "revisao_id": "r3",
                "volume_mensal": 50,
                "tempo_medio_execucao_min": 40,
                "percentual_retrabalho": 0.1,
                "custo_hora_mao_obra": 50,
                "deletado": False,
            },
        ],
    )
    mock_repo.return_value.load_raw.return_value = raw

    result = EngineeringTransformaMaisService().list_processes(EngineeringProcessFilters())

    assert result["total"] == 2
    ids = {item["id"] for item in result["items"]}
    assert ids == {"i1", "i2"}
    assert all(item["processo_id"] == "p1" for item in result["items"])
    by_inst = {item["id"]: item for item in result["items"]}
    assert by_inst["i1"]["filial_id"] == "01"
    assert by_inst["i2"]["filial_id"] == "02"


@patch("tm_app.application.integrations.engineering_transforma_mais.DashboardCalculoRepository")
@patch("tm_app.application.integrations.engineering_transforma_mais.DashboardDataRepository")
def test_summary_legacy_contract_fields(mock_repo, mock_cache):
    _mock_cache_empty(mock_cache)
    raw = _load_fixture("golden_baseline_melhoria.json")
    mock_repo.return_value.load_raw.return_value = raw

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


@patch("tm_app.application.integrations.engineering_transforma_mais.DashboardCalculoRepository")
@patch("tm_app.application.integrations.engineering_transforma_mais.DashboardDataRepository")
def test_list_processes_filter_by_filial(mock_repo, mock_cache):
    _mock_cache_empty(mock_cache)
    raw = _load_fixture("golden_baseline_melhoria.json")
    mock_repo.return_value.load_raw.return_value = raw

    empty = EngineeringTransformaMaisService().list_processes(
        EngineeringProcessFilters(filial_id="99")
    )
    assert empty["total"] == 0

    hit = EngineeringTransformaMaisService().list_processes(
        EngineeringProcessFilters(filial_id="01")
    )
    assert hit["total"] == 1


@patch("tm_app.application.integrations.engineering_transforma_mais.DashboardCalculoRepository")
@patch("tm_app.application.integrations.engineering_transforma_mais.DashboardDataRepository")
def test_list_processes_from_cache(mock_repo, mock_cache):
    mock_cache.return_value.count.return_value = 3
    mock_cache.return_value.query_instancias_operacionais.return_value = [
        {
            "instancia_id": "i1",
            "processo_id": "p1",
            "codigo_processo": "PROC-1",
            "nome_processo": "Processo cache",
            "status_processo": "ativo",
            "filial_id": "01",
            "setor_id": "engenharia",
            "economia_diaria": 120.5,
            "payback_meses": 6.0,
            "data_implantacao": "2025-01-15",
        }
    ]

    result = EngineeringTransformaMaisService().list_processes(EngineeringProcessFilters())

    mock_repo.return_value.load_raw.assert_not_called()
    assert result["total"] == 1
    item = result["items"][0]
    assert item["id"] == "i1"
    assert item["daily_savings"] == 120.5
    assert item["payback_months"] == 6.0


@patch("tm_app.application.integrations.engineering_transforma_mais.DashboardCalculoRepository")
@patch("tm_app.application.integrations.engineering_transforma_mais.DashboardDataRepository")
def test_summary_from_cache(mock_repo, mock_cache):
    mock_cache.return_value.count.return_value = 10
    mock_cache.return_value.query_resumo.return_value = {
        "solucoes_implementadas": 2,
        "economia_bruta_total": 1000.0,
        "economia_liquida_total": 800.0,
        "investimento_total": 400.0,
        "horas_economizadas_total": 12.0,
    }
    mock_cache.return_value.query_evolucao.return_value = [
        {
            "competencia": "2025-02",
            "economia_bruta": 1000.0,
            "investimento_unico_mes": 200.0,
            "custo_recorrente_mes": 100.0,
            "custo_recursos_compartilhados_mes": 100.0,
            "investimento_total_mes": 400.0,
            "economia_liquida_mes": 800.0,
        }
    ]

    data = EngineeringTransformaMaisService().get_summary(
        filial_id="01",
        start_date="2025-02-01",
        end_date="2025-02-28",
    )

    mock_repo.return_value.load_raw.assert_not_called()
    mock_cache.return_value.query_resumo.assert_called_once_with(
        filial_id="01",
        competencia_inicio="2025-02",
        competencia_fim="2025-02",
    )
    assert data["implemented_solutions_count"] == 2
    assert data["total_net_savings_until_now"] == 800.0
    assert data["average_roi"] == 2.0
    assert data["monthly_breakdown"][0]["month"] == "2025-02"
