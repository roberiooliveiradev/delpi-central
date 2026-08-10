"""Regressão — tempo previsto / eficiência estáveis via HY_TEMPAD × qtd."""

from app.domain.production.production_tempo_previsto import (
    compute_eficiencia_percentual,
    compute_tempo_previsto_horas,
    resolve_unit_hours,
)


def test_unit_hours_prefers_hy_tempad() -> None:
    assert resolve_unit_hours(hy_tempad=0.00091, hy_tempom=0.5, hy_quant=100) == 0.00091


def test_tempo_previsto_stable_when_hy_quant_shrinks() -> None:
    """Mesmo HY_TEMPAD e qtd apontada → mesmo previsto, independente de HY_QUANT."""
    common = dict(qtd_apontada=100.0, hy_tempad=0.00091, setup_horas=0.0)
    a = compute_tempo_previsto_horas(**common, hy_tempom=0.91, hy_quant=1000.0)
    b = compute_tempo_previsto_horas(**common, hy_tempom=0.091, hy_quant=100.0)
    assert a == b
    assert a == round(0.00091 * 100.0, 6)


def test_eficiencia_matches_rate_over_meta() -> None:
    """Com meta = 1/TEMPAD, % ≈ (qtd/real) / meta × 100."""
    tempad = 1.0 / 1099.0
    qtd = 500.0
    real = 0.5  # 1000 unid/h
    previsto = compute_tempo_previsto_horas(qtd_apontada=qtd, hy_tempad=tempad)
    eff = compute_eficiencia_percentual(tempo_previsto_horas=previsto, tempo_real_horas=real)
    rate = qtd / real
    meta = 1.0 / tempad
    expected = round(rate / meta * 100.0, 2)
    assert eff == expected
    assert eff is not None and eff > 90  # ~91% — não ~29%


def test_partial_hy_tempom_must_not_crush_efficiency() -> None:
    """Anti-padrão da view: TEMPOM parcial × (qtd/C2) derruba o %."""
    tempad = 0.001
    qtd = 100.0
    real = 0.1
    stable = compute_tempo_previsto_horas(qtd_apontada=qtd, hy_tempad=tempad)
    # Simula view com HY_QUANT encolhido (TEMPOM = TEMPAD×QUANT residual)
    broken_factor = 0.001 * 30.0  # HY_TEMPOM residual
    c2_quant = 100.0
    broken_previsto = broken_factor * (qtd / c2_quant)
    stable_eff = compute_eficiencia_percentual(
        tempo_previsto_horas=stable, tempo_real_horas=real
    )
    broken_eff = compute_eficiencia_percentual(
        tempo_previsto_horas=broken_previsto, tempo_real_horas=real
    )
    assert stable_eff == 100.0
    assert broken_eff is not None and broken_eff < 40
