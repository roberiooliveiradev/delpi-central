from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from tm_app.application.services.dashboard_live_service import DashboardLiveService
from tm_app.domain.raw_data import TransformometroRawData

FIXTURES = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> TransformometroRawData:
    payload = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return TransformometroRawData(**payload)


@patch("tm_app.application.services.dashboard_live_service.DashboardDataRepository")
def test_build_summary_marks_live_source(mock_repo):
    raw = _load_fixture("golden_baseline_melhoria.json")
    mock_repo.return_value.load_raw.return_value = raw

    summary = DashboardLiveService().build_summary()

    assert summary["fonte"] == "cadastro_tempo_real"
    assert "economia_liquida_total" in summary
    assert isinstance(summary.get("evolucao_mensal"), list)


@patch("tm_app.application.services.dashboard_live_service.DashboardDataRepository")
def test_query_ranking_processos_filters_by_first_non_baseline_implementation_date(mock_repo):
    raw = TransformometroRawData(
        processos=[
            {
                "processo_id": "p1",
                "codigo_processo": "PROC-0001",
                "nome_processo": "Processo com revisao posterior",
                "filial_id": "01",
                "setor_id": "engenharia",
                "status_processo": "ativo",
                "created_at": "2025-01-01",
                "deletado": False,
            },
            {
                "processo_id": "p2",
                "codigo_processo": "PROC-0002",
                "nome_processo": "Processo implantado no recorte",
                "filial_id": "01",
                "setor_id": "engenharia",
                "status_processo": "ativo",
                "created_at": "2025-05-01",
                "deletado": False,
            },
        ],
        revisoes=[
            {
                "revisao_id": "p1-baseline",
                "processo_id": "p1",
                "versao_revisao": "1.0.0",
                "cenario_tipo": "baseline",
                "data_inicio_vigencia": "2025-01-01",
                "revisao_ativa": False,
                "deletado": False,
            },
            {
                "revisao_id": "p1-melhoria",
                "processo_id": "p1",
                "versao_revisao": "2.0.0",
                "cenario_tipo": "melhoria",
                "data_implantacao": "2025-02-10",
                "data_inicio_vigencia": "2025-02-01",
                "revisao_ativa": False,
                "deletado": False,
            },
            {
                "revisao_id": "p1-automacao",
                "processo_id": "p1",
                "versao_revisao": "3.0.0",
                "cenario_tipo": "automacao",
                "data_implantacao": "2025-06-05",
                "data_inicio_vigencia": "2025-06-01",
                "revisao_ativa": True,
                "deletado": False,
            },
            {
                "revisao_id": "p2-baseline",
                "processo_id": "p2",
                "versao_revisao": "1.0.0",
                "cenario_tipo": "baseline",
                "data_inicio_vigencia": "2025-05-01",
                "revisao_ativa": False,
                "deletado": False,
            },
            {
                "revisao_id": "p2-melhoria",
                "processo_id": "p2",
                "versao_revisao": "2.0.0",
                "cenario_tipo": "melhoria",
                "data_implantacao": "2025-06-05",
                "data_inicio_vigencia": "2025-06-01",
                "revisao_ativa": True,
                "deletado": False,
            },
        ],
        medicoes=[
            {
                "revisao_id": "p1-baseline",
                "volume_mensal": 100,
                "tempo_medio_execucao_min": 60,
                "percentual_retrabalho": 0,
                "custo_hora_mao_obra": 60,
                "quantidade_erros_mes": 0,
                "custo_unitario_erro": 0,
                "custo_outros_desperdicios": 0,
                "deletado": False,
            },
            {
                "revisao_id": "p1-melhoria",
                "volume_mensal": 100,
                "tempo_medio_execucao_min": 40,
                "percentual_retrabalho": 0,
                "custo_hora_mao_obra": 60,
                "quantidade_erros_mes": 0,
                "custo_unitario_erro": 0,
                "custo_outros_desperdicios": 0,
                "deletado": False,
            },
            {
                "revisao_id": "p1-automacao",
                "volume_mensal": 100,
                "tempo_medio_execucao_min": 20,
                "percentual_retrabalho": 0,
                "custo_hora_mao_obra": 60,
                "quantidade_erros_mes": 0,
                "custo_unitario_erro": 0,
                "custo_outros_desperdicios": 0,
                "deletado": False,
            },
            {
                "revisao_id": "p2-baseline",
                "volume_mensal": 100,
                "tempo_medio_execucao_min": 60,
                "percentual_retrabalho": 0,
                "custo_hora_mao_obra": 60,
                "quantidade_erros_mes": 0,
                "custo_unitario_erro": 0,
                "custo_outros_desperdicios": 0,
                "deletado": False,
            },
            {
                "revisao_id": "p2-melhoria",
                "volume_mensal": 100,
                "tempo_medio_execucao_min": 30,
                "percentual_retrabalho": 0,
                "custo_hora_mao_obra": 60,
                "quantidade_erros_mes": 0,
                "custo_unitario_erro": 0,
                "custo_outros_desperdicios": 0,
                "deletado": False,
            },
        ],
        investimentos=[],
        recursos_compartilhados=[],
        revisao_recursos_compartilhados=[],
        recurso_custos=[],
    )
    mock_repo.return_value.load_raw.return_value = raw

    rows = DashboardLiveService().query_ranking_processos(
        competencia_inicio="2025-06-01",
        competencia_fim="2025-06-30",
    )

    assert [row["processo_id"] for row in rows] == ["p2"]
    assert rows[0]["data_implantacao"] == "2025-06-05"
    assert rows[0]["revisao_implantacao_id"] == "p2-melhoria"
