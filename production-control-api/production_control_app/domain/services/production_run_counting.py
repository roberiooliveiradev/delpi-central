"""Fórmula MES de peças a partir de âncora absoluta + epoch do Pulse."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


@dataclass(frozen=True)
class SegmentPiecesResult:
    pieces: int
    epoch_changed: bool


def target_pieces_from_quantity(
    quantity: object,
    pieces_conversion_factor: object,
) -> int | None:
    try:
        normalized = Decimal(str(quantity)) * Decimal(str(pieces_conversion_factor))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if not normalized.is_finite() or normalized <= 0:
        return None
    target = int(normalized.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return target if target > 0 else None


def pieces_from_anchor(
    *,
    current_counter: int,
    current_epoch: int,
    anchor_counter: int,
    anchor_epoch: int,
) -> SegmentPiecesResult:
    """Contagem exata do segmento aberto.

    Se o epoch mudou (reset/set/restore), o consumidor deve fechar o segmento
    com o último ``pieces`` conhecido sob o epoch antigo e abrir novo com a
    âncora atual — esta função só sinaliza ``epoch_changed``.
    """
    if int(current_epoch) != int(anchor_epoch):
        return SegmentPiecesResult(pieces=0, epoch_changed=True)
    delta = int(current_counter) - int(anchor_counter)
    return SegmentPiecesResult(pieces=max(0, delta), epoch_changed=False)


def sum_segment_pieces(closed_pieces: list[int], open_pieces: int) -> int:
    total = sum(max(0, int(p)) for p in closed_pieces)
    return total + max(0, int(open_pieces))


@dataclass(frozen=True)
class CountChange:
    """Mudança real de contagem observada em um Production Run.

    delta_pieces é sempre != 0: positivo = produção, negativo = correção.
    Os valores são peças físicas do domínio MES (não pulsos crus).
    """

    pieces_total: int
    delta_pieces: int
    event_type: str


def build_count_change(
    *,
    previous_total: int,
    observed_total: int,
) -> CountChange | None:
    """Única regra de interpretação de mudança de contagem.

    Retorna None quando não há mudança real — nesse caso nenhum evento
    deve ser persistido (polling idle não é fato). Saltos são agregados:
    100→105 produz um único evento production com delta_pieces=5.
    """
    prev = max(0, int(previous_total or 0))
    observed = max(0, int(observed_total or 0))
    delta = observed - prev
    if delta == 0:
        return None
    return CountChange(
        pieces_total=observed,
        delta_pieces=delta,
        event_type="production" if delta > 0 else "correction",
    )
