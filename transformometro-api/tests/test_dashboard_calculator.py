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
    # horas: (100*60 - 100*30) / 60 = 50
    assert row["horas_economizadas_mes"] == 50.0
    assert row["economia_bruta"] >= 2500.0
    assert row["economia_recursos_compartilhados"] == 0.0
    assert row["custo_recursos_compartilhados_mes"] == 150.0
    assert row["investimento_total_mes"] == 150.0
    assert row["economia_liquida_mes"] == row["economia_bruta"] - 150.0
    assert row["codigo_filial"] == "01"
    assert row["codigo_setor"] == "engenharia"
    assert "dashboard_calculo_id" not in row


def test_baseline_row_is_not_materialized():
    raw = _load_fixture("golden_baseline_melhoria.json")
    calc = DashboardCalculatorService()

    rows = [
        row
        for row in calc.build_dashboard_rows(raw)
        if row["revisao_id"] == "r-baseline" and row["competencia"] == "2025-01"
    ]
    assert rows == []


def test_process_without_active_revision_still_calculates_history():
    """Revisões comparáveis inativas entram no histórico por vigência, não só por flag ativa."""
    raw = _load_fixture("golden_baseline_melhoria.json")
    raw.revisoes = [
        {**review, "revisao_ativa": False}
        for review in raw.revisoes
    ]
    calc = DashboardCalculatorService()

    rows = calc.build_dashboard_rows(raw)
    assert any(row["revisao_id"] == "r-melhoria" for row in rows)


def test_process_list_daily_savings_from_bruta():
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
                "investimento_id": "i0",
                "revisao_id": "r-melhoria",
                "tipo_investimento": "unico",
                "categoria_investimento": "setup",
                "descricao_item": "Implantação",
                "quantidade": 1,
                "valor_unitario": 300,
                "valor_total": 300,
                "data_investimento": "2025-02-01",
                "recorrencia": "unico",
                "meses_vigencia": None,
                "centro_custo": "TI",
                "observacoes": None,
                "deletado": False,
            },
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

    assert feb["investimento_unico_mes"] == 300.0
    assert mar["investimento_unico_mes"] == 0.0
    assert feb["custo_recorrente_mes"] == 1200.0
    assert mar["custo_recorrente_mes"] == 1200.0
    assert apr["custo_recorrente_mes"] == 1200.0
    assert may["custo_recorrente_mes"] == 0.0
    assert feb["investimento_total_mes"] == 1500.0
    assert mar["investimento_total_mes"] == 1200.0
    assert apr["investimento_total_mes"] == 1200.0
    assert may["investimento_total_mes"] == 0.0
    assert feb["economia_liquida_mes"] == feb["economia_bruta"] - feb["investimento_total_mes"]


def test_consolidated_roi_without_double_investment_discount():
    raw = _load_fixture("golden_baseline_melhoria.json")
    calc = DashboardCalculatorService()
    summary = calc.build_summary(raw, filial_id=None, start_date=None, end_date=None)

    liquida = float(summary["economia_liquida_total"] or 0)
    investimento = float(summary["investimento_total"] or 0)
    if investimento > 0:
        expected_roi = liquida / investimento
        assert abs(float(summary["roi_medio"] or 0) - expected_roi) < 0.02


def test_proportional_base_competencia_reduces_shared_cost():
    raw = TransformometroRawData(
        processos=[
            {
                "processo_id": "p1",
                "codigo_processo": "PROC-PROP",
                "nome_processo": "Proporcional",
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
                "data_inicio_vigencia": "2025-09-01",
                "revisao_ativa": True,
                "deletado": False,
            },
            {
                "revisao_id": "r-melhoria",
                "processo_id": "p1",
                "cenario_tipo": "melhoria",
                "data_inicio_vigencia": "2025-09-26",
                "data_implantacao": "2025-09-26",
                "revisao_ativa": True,
                "deletado": False,
            },
        ],
        medicoes=[
            {
                "revisao_id": "r-baseline",
                "volume_mensal": 10,
                "tempo_medio_execucao_min": 60,
                "percentual_retrabalho": 0,
                "custo_hora_mao_obra": 50,
                "custo_unitario_retrabalho": 0,
                "tempo_retrabalho_min": 0,
                "quantidade_erros_mes": 0,
                "custo_unitario_erro": 0,
                "custo_outros_desperdicios": 0,
                "deletado": False,
            },
            {
                "revisao_id": "r-melhoria",
                "volume_mensal": 10,
                "tempo_medio_execucao_min": 30,
                "percentual_retrabalho": 0,
                "custo_hora_mao_obra": 50,
                "custo_unitario_retrabalho": 0,
                "tempo_retrabalho_min": 0,
                "quantidade_erros_mes": 0,
                "custo_unitario_erro": 0,
                "custo_outros_desperdicios": 0,
                "deletado": False,
            },
        ],
        investimentos=[],
        recursos_compartilhados=[
            {
                "recurso_compartilhado_id": "rc1",
                "codigo_recurso": "RC-0001",
                "nome_recurso": "Embaixador",
                "categoria_recurso": "horas_internas",
                "tipo_custo": "variavel",
                "recorrencia": "mensal",
                "criterio_rateio": "igualitario",
                "base_competencia": "proporcional_dias",
                "status_recurso": "ativo",
                "valor_total_recorrente": 1000,
                "data_inicio_vigencia": "2025-01-01",
                "deletado": False,
            }
        ],
        revisao_recursos_compartilhados=[
            {
                "vinculo_id": "v1",
                "revisao_id": "r-melhoria",
                "recurso_compartilhado_id": "rc1",
                "data_inicio_uso": "2025-09-26",
                "ativo": True,
                "deletado": False,
            }
        ],
        recurso_custos=[],
    )
    calc = DashboardCalculatorService()
    row = next(
        r
        for r in calc.build_dashboard_rows(raw)
        if r["revisao_id"] == "r-melhoria" and r["competencia"] == "2025-09"
    )
    assert row["custo_recursos_compartilhados_mes"] < 1000.0
    assert row["custo_recursos_compartilhados_mes"] > 0.0


def test_roi_consolidated_matches_liquida_over_investment():
    raw = _load_fixture("golden_baseline_melhoria.json")
    calc = DashboardCalculatorService()
    summary = calc.build_summary(
        raw,
        filial_id=None,
        start_date="2025-06-01",
        end_date="2025-06-03",
    )
    liquida = float(summary["economia_liquida_total"] or 0)
    investimento = float(summary["investimento_total"] or 0)
    if investimento > 0:
        expected = liquida / investimento
        assert abs(float(summary["roi_medio"] or 0) - expected) < 0.02


def test_summary_cards_prorate_partial_day_range():
    raw = _load_fixture("golden_baseline_melhoria.json")
    calc = DashboardCalculatorService()

    full = calc.build_summary(
        raw,
        filial_id=None,
        start_date="2025-02-01",
        end_date="2025-02-28",
    )
    partial = calc.build_summary(
        raw,
        filial_id=None,
        start_date="2025-02-15",
        end_date="2025-02-20",
    )

    assert partial["economia_liquida_total"] < full["economia_liquida_total"]
    assert partial["economia_bruta_total"] < full["economia_bruta_total"]


def test_competencia_day_fraction_single_month():
    calc = DashboardCalculatorService()
    factor = calc.competencia_day_fraction_in_range(
        "2026-06",
        "2026-06-01",
        "2026-06-03",
    )
    assert abs(factor - (3 / 30)) < 1e-6


def test_hours_saved_compares_total_minutes_per_revision_volume():
    """Baseline e melhoria com volumes distintos: soma minutos de cada lado."""
    raw = TransformometroRawData(
        processos=[
            {
                "processo_id": "p1",
                "codigo_processo": "PROC-VOL",
                "nome_processo": "Volume distinto",
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
                "volume_mensal": 1000,
                "tempo_medio_execucao_min": 10,
                "percentual_retrabalho": 0,
                "custo_hora_mao_obra": 50,
                "custo_unitario_retrabalho": 0,
                "tempo_retrabalho_min": 0,
                "quantidade_erros_mes": 0,
                "custo_unitario_erro": 0,
                "custo_outros_desperdicios": 0,
                "deletado": False,
            },
            {
                "revisao_id": "r-melhoria",
                "volume_mensal": 500,
                "tempo_medio_execucao_min": 5,
                "percentual_retrabalho": 0,
                "custo_hora_mao_obra": 50,
                "custo_unitario_retrabalho": 0,
                "tempo_retrabalho_min": 0,
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
    calc = DashboardCalculatorService()
    row = next(
        r
        for r in calc.build_dashboard_rows(raw)
        if r["revisao_id"] == "r-melhoria" and r["competencia"] == "2025-02"
    )
    # (1000*10 - 500*5) / 60 = 125 h — não (10-5)*500/60 ≈ 41,67 h
    assert row["horas_economizadas_mes"] == 125.0


def test_active_fraction_open_review_uses_full_competencia_month():
    """Revisão sem data_fim não deve truncar o mês corrente em date.today()."""
    from datetime import date

    from tm_app.domain import calc_rules

    review = {
        "cenario_tipo": "melhoria",
        "data_inicio_vigencia": "2025-11-05",
        "data_implantacao": "2025-11-05",
        "data_fim_vigencia": None,
    }
    assert calc_rules.review_vigencia_fraction_in_month(review, date(2026, 6, 1)) == 1.0


def test_hours_saved_period_filter_not_double_prorated_with_open_review():
    """Cenário PROC-0020: horas no recorte 4 dias ≠ (MTD vigência) × (filtro dias)."""
    from datetime import date

    raw = TransformometroRawData(
        processos=[
            {
                "processo_id": "p1",
                "codigo_processo": "PROC-X",
                "nome_processo": "Teste",
                "filial_id": "01",
                "setor_id": "producao",
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
                "data_fim_vigencia": "2025-11-05",
                "revisao_ativa": False,
                "deletado": False,
            },
            {
                "revisao_id": "r-melhoria",
                "processo_id": "p1",
                "cenario_tipo": "melhoria",
                "data_inicio_vigencia": "2025-11-05",
                "data_implantacao": "2025-11-05",
                "revisao_ativa": True,
                "deletado": False,
            },
        ],
        medicoes=[
            {
                "revisao_id": "r-baseline",
                "volume_mensal": 336,
                "tempo_medio_execucao_min": 20,
                "percentual_retrabalho": 0,
                "custo_hora_mao_obra": 20.89,
                "custo_unitario_retrabalho": 0,
                "tempo_retrabalho_min": 0,
                "quantidade_erros_mes": 0,
                "custo_unitario_erro": 0,
                "custo_outros_desperdicios": 0,
                "deletado": False,
            },
            {
                "revisao_id": "r-melhoria",
                "volume_mensal": 336,
                "tempo_medio_execucao_min": 0.5,
                "percentual_retrabalho": 0,
                "custo_hora_mao_obra": 20.89,
                "custo_unitario_retrabalho": 0,
                "tempo_retrabalho_min": 0,
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
    calc = DashboardCalculatorService()
    row = next(
        r
        for r in calc.build_dashboard_rows(raw)
        if r["revisao_id"] == "r-melhoria" and r["competencia"] == "2026-06"
    )
    assert row["horas_economizadas_mes"] == 109.2

    summary = calc.build_summary(raw, None, "2026-06-01", "2026-06-04")
    assert summary["horas_economizadas_total"] == 14.56

    prorated = calc._prorate_row_metrics_for_period(
        row, start_date="2026-06-01", end_date="2026-06-04"
    )
    assert prorated["horas_economizadas_mes"] == 14.56
    assert round(prorated["horas_economizadas_mes"] / 4, 2) == 3.64


def test_parse_date_accepts_iso_datetime():
    calc = DashboardCalculatorService()

    assert calc._parse_date("2025-01-01T00:00:00.000Z") == date(2025, 1, 1)
    assert calc._parse_date("2025-01-01T03:00:00+00:00") == date(2025, 1, 1)


def test_build_summary_does_not_crash_when_period_filter_is_unparseable():
    raw = _load_fixture("golden_baseline_melhoria.json")
    calc = DashboardCalculatorService()

    summary = calc.build_summary(
        raw,
        filial_id=None,
        start_date="undefined",
        end_date="2025-03-31",
    )

    assert summary["economia_liquida_total"] is not None
    assert summary["evolucao_mensal"]


def test_build_summary_accepts_wide_yyyy_mm_dd_range():
    raw = _load_fixture("golden_baseline_melhoria.json")
    calc = DashboardCalculatorService()

    summary = calc.build_summary(
        raw,
        filial_id=None,
        start_date="2025-01-01",
        end_date="2026-06-11",
    )

    assert summary["evolucao_mensal"]
    assert summary["economia_liquida_total"] is not None
