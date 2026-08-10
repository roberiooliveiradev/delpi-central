"""Tempo previsto e eficiência por apontamento — eficiência fabril / OEE.

Alinhado a ``production_meta_por_hora``: o ritmo unitário estável é ``HY_TEMPAD``
(h/unidade no snapshot SHY da OP).

A view ``vw_Apontamentos_Eficiencia`` ainda usa::

    SETUP + HY_TEMPOM × (QTD / C2_QUANT)

``HY_TEMPOM = HY_TEMPAD × HY_QUANT`` e ``HY_QUANT`` encolhe com apontamento
parcial → o previsto (e o %) caem artificialmente mesmo com Meta/hora correta
(``1 / HY_TEMPAD``).

Fórmula canônica (sem depender de ``HY_QUANT`` / ``C2_QUANT``)::

    tempo_previsto = setup + HY_TEMPAD × qtd_apontada
    eficiencia_%   = tempo_previsto / tempo_real × 100

Fallback: ``HY_TEMPOM / HY_QUANT`` (equivale a TEMPAD quando a proporção vale);
por fim ``G2_TEMPAD``.
"""

from __future__ import annotations


def resolve_unit_hours(
    *,
    hy_tempad: float | int | None = None,
    hy_tempom: float | int | None = None,
    hy_quant: float | int | None = None,
    g2_tempad: float | int | None = None,
) -> float | None:
    """Horas padrão por unidade (mesmo ritmo da meta/hora)."""
    tempad = _positive_float(hy_tempad)
    if tempad is not None:
        return tempad

    tempom = _positive_float(hy_tempom)
    quant = _positive_float(hy_quant)
    if tempom is not None and quant is not None:
        return tempom / quant

    return _positive_float(g2_tempad)


def compute_tempo_previsto_horas(
    *,
    qtd_apontada: float | int | None,
    hy_tempad: float | int | None = None,
    hy_tempom: float | int | None = None,
    hy_quant: float | int | None = None,
    g2_tempad: float | int | None = None,
    setup_horas: float | int | None = None,
) -> float | None:
    """Tempo previsto do apontamento (horas), estável sob OP parcial."""
    qty = _positive_float(qtd_apontada)
    unit = resolve_unit_hours(
        hy_tempad=hy_tempad,
        hy_tempom=hy_tempom,
        hy_quant=hy_quant,
        g2_tempad=g2_tempad,
    )
    if qty is None or unit is None:
        return None
    setup = _non_negative_float(setup_horas) or 0.0
    return round(setup + unit * qty, 6)


def compute_eficiencia_percentual(
    *,
    tempo_previsto_horas: float | int | None,
    tempo_real_horas: float | int | None,
) -> float | None:
    previsto = _positive_float(tempo_previsto_horas)
    real = _positive_float(tempo_real_horas)
    if previsto is None or real is None:
        return None
    return round(previsto * 100.0 / real, 2)


def _positive_float(value: float | int | None) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number <= 0:
        return None
    return number


def _non_negative_float(value: float | int | None) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number < 0:
        return None
    return number
