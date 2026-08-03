"""Regressão — Meta/hora estável via SHY.HY_TEMPAD (não HY_TEMPOM parcial)."""

from app.domain.production.production_meta_por_hora import compute_meta_por_hora


def test_meta_por_hora_from_hy_tempad_stable_across_partial_appointments() -> None:
    """HY_TEMPOM muda com HY_QUANT; HY_TEMPAD permanece — meta = 1/TEMPAD."""
    # Dados reais PA 90262005 op 04 filial 02 (jul/2026)
    assert (
        compute_meta_por_hora(hy_tempad=5.0, hy_tempom=3.9, hy_quant=0.78) == 0.2
    )
    assert (
        compute_meta_por_hora(hy_tempad=5.0, hy_tempom=2.3, hy_quant=0.46) == 0.2
    )
    assert (
        compute_meta_por_hora(hy_tempad=5.0, hy_tempom=4.25, hy_quant=0.85) == 0.2
    )
    assert (
        compute_meta_por_hora(hy_tempad=5.0, hy_tempom=1.95, hy_quant=0.39) == 0.2
    )


def test_meta_por_hora_hy_quant_over_tempom_equals_tempad_rate() -> None:
    assert compute_meta_por_hora(hy_tempad=None, hy_tempom=3.9, hy_quant=0.78) == 0.2
    assert compute_meta_por_hora(hy_tempad=None, hy_tempom=2.3, hy_quant=0.46) == 0.2


def test_meta_por_hora_old_qtd_over_tempom_diverged() -> None:
    """Anti-padrão: C2_QUANT / HY_TEMPOM com TEMPOM parcial."""
    assert round(1.0 / 3.9, 6) == 0.25641
    assert round(0.7 / 2.3, 6) == 0.304348
    assert compute_meta_por_hora(hy_tempad=5.0, hy_tempom=3.9, hy_quant=0.78) == 0.2


def test_meta_por_hora_falls_back_to_g2_when_shy_missing() -> None:
    assert compute_meta_por_hora(g2_tempad=5.0) == 0.2
    assert compute_meta_por_hora() is None


def test_meta_por_hora_prefers_hy_tempad_over_g2() -> None:
    # Snapshot da OP (4 h/MI) prevalece sobre cadastro atual (5 h/MI)
    assert (
        compute_meta_por_hora(hy_tempad=4.0, g2_tempad=5.0) == 0.25
    )
