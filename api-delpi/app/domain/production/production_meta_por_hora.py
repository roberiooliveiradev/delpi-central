"""Meta de produção por hora (ritmo padrão) — eficiência fabril.

Fonte preferencial: snapshot da OP em ``SHY010`` (não o SG2 atual, que muda
no cadastro ao longo do tempo).

Campos SHY relevantes:

- ``HY_TEMPAD`` = horas padrão **por unidade** congeladas na OP (estável).
- ``HY_QUANT`` = quantidade associada ao tempo corrente (muda com apontamento
  parcial / saldo).
- ``HY_TEMPOM`` = ``HY_TEMPAD × HY_QUANT`` (muda junto com ``HY_QUANT``).

Por isso **não** usar ``QTD_TOTAL_OP / HY_TEMPOM``: o denominador encolhe com
apontamentos parciais e a meta oscila (ex.: 0,256 / 0,304 / 0,200 no mesmo PA).

Meta/hora (unidades/h), sem setup:

1. ``1 / HY_TEMPAD`` (ritmo unitário do snapshot da OP)
2. ``HY_QUANT / HY_TEMPOM`` se ``TEMPAD`` ausente (equivalente quando
   ``TEMPOM = TEMPAD × QUANT``)
3. ``1 / G2_TEMPAD`` só se SHY não tiver fator (cadastro atual — último recurso)
"""

from __future__ import annotations


def compute_meta_por_hora(
    *,
    hy_tempad: float | int | None = None,
    hy_tempom: float | int | None = None,
    hy_quant: float | int | None = None,
    g2_tempad: float | int | None = None,
    qtd_total_op: float | int | None = None,
) -> float | None:
    """Retorna ritmo padrão (unidades/hora) ou None se não houver fator válido.

    ``qtd_total_op`` é ignorado na fórmula canônica (mantido na assinatura só
    para compatibilidade de chamadas antigas de teste).
    """
    del qtd_total_op  # não usar — varia / não acompanha HY_TEMPOM parcial

    tempad = _positive_float(hy_tempad)
    if tempad is not None:
        return round(1.0 / tempad, 6)

    tempom = _positive_float(hy_tempom)
    quant = _positive_float(hy_quant)
    if tempom is not None and quant is not None:
        return round(quant / tempom, 6)

    g2 = _positive_float(g2_tempad)
    if g2 is not None:
        return round(1.0 / g2, 6)
    return None


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
