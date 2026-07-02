from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from tm_app.application.services.dashboard_live_service import DashboardLiveService
from tm_app.domain import calc_rules
from tm_app.domain.raw_data import TransformometroRawData

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def _default_active_filiais_count(monkeypatch):
    monkeypatch.setattr(
        "tm_app.application.services.dashboard_view_scope_service.count_active_filiais",
        lambda: 2,
    )


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
def test_build_summary_roi_consolidated_without_double_discount(mock_repo):
    raw = _load_fixture("golden_baseline_melhoria.json")
    mock_repo.return_value.load_raw.return_value = raw

    summary = DashboardLiveService().build_summary()

    liquida = float(summary.get("economia_liquida_total") or 0)
    investimento = float(summary.get("investimento_total") or 0)
    if investimento > 0:
        assert abs(float(summary.get("roi_medio") or 0) - liquida / investimento) < 0.02


@patch(
    "tm_app.application.services.dashboard_view_scope_service.count_active_filiais"
)
@patch("tm_app.application.services.dashboard_live_service.DashboardDataRepository")
def test_build_summary_consolidado_escala_instancia_multi_unidade(
    mock_repo, mock_count_filiais
):
    from tm_app.application.services.dashboard_query_cache import dashboard_query_cache
    from tm_app.domain.raw_data import TransformometroRawData

    dashboard_query_cache.invalidate()
    mock_count_filiais.return_value = 2
    raw = TransformometroRawData(
        processos=[
            {
                "processo_id": "p1",
                "codigo_processo": "PROC-MU",
                "nome_processo": "Multi",
                "status_processo": "ativo",
                "deletado": False,
            }
        ],
        processo_instancias=[
            {
                "instancia_id": "i-all",
                "processo_id": "p1",
                "todas_filiais_ativas": True,
                "setores": [{"codigo_setor": "eng", "setor_id": "eng"}],
                "deletado": False,
            }
        ],
        revisoes=[
            {
                "revisao_id": "r-base",
                "processo_id": "p1",
                "instancia_id": "i-all",
                "cenario_tipo": "baseline",
                "data_inicio_vigencia": "2025-01-01",
                "revisao_ativa": False,
                "deletado": False,
            },
            {
                "revisao_id": "r-mel",
                "processo_id": "p1",
                "instancia_id": "i-all",
                "cenario_tipo": "melhoria",
                "data_inicio_vigencia": "2025-06-01",
                "data_implantacao": "2025-06-01",
                "revisao_ativa": True,
                "deletado": False,
            },
        ],
        medicoes=[
            _medicao_live("r-base", 60),
            _medicao_live("r-mel", 30),
        ],
    )
    mock_repo.return_value.load_raw.return_value = raw

    summary = DashboardLiveService().build_summary(
        competencia_inicio="2025-06-01",
        competencia_fim="2025-06-30",
    )

    bruta_jun = next(
        item["economia_bruta"]
        for item in summary["evolucao_mensal"]
        if item["competencia"] == "2025-06"
    )
    assert bruta_jun == 5000.0
    assert summary["scope"]["escopo_unidades"] == 2


@patch("tm_app.application.services.dashboard_live_service.DashboardDataRepository")
def test_query_ranking_processos_uses_first_implementation_date_but_keeps_later_active_rows(mock_repo):
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

    assert [row["processo_id"] for row in rows] == ["p1", "p2"]
    assert rows[0]["data_implantacao"] == "2025-02-10"
    assert rows[0]["revisao_implantacao_id"] == "p1-melhoria"
    assert rows[0]["investimento_total_mes"] == 0.0
    assert rows[1]["data_implantacao"] == "2025-06-05"
    assert rows[1]["revisao_implantacao_id"] == "p2-melhoria"


def _medicao_live(revisao_id: str, tempo: float) -> dict:
    return {
        "revisao_id": revisao_id,
        "volume_mensal": 100,
        "tempo_medio_execucao_min": tempo,
        "percentual_retrabalho": 0,
        "custo_hora_mao_obra": 50,
        "quantidade_erros_mes": 0,
        "custo_unitario_erro": 0,
        "custo_outros_desperdicios": 0,
        "deletado": False,
    }


def _multi_instancia_raw_live() -> TransformometroRawData:
    return TransformometroRawData(
        processos=[
            {
                "processo_id": "p1",
                "codigo_processo": "PROC-MULTI",
                "nome_processo": "Multi-instância",
                "status_processo": "ativo",
                "deletado": False,
            }
        ],
        processo_instancias=[
            {
                "instancia_id": "i-sc",
                "processo_id": "p1",
                "filial_id": "01",
                "codigo_filial": "01",
                "setores": [{"codigo_setor": "eng", "setor_id": "eng"}],
                "deletado": False,
            },
            {
                "instancia_id": "i-es",
                "processo_id": "p1",
                "filial_id": "02",
                "codigo_filial": "02",
                "setores": [{"codigo_setor": "eng", "setor_id": "eng"}],
                "deletado": False,
            },
        ],
        revisoes=[
            {
                "revisao_id": "r-sc-base",
                "processo_id": "p1",
                "instancia_id": "i-sc",
                "cenario_tipo": "baseline",
                "data_inicio_vigencia": "2025-01-01",
                "revisao_ativa": False,
                "deletado": False,
            },
            {
                "revisao_id": "r-sc-mel",
                "processo_id": "p1",
                "instancia_id": "i-sc",
                "cenario_tipo": "melhoria",
                "data_inicio_vigencia": "2025-04-01",
                "revisao_ativa": True,
                "deletado": False,
            },
            {
                "revisao_id": "r-es-base",
                "processo_id": "p1",
                "instancia_id": "i-es",
                "cenario_tipo": "baseline",
                "data_inicio_vigencia": "2025-03-01",
                "revisao_ativa": False,
                "deletado": False,
            },
            {
                "revisao_id": "r-es-mel",
                "processo_id": "p1",
                "instancia_id": "i-es",
                "cenario_tipo": "melhoria",
                "data_inicio_vigencia": "2025-04-01",
                "revisao_ativa": True,
                "deletado": False,
            },
        ],
        medicoes=[
            _medicao_live("r-sc-base", 60),
            _medicao_live("r-sc-mel", 30),  # 2500/mês
            _medicao_live("r-es-base", 60),
            _medicao_live("r-es-mel", 48),  # 1000/mês
        ],
        investimentos=[],
        recursos_compartilhados=[],
        revisao_recursos_compartilhados=[],
        recurso_custos=[],
    )


@patch("tm_app.application.services.dashboard_live_service.DashboardDataRepository")
def test_process_monthly_liquida_uses_instance_average(mock_repo):
    """Alertas: economia líquida por processo/mês é a média das instâncias ativas."""
    mock_repo.return_value.load_raw.return_value = _multi_instancia_raw_live()

    rows = DashboardLiveService().query_process_monthly_liquida(
        competencia_inicio="2025-04-01",
        competencia_fim="2025-04-30",
    )

    abril = [r for r in rows if r["competencia"] == "2025-04" and r["processo_id"] == "p1"]
    assert len(abril) == 1
    # média (2500 + 1000) / 2 = 1750, não a soma 3500.
    assert abril[0]["economia_liquida_mes"] == 1750.0


def _venc_processo(pid: str, mel_start: date) -> dict:
    return {
        "processo": {
            "processo_id": pid, "codigo_processo": f"P-{pid}", "nome_processo": pid,
            "status_processo": "ativo", "deletado": False,
        },
        "instancia": {
            "instancia_id": f"i-{pid}", "processo_id": pid, "filial_id": "01",
            "codigo_filial": "01", "setores": [{"codigo_setor": "eng", "setor_id": "eng"}],
            "deletado": False,
        },
        "revisoes": [
            {
                "revisao_id": f"b-{pid}", "processo_id": pid, "instancia_id": f"i-{pid}",
                "cenario_tipo": "baseline", "data_inicio_vigencia": "2023-01-01",
                "revisao_ativa": False, "deletado": False,
            },
            {
                "revisao_id": f"m-{pid}", "processo_id": pid, "instancia_id": f"i-{pid}",
                "cenario_tipo": "melhoria", "data_inicio_vigencia": mel_start.isoformat(),
                "data_implantacao": mel_start.isoformat(), "revisao_ativa": True, "deletado": False,
            },
        ],
        "medicoes": [
            {"revisao_id": f"b-{pid}", "volume_mensal": 100, "tempo_medio_execucao_min": 60,
             "custo_hora_mao_obra": 50, "deletado": False},
            {"revisao_id": f"m-{pid}", "volume_mensal": 100, "tempo_medio_execucao_min": 30,
             "custo_hora_mao_obra": 50, "deletado": False},
        ],
    }


def _familia_setor_raw() -> TransformometroRawData:
    def _proc(pid: str, setor: str, familia: str) -> dict:
        return {
            "processo_id": pid,
            "codigo_processo": f"P-{pid}",
            "nome_processo": pid,
            "familia_processo": familia,
            "status_processo": "ativo",
            "deletado": False,
        }

    def _inst(pid: str, setor: str) -> dict:
        return {
            "instancia_id": f"i-{pid}",
            "processo_id": pid,
            "filial_id": "01",
            "codigo_filial": "01",
            "setores": [{"codigo_setor": setor, "setor_id": setor}],
            "deletado": False,
        }

    def _revs(pid: str) -> list[dict]:
        return [
            {
                "revisao_id": f"b-{pid}", "processo_id": pid, "instancia_id": f"i-{pid}",
                "cenario_tipo": "baseline", "data_inicio_vigencia": "2026-01-01",
                "revisao_ativa": False, "deletado": False,
            },
            {
                "revisao_id": f"m-{pid}", "processo_id": pid, "instancia_id": f"i-{pid}",
                "cenario_tipo": "melhoria", "data_inicio_vigencia": "2026-06-01",
                "data_implantacao": "2026-06-01", "revisao_ativa": True, "deletado": False,
            },
        ]

    procs = [("pc", "comercial", "Familia Comercial"), ("pe", "eng", "Familia Eng")]
    return TransformometroRawData(
        processos=[_proc(pid, setor, fam) for pid, setor, fam in procs],
        processo_instancias=[_inst(pid, setor) for pid, setor, _ in procs],
        revisoes=[r for pid, _, _ in procs for r in _revs(pid)],
        medicoes=[
            m
            for pid, _, _ in procs
            for m in (_medicao_live(f"b-{pid}", 60), _medicao_live(f"m-{pid}", 30))
        ],
        investimentos=[], recursos_compartilhados=[],
        revisao_recursos_compartilhados=[], recurso_custos=[],
    )


@patch("tm_app.application.services.dashboard_live_service.DashboardDataRepository")
def test_query_resumo_por_familia_filtra_por_setor(mock_repo):
    """Visão departamento (setor) não deve dar erro e deve filtrar por família do setor."""
    mock_repo.return_value.load_raw.return_value = _familia_setor_raw()

    rows = DashboardLiveService().query_resumo_por_familia(
        view="department",
        filial_id="01",
        setor_id="comercial",
        competencia_inicio="2026-07-01",
        competencia_fim="2026-07-31",
    )

    familias = {row["familia_processo"] for row in rows}
    assert familias == {"Familia Comercial"}


@patch("tm_app.application.services.dashboard_live_service.DashboardDataRepository")
def test_list_vencimentos_separa_vencendo_e_vencidas(mock_repo):
    today = date.today()
    # Aniversário ~ hoje+30d (vencendo), ~ hoje-1m (vencida), ~ hoje+11m (vigente).
    procs = [
        _venc_processo("venc", calc_rules.add_months(today + timedelta(days=30), -12)),
        _venc_processo("vcda", calc_rules.add_months(today, -13)),
        _venc_processo("vige", calc_rules.add_months(today, -1)),
    ]
    raw = TransformometroRawData(
        processos=[p["processo"] for p in procs],
        processo_instancias=[p["instancia"] for p in procs],
        revisoes=[r for p in procs for r in p["revisoes"]],
        medicoes=[m for p in procs for m in p["medicoes"]],
        investimentos=[], recursos_compartilhados=[],
        revisao_recursos_compartilhados=[], recurso_custos=[],
    )
    mock_repo.return_value.load_raw.return_value = raw

    data = DashboardLiveService().list_vencimentos(dias=90)

    assert data["janela_dias"] == 90
    assert data["total_vencendo"] == 1
    assert data["vencendo"][0]["processo_id"] == "venc"
    assert data["total_vencidas"] == 1
    assert data["vencidas"][0]["processo_id"] == "vcda"
