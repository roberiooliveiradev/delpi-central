import json
from datetime import date
from pathlib import Path

from tm_app.domain.raw_data import TransformometroRawData
from tm_app.domain.services.dashboard_calculator import DashboardCalculatorService

FIXTURES = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> TransformometroRawData:
    payload = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return TransformometroRawData(**payload)


def test_golden_baseline_melhoria_economia_bruta_positiva():
    raw = _load_fixture("golden_baseline_melhoria.json")
    calc = DashboardCalculatorService()

    rows = [
        row
        for row in calc.build_dashboard_rows(raw)
        if row["revisao_id"] == "r-melhoria" and row["competencia"] == "2025-02"
    ]
    assert len(rows) == 1
    row = rows[0]

    # tempo: 100 * (60-30)/60 * 50 = 2500
    assert row["economia_tempo"] == 2500.0
    assert row["economia_bruta"] >= 2500.0
    assert row["economia_recursos_compartilhados"] == 0.0
    assert row["economia_liquida_mes"] == row["economia_bruta"]


def test_baseline_row_economia_bruta_zero():
    raw = _load_fixture("golden_baseline_melhoria.json")
    calc = DashboardCalculatorService()

    rows = [
        row
        for row in calc.build_dashboard_rows(raw)
        if row["revisao_id"] == "r-baseline" and row["competencia"] == "2025-01"
    ]
    assert len(rows) == 1
    assert rows[0]["economia_bruta"] == 0.0


def test_process_list_daily_savings_from_liquida():
    raw = _load_fixture("golden_baseline_melhoria.json")
    calc = DashboardCalculatorService()

    items = calc.build_process_list(raw)
    assert len(items) == 1
    daily = items[0]["economia_diaria"]
    assert daily is not None
    assert daily > 0


def test_process_list_uses_first_non_baseline_implementation_date():
    raw = _load_fixture("golden_baseline_melhoria.json")
    raw.revisoes[1] = {
        **raw.revisoes[1],
        "data_implantacao": "2025-02-10",
        "revisao_ativa": False,
    }
    raw.revisoes.append(
        {
            "revisao_id": "r-automacao",
            "processo_id": "p1",
            "versao_revisao": "3.0.0",
            "cenario_tipo": "automacao",
            "data_implantacao": "2025-04-15",
            "data_inicio_vigencia": "2025-04-01",
            "revisao_ativa": True,
            "deletado": False,
        }
    )
    raw.medicoes.append(
        {
            **raw.medicoes[1],
            "revisao_id": "r-automacao",
            "tempo_medio_execucao_min": 20,
        }
    )
    calc = DashboardCalculatorService()

    items = calc.build_process_list(raw)

    assert items[0]["data_implantacao"] == "10/02/2025"


def test_max_zero_when_melhoria_piora_tempo():
    raw = _load_fixture("golden_baseline_melhoria.json")
    raw.revisoes[1] = {**raw.revisoes[1], "data_inicio_vigencia": "2025-03-01"}
    raw.medicoes[1] = {
        **raw.medicoes[1],
        "tempo_medio_execucao_min": 120,
    }
    calc = DashboardCalculatorService()
    rows = [
        row
        for row in calc.build_dashboard_rows(raw)
        if row["revisao_id"] == "r-melhoria" and row["competencia"] == "2025-03"
    ]
    assert rows[0]["economia_tempo"] == 0.0


def test_recurring_investment_spreads_over_active_months():
    raw = TransformometroRawData(
        processos=[
            {
                "processo_id": "p1",
                "codigo_processo": "PROC-0001",
                "nome_processo": "Processo Recorrente",
                "filial_id": "01",
                "setor_id": "engenharia",
                "status_processo": "ativo",
                "deletado": False,
            }
        ],
        revisoes=[
            {
                "revisao_id": "r-baseline",
                "processo_id": "p1",
                "cenario_tipo": "baseline",
                "data_inicio_vigencia": "2025-01-01",
                "revisao_ativa": False,
                "deletado": False,
            },
            {
                "revisao_id": "r-melhoria",
                "processo_id": "p1",
                "cenario_tipo": "melhoria",
                "data_inicio_vigencia": "2025-02-01",
                "revisao_ativa": True,
                "deletado": False,
            },
        ],
        medicoes=[
            {
                "revisao_id": "r-baseline",
                "volume_mensal": 100,
                "tempo_medio_execucao_min": 60,
                "percentual_retrabalho": 0.1,
                "custo_hora_mao_obra": 50,
                "custo_unitario_retrabalho": 0,
                "tempo_retrabalho_min": 10,
                "quantidade_erros_mes": 0,
                "custo_unitario_erro": 0,
                "custo_outros_desperdicios": 0,
                "deletado": False,
            },
            {
                "revisao_id": "r-melhoria",
                "volume_mensal": 100,
                "tempo_medio_execucao_min": 30,
                "percentual_retrabalho": 0.05,
                "custo_hora_mao_obra": 50,
                "custo_unitario_retrabalho": 0,
                "tempo_retrabalho_min": 10,
                "quantidade_erros_mes": 0,
                "custo_unitario_erro": 0,
                "custo_outros_desperdicios": 0,
                "deletado": False,
            },
        ],
        investimentos=[
            {
                "investimento_id": "i1",
                "revisao_id": "r-melhoria",
                "tipo_investimento": "fixo",
                "categoria_investimento": "infra",
                "descricao_item": "Assinatura",
                "quantidade": 1,
                "valor_unitario": 1200,
                "valor_total": 1200,
                "data_investimento": "2025-02-01",
                "recorrencia": "mensal",
                "meses_vigencia": 3,
                "centro_custo": "TI",
                "observacoes": None,
                "deletado": False,
            }
        ],
        recursos_compartilhados=[],
        revisao_recursos_compartilhados=[],
        recurso_custos=[],
    )

    calc = DashboardCalculatorService()
    rows = [
        row for row in calc.build_dashboard_rows(raw) if row["revisao_id"] == "r-melhoria"
    ]
    assert len(rows) >= 3
    feb = next(row for row in rows if row["competencia"] == "2025-02")
    mar = next(row for row in rows if row["competencia"] == "2025-03")
    apr = next(row for row in rows if row["competencia"] == "2025-04")
    may = next(row for row in rows if row["competencia"] == "2025-05")

    assert feb["custo_recorrente_mes"] == 1200.0
    assert mar["custo_recorrente_mes"] == 1200.0
    assert apr["custo_recorrente_mes"] == 1200.0
    assert may["custo_recorrente_mes"] == 0.0
    assert feb["investimento_total_mes"] == 1200.0
    assert mar["investimento_total_mes"] == 1200.0
    assert apr["investimento_total_mes"] == 1200.0
    assert may["investimento_total_mes"] == 0.0
