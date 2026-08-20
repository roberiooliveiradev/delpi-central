"""Priorização de conjunto na fila dos centros de trabalho.

Regra de negócio: priorizar um conjunto (C2_NUM) leva **todas** as OPs desse
conjunto para o topo da fila de cada centro onde elas aparecem. Operações já
iniciadas (em produção agora ou com apontamento no histórico) não são
ultrapassadas — mantêm a posição atual e o conjunto entra logo depois delas.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from production_control_app.domain.services.machine_load_queue_slots import (
    OperationKey,
    free_positions,
    pinned_positions,
    reorder_free_slots,
    slots_by_work_center,
    started_predicate,
)
from production_control_app.domain.services.production_order_key import (
    order_belongs_to_conjunto,
)


@dataclass(frozen=True)
class ConjuntoPrioritization:
    operations: list[dict[str, Any]]
    work_centers: list[str]
    prioritized_operation_count: int
    kept_ahead_count: int


def prioritize_conjunto(
    operations: list[dict[str, Any]],
    *,
    conjunto_key: str,
    started_keys: set[OperationKey] | None = None,
) -> ConjuntoPrioritization:
    """Reordena a fila de cada centro que tem OPs do conjunto.

    ``started_keys`` traz o status ao vivo (HZA) por ``(production_order, operation_code)``
    quando o snapshot congelado não carrega os campos de apontamento.
    """
    started_here = started_predicate(started_keys)

    next_ops = list(operations)
    centers: list[str] = []
    prioritized_count = 0
    kept_ahead = 0

    for center, slots in slots_by_work_center(operations).items():
        center_ops = [operations[index] for index in slots]
        target_positions = {
            position
            for position, item in enumerate(center_ops)
            if order_belongs_to_conjunto(item.get("production_order"), conjunto_key)
        }
        if not target_positions:
            continue

        pinned = pinned_positions(center_ops, is_pinned=started_here)
        free = free_positions(center_ops, pinned=pinned)
        movable_targets = [position for position in free if position in target_positions]
        if not movable_targets:
            continue

        movable_rest = [position for position in free if position not in target_positions]
        reordered = reorder_free_slots(
            center_ops,
            pinned=pinned,
            desired_free_order=movable_targets + movable_rest,
        )

        for slot, item in zip(slots, reordered, strict=True):
            next_ops[slot] = item

        centers.append(center)
        prioritized_count += len(movable_targets)
        # O conjunto ocupa a primeira posição livre; tudo antes dela é operação já iniciada.
        kept_ahead += free[0]

    return ConjuntoPrioritization(
        operations=next_ops,
        work_centers=centers,
        prioritized_operation_count=prioritized_count,
        kept_ahead_count=kept_ahead,
    )
