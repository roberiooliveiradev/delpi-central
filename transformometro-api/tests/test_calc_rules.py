"""Testes das regras centralizadas (tm_app/domain/calc_rules.py)."""

from datetime import date

from datetime import date
from unittest.mock import patch

from tm_app.domain import calc_rules


def test_count_active_implemented_improvements_counts_distinct_instancias():
    instancias = [
        {"instancia_id": "i1", "deletado": False},
        {"instancia_id": "i2", "deletado": False},
    ]
    revisoes = [
        {
            "instancia_id": "i1",
            "cenario_tipo": "melhoria",
            "revisao_ativa": True,
            "deletado": False,
        },
        {
            "instancia_id": "i1",
            "cenario_tipo": "automacao",
            "revisao_ativa": False,
            "deletado": False,
        },
        {
            "instancia_id": "i2",
            "cenario_tipo": "baseline",
            "revisao_ativa": True,
            "deletado": False,
        },
    ]
    assert calc_rules.count_active_implemented_improvements(
        instancias=instancias,
        revisoes=revisoes,
    ) == 1


def test_review_vigencia_open_review_full_month():
    review = {
        "cenario_tipo": "melhoria",
        "data_inicio_vigencia": "2025-11-05",
        "data_implantacao": "2025-11-05",
        "data_fim_vigencia": None,
    }
    assert calc_rules.review_vigencia_fraction_in_month(review, date(2026, 6, 1)) == 1.0


def test_review_validity_end_date_is_start_plus_12_months():
    review = {
        "cenario_tipo": "melhoria",
        "data_inicio_vigencia": "2025-06-01",
        "data_implantacao": "2025-06-01",
    }
    assert calc_rules.review_validity_end_date(review) == date(2026, 6, 1)
    # Último dia efetivo é a véspera do aniversário.
    assert calc_rules.review_effective_end_date(review) == date(2026, 5, 31)


def test_review_vigencia_zero_after_anniversary():
    review = {
        "cenario_tipo": "melhoria",
        "data_inicio_vigencia": "2025-06-01",
        "data_implantacao": "2025-06-01",
    }
    # Mês anterior ao aniversário conta integralmente.
    assert calc_rules.review_vigencia_fraction_in_month(review, date(2026, 5, 1)) == 1.0
    # A partir do mês do aniversário deixa de contar.
    assert calc_rules.review_vigencia_fraction_in_month(review, date(2026, 6, 1)) == 0.0


def test_review_effective_end_uses_earliest_of_fim_and_anniversary():
    review = {
        "cenario_tipo": "melhoria",
        "data_inicio_vigencia": "2025-06-01",
        "data_implantacao": "2025-06-01",
        "data_fim_vigencia": "2025-12-31",
    }
    # Supersessão antes do aniversário: fim de vigência prevalece.
    assert calc_rules.review_effective_end_date(review) == date(2025, 12, 31)


def test_baseline_review_has_no_validity_cap():
    review = {
        "cenario_tipo": "baseline",
        "data_inicio_vigencia": "2025-06-01",
        "data_implantacao": "2025-06-01",
    }
    assert calc_rules.review_validity_end_date(review) is None
    assert calc_rules.review_effective_end_date(review) is None


def test_hours_saved_proc0020_scenario():
    baseline = {"volume_mensal": 336, "tempo_medio_execucao_min": 20}
    melhoria = {"volume_mensal": 336, "tempo_medio_execucao_min": 0.5}
    review = {
        "cenario_tipo": "melhoria",
        "data_inicio_vigencia": "2025-11-05",
        "data_implantacao": "2025-11-05",
    }
    hours = calc_rules.hours_saved_in_competencia_month(
        baseline, melhoria, review, date(2026, 6, 1)
    )
    assert hours == 109.2


def test_period_filter_hours_not_double_prorated():
    row = {
        "competencia": "2026-06",
        "economia_bruta": 2398.17,
        "economia_liquida_mes": 2241.07,
        "investimento_unico_mes": 0,
        "custo_recorrente_mes": 0,
        "custo_recursos_compartilhados_mes": 157.1,
        "horas_economizadas_mes": 109.2,
    }
    prorated = calc_rules.prorate_dashboard_row_for_period(
        row, start_date="2026-06-01", end_date="2026-06-04"
    )
    assert prorated is not None
    assert round(prorated["horas_economizadas_mes"], 2) == 14.56

    daily = calc_rules.daily_averages_from_period_totals(
        {"economia_bruta": prorated["economia_bruta"], "horas_economizadas_mes": prorated["horas_economizadas_mes"]},
        {"2026-06"},
        start_date="2026-06-01",
        end_date="2026-06-04",
    )
    assert daily["horas_diaria"] == 3.64


def test_aggregate_period_from_rows():
    rows = [
        {
            "competencia": "2026-06",
            "economia_bruta": 1000.0,
            "economia_liquida_mes": 900.0,
            "investimento_unico_mes": 0,
            "custo_recorrente_mes": 0,
            "custo_recursos_compartilhados_mes": 100.0,
            "horas_economizadas_mes": 109.2,
        }
    ]
    totals = calc_rules.aggregate_period_from_rows(
        rows, start_date="2026-06-01", end_date="2026-06-04"
    )
    assert round(totals["horas_economizadas_mes"], 2) == 14.56


def test_clamp_period_to_elapsed_days_limits_end_to_today():
    start, end, entirely_future = calc_rules.clamp_period_to_elapsed_days(
        "2026-07-01",
        "2026-07-31",
        today=date(2026, 7, 7),
    )

    assert entirely_future is False
    assert start == "2026-07-01"
    assert end == "2026-07-07"


def test_clamp_period_to_elapsed_days_marks_entirely_future():
    start, end, entirely_future = calc_rules.clamp_period_to_elapsed_days(
        "2026-08-01",
        "2026-08-31",
        today=date(2026, 7, 7),
    )

    assert entirely_future is True
    assert start == "2026-08-01"
    assert end == "2026-08-31"


def test_build_daily_evolucao_series_varies_by_vigencia_start():
    """Revisão que começa no meio do mês só contribui a partir desse dia."""
    reviews = {
        "r-early": {
            "revisao_id": "r-early",
            "cenario_tipo": "melhoria",
            "data_inicio_vigencia": "2026-04-01",
            "data_implantacao": "2026-04-01",
        },
        "r-late": {
            "revisao_id": "r-late",
            "cenario_tipo": "automacao",
            "data_inicio_vigencia": "2026-04-16",
            "data_implantacao": "2026-04-16",
        },
    }
    rows = [
        {
            "revisao_id": "r-early",
            "competencia": "2026-04",
            "economia_bruta": 300.0,
            "economia_liquida_mes": 300.0,
            "investimento_unico_mes": 0.0,
            "custo_recorrente_mes": 0.0,
            "custo_recursos_compartilhados_mes": 0.0,
            "investimento_total_mes": 0.0,
            "horas_economizadas_mes": 30.0,
        },
        {
            "revisao_id": "r-late",
            "competencia": "2026-04",
            "economia_bruta": 150.0,
            "economia_liquida_mes": 80.0,
            "investimento_unico_mes": 70.0,
            "custo_recorrente_mes": 0.0,
            "custo_recursos_compartilhados_mes": 0.0,
            "investimento_total_mes": 70.0,
            "horas_economizadas_mes": 15.0,
        },
    ]

    items = calc_rules.build_daily_evolucao_series(
        rows,
        start_date="2026-04-01",
        end_date="2026-04-30",
        reviews_by_id=reviews,
    )

    assert len(items) == 30
    by_day = {item["competencia"]: item for item in items}

    day_01 = by_day["2026-04-01"]
    day_15 = by_day["2026-04-15"]
    day_16 = by_day["2026-04-16"]
    day_30 = by_day["2026-04-30"]

    # Até 15/04 só r-early (300/30 = 10)
    assert day_01["economia_bruta"] == 10.0
    assert day_15["economia_bruta"] == 10.0
    # A partir de 16/04: early 10 + late 150/15 = 10 → 20
    assert day_16["economia_bruta"] == 20.0
    assert day_30["economia_bruta"] == 20.0
    # Único do late no 1º dia ativo
    assert day_16["investimento_unico_mes"] == 70.0
    assert day_01["investimento_unico_mes"] == 0.0
    assert day_01["economia_bruta"] != day_16["economia_bruta"]
