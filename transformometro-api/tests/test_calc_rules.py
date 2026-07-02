"""Testes das regras centralizadas (tm_app/domain/calc_rules.py)."""

from datetime import date

from tm_app.domain import calc_rules


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
