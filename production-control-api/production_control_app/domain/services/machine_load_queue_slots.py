"""Mecânica de slots da fila de um centro de trabalho.

Toda reordenação da carga máquina (priorizar conjunto, otimizar por entrega)
obedece à mesma regra: operação **já iniciada** — em produção agora ou com
apontamento no histórico — fica travada onde está; só as posições livres são
permutadas. Este módulo é a fonte única dessa mecânica.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

# Status vindos da HZA010: a operação já foi tocada na fábrica.
STARTED_PRODUCTION_STATUSES = frozenset({"in_progress", "started"})

OperationKey = tuple[str, str]


def is_started_operation(item: dict[str, Any]) -> bool:
    """True se a operação já foi iniciada (em produção agora ou já apontada)."""
    if item.get("is_in_production"):
        return True
    status = str(item.get("production_status") or "").strip().lower()
    return status in STARTED_PRODUCTION_STATUSES


def operation_identity(item: dict[str, Any]) -> OperationKey:
    return (
        str(item.get("production_order") or "").strip(),
        str(item.get("operation_code") or "").strip(),
    )


def started_predicate(
    started_keys: set[OperationKey] | None = None,
) -> Callable[[dict[str, Any]], bool]:
    """Predicado de «já iniciada» combinando o snapshot com o status vivo (HZA).

    ``started_keys`` cobre o caso em que o payload congelado não carrega os
    campos de apontamento.
    """
    started = started_keys or set()

    def started_here(item: dict[str, Any]) -> bool:
        return is_started_operation(item) or operation_identity(item) in started

    return started_here


def slots_by_work_center(operations: list[dict[str, Any]]) -> dict[str, list[int]]:
    """Índices de cada operação na lista global, agrupados por centro de trabalho."""
    slots: dict[str, list[int]] = {}
    for index, item in enumerate(operations):
        center = str(item.get("work_center") or "").strip()
        if not center:
            continue
        slots.setdefault(center, []).append(index)
    return slots


def pinned_positions(
    center_ops: list[dict[str, Any]],
    *,
    is_pinned: Callable[[dict[str, Any]], bool],
) -> set[int]:
    return {position for position, item in enumerate(center_ops) if is_pinned(item)}


def free_positions(center_ops: list[dict[str, Any]], *, pinned: set[int]) -> list[int]:
    return [position for position in range(len(center_ops)) if position not in pinned]


def reorder_free_slots(
    center_ops: list[dict[str, Any]],
    *,
    pinned: set[int],
    desired_free_order: list[int],
) -> list[dict[str, Any]]:
    """Reescreve a fila do centro mantendo as posições travadas.

    ``desired_free_order`` é a permutação das posições livres na ordem em que
    devem ocupar os buracos deixados pelas travadas.
    """
    pending = iter(desired_free_order)
    return [
        center_ops[position] if position in pinned else center_ops[next(pending)]
        for position in range(len(center_ops))
    ]
