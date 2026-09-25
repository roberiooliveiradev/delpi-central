"""Fórmula MES de peças a partir de âncora absoluta + epoch do Pulse."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SegmentPiecesResult:
    pieces: int
    epoch_changed: bool


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
