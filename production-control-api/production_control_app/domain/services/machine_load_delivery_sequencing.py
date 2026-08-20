"""Otimização da fila pela data de entrega do PA.

Regra de negócio: o carga máquina do TOTVS às vezes deixa material de entrega
distante à frente de material vencendo. Otimizar resequencia a fila de **todos**
os centros de trabalho pela entrega efetiva da OP, sem ultrapassar operação já
iniciada e preservando a ordem atual entre operações da mesma data — o ajuste
manual do PCP dentro do dia continua valendo.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from production_control_app.domain.services.machine_load_delivery_window import (
    missing_due_date_count,
    operation_due_date,
)
from production_control_app.domain.services.machine_load_queue_slots import (
    OperationKey,
    free_positions,
    pinned_positions,
    reorder_free_slots,
    slots_by_work_center,
    started_predicate,
)


@dataclass(frozen=True)
class DeliverySequencing:
    operations: list[dict[str, Any]]
    #: Só os centros cuja ordem realmente mudou.
    work_centers: list[str]
    moved_operation_count: int
    kept_ahead_count: int
    missing_due_date_count: int


def optimize_by_delivery_date(
    operations: list[dict[str, Any]],
    *,
    started_keys: set[OperationKey] | None = None,
) -> DeliverySequencing:
    """Ordena a fila de cada centro pela entrega do PA.

    ``started_keys`` traz o status ao vivo (HZA) por ``(production_order, operation_code)``
    quando o snapshot congelado não carrega os campos de apontamento.
    """
    started_here = started_predicate(started_keys)

    next_ops = list(operations)
    centers: list[str] = []
    moved_count = 0
    kept_ahead = 0

    for center, slots in slots_by_work_center(operations).items():
        center_ops = [operations[index] for index in slots]
        pinned = pinned_positions(center_ops, is_pinned=started_here)
        free = free_positions(center_ops, pinned=pinned)
        if not free:
            continue

        def sort_key(position: int, ops: list[dict[str, Any]] = center_ops) -> tuple[int, str]:
            # Sem entrega vai para o fim; `sorted` é estável, então o empate
            # preserva a ordem atual da fila.
            due = operation_due_date(ops[position])
            return (0, due) if due else (1, "")

        desired = sorted(free, key=sort_key)
        if desired == free:
            continue

        reordered = reorder_free_slots(
            center_ops,
            pinned=pinned,
            desired_free_order=desired,
        )
        for slot, item in zip(slots, reordered, strict=True):
            next_ops[slot] = item

        centers.append(center)
        moved_count += sum(
            1 for before, after in zip(free, desired, strict=True) if before != after
        )
        # Tudo antes da primeira posição livre é operação já iniciada.
        kept_ahead += free[0]

    return DeliverySequencing(
        operations=next_ops,
        work_centers=centers,
        moved_operation_count=moved_count,
        kept_ahead_count=kept_ahead,
        missing_due_date_count=missing_due_date_count(operations),
    )
