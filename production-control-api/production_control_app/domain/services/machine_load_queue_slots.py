"""Mecânica de slots da fila de um centro de trabalho.

Toda reordenação da carga máquina (priorizar conjunto, otimizar por entrega,
reordenar, atualizar a partir do TOTVS) obedece à mesma regra: operação com
**run aberto no cockpit do operador** fica travada onde está; só as posições
livres são permutadas. Este módulo é a fonte única dessa mecânica.

A proteção depende exclusivamente das chaves oficiais fornecidas pela aplicação
(runs locais do MES) — nunca de apontamentos HZA nem de flags persistidas no
snapshot congelado (``production_status``, ``is_in_production``).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

OperationKey = tuple[str, str]

# Identidade funcional da operação protegida: centro de trabalho + OP + operação.
# O centro entra na chave porque a mesma OP/operação pode existir em outro posto
# sem run aberto — proteger por par OP+operação travaria a posição errada.
ProtectedOperationKey = tuple[str, str, str]


def _norm(value: Any) -> str:
    return str(value or "").strip().upper()


def operation_identity(item: dict[str, Any]) -> OperationKey:
    return (
        str(item.get("production_order") or "").strip(),
        str(item.get("operation_code") or "").strip(),
    )


def protected_operation_key(item: dict[str, Any]) -> ProtectedOperationKey:
    """Chave canônica (centro, OP, operação) — vale para item da fila e run."""
    return (
        _norm(item.get("work_center")),
        _norm(item.get("production_order")),
        str(item.get("operation_code") or "").strip(),
    )


def protected_predicate(
    protected_keys: set[ProtectedOperationKey] | None = None,
) -> Callable[[dict[str, Any]], bool]:
    """Predicado de «protegida» olhando só as chaves oficiais de runs abertos.

    Sem run aberto a posição é livre — mesmo que o snapshot congelado carregue
    ``is_in_production``/``production_status`` herdados de apontamentos HZA.
    """
    protected = protected_keys or set()

    def is_protected(item: dict[str, Any]) -> bool:
        return protected_operation_key(item) in protected

    return is_protected


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


def carry_pinned_positions(
    previous_operations: list[dict[str, Any]],
    next_operations: list[dict[str, Any]],
    *,
    is_pinned: Callable[[dict[str, Any]], bool],
) -> list[dict[str, Any]]:
    """Reposiciona operações travadas no slot que ocupavam antes do refresh.

    O «Atualizar» reconstrói a fila na ordem cronológica do TOTVS e descarta a
    ordenação manual — mas uma operação com run aberto conserva o índice que
    ocupava dentro do seu centro de trabalho na fila anterior. Sem este reparo
    ela cairia na posição cronológica do ERP e, por estar travada para qualquer
    reordenação, ficaria congelada no lugar errado.

    Ambas as listas chegam já filtradas (só operações visíveis). Operação
    protegida que só existe na fila nova entra na ordem em que veio; índice
    anterior além do fim da fila nova cai na última posição; colisões entre
    protegidas resolvem para a frente, preservando a ordem relativa anterior.
    """
    previous_slots = slots_by_work_center(previous_operations)
    next_slots = slots_by_work_center(next_operations)
    merged = list(next_operations)
    for center, indices in next_slots.items():
        previous_center = [
            previous_operations[index] for index in previous_slots.get(center, [])
        ]
        next_center = [next_operations[index] for index in indices]
        # Índice relativo ao centro — a identidade OP+operação é única por CT,
        # mesmo contrato de reorder_sequence/ordered_keys.
        pinned_index = {
            operation_identity(item): position
            for position, item in enumerate(previous_center)
            if is_pinned(item)
        }
        if not pinned_index:
            continue
        size = len(next_center)
        pinned_slots: dict[int, dict[str, Any]] = {}
        pending: list[dict[str, Any]] = []
        for item in next_center:
            target = pinned_index.get(operation_identity(item))
            if target is None:
                pending.append(item)
                continue
            position = min(target, size - 1)
            while position in pinned_slots:
                position += 1
            pinned_slots[position] = item
        free = iter(pending)
        rebuilt = [
            pinned_slots[position] if position in pinned_slots else next(free)
            for position in range(size)
        ]
        for slot, item in zip(indices, rebuilt, strict=True):
            merged[slot] = item
    return merged
