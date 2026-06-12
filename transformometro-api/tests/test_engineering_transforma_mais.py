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


@patch("tm_app.application.integrations.engineering_transforma_mais.DashboardDataRepository")
def test_list_processes_legacy_contract(mock_repo):
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


@patch("tm_app.application.integrations.engineering_transforma_mais.DashboardDataRepository")
def test_list_processes_one_row_per_instancia(mock_repo):
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


@patch("tm_app.application.integrations.engineering_transforma_mais.DashboardDataRepository")
def test_summary_legacy_contract_fields(mock_repo):
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


@patch("tm_app.application.integrations.engineering_transforma_mais.DashboardDataRepository")
def test_list_processes_filter_by_filial(mock_repo):
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
