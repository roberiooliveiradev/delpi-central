"""Conjuntos e operações retirados da programação.

Regra de negócio: o PCP pode tirar um conjunto inteiro (C2_NUM) ou operações
específicas (CT + OP + operação) da programação. Os itens somem da fila e do
cockpit do operador, mas **continuam no snapshot na posição original** —
devolver à fila é só remover a marca correspondente.

A fonte de verdade é o par de listas no ``payload_json``:

- ``withdrawn_conjuntos``: retirada por conjunto (semântica preservada);
- ``withdrawn_operations``: retirada por operação individual.

As marcas se somam: retirada individual + conjunto retirado escondem a
operação; restaurar uma não revela o que a outra ainda esconde. Nenhuma marca
é gravada na própria operação — a visibilidade é derivada na leitura.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from production_control_app.domain.services.production_order_key import (
    conjunto_key_from_order,
    normalize_order_code,
    order_belongs_to_conjunto,
)

WITHDRAWN_CONJUNTOS_KEY = "withdrawn_conjuntos"
WITHDRAWN_OPERATIONS_KEY = "withdrawn_operations"


def _norm_center(value: Any) -> str:
    return str(value or "").strip().upper()


@dataclass(frozen=True)
class WithdrawnMarks:
    """Marcas de retirada de um payload — única entrada para visibilidade.

    ``conjuntos``: chaves C2_NUM retiradas. ``operations``: tuplas
    (centro, OP, operação) retiradas individualmente. Toda consulta da fila
    deve usar ``withdrawn_marks(payload)`` — nunca metade do estado.
    """

    conjuntos: frozenset[str]
    operations: frozenset[tuple[str, str, str]]


def withdrawn_entries(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Lista de conjuntos retirados gravada no snapshot (sempre uma cópia)."""
    raw = payload.get(WITHDRAWN_CONJUNTOS_KEY)
    if not isinstance(raw, list):
        return []
    return [dict(item) for item in raw if isinstance(item, dict) and item.get("order_number")]


def withdrawn_operation_entries(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Operações retiradas individualmente (sempre uma cópia)."""
    raw = payload.get(WITHDRAWN_OPERATIONS_KEY)
    if not isinstance(raw, list):
        return []
    return [
        dict(item)
        for item in raw
        if isinstance(item, dict)
        and item.get("production_order")
        and item.get("operation_code")
        and item.get("work_center")
    ]


def withdrawn_order_numbers(payload: dict[str, Any]) -> set[str]:
    return {
        key
        for item in withdrawn_entries(payload)
        if (key := normalize_order_code(item.get("order_number")))
    }


def withdrawn_marks(payload: dict[str, Any]) -> WithdrawnMarks:
    """Estado completo de retiradas — conjuntos + operações individuais."""
    op_keys = frozenset(
        (
            _norm_center(item.get("work_center")),
            normalize_order_code(item.get("production_order")),
            normalize_order_code(item.get("operation_code")),
        )
        for item in withdrawn_operation_entries(payload)
    )
    return WithdrawnMarks(
        conjuntos=frozenset(withdrawn_order_numbers(payload)),
        operations=op_keys,
    )


def _operation_withdrawn_key(item: dict[str, Any]) -> tuple[str, str, str]:
    return (
        _norm_center(item.get("work_center")),
        normalize_order_code(item.get("production_order")),
        normalize_order_code(item.get("operation_code")),
    )


def is_withdrawn(operation: dict[str, Any], marks: WithdrawnMarks) -> bool:
    """A operação está fora da programação por conjunto ou por marca própria.

    Exige ``WithdrawnMarks`` — quem consulta visibilidade nunca vê metade do
    estado (só conjuntos ou só operações).
    """
    if marks.operations and _operation_withdrawn_key(operation) in marks.operations:
        return True
    if not marks.conjuntos:
        return False
    order = operation.get("production_order")
    return any(order_belongs_to_conjunto(order, key) for key in marks.conjuntos)


def visible_operations(
    operations: list[dict[str, Any]],
    marks: WithdrawnMarks,
) -> list[dict[str, Any]]:
    """Operações que continuam na programação."""
    if not marks.conjuntos and not marks.operations:
        return list(operations)
    return [item for item in operations if not is_withdrawn(item, marks)]


def withdrawn_operations(
    operations: list[dict[str, Any]],
    marks: WithdrawnMarks,
) -> list[dict[str, Any]]:
    if not marks.conjuntos and not marks.operations:
        return []
    return [item for item in operations if is_withdrawn(item, marks)]


def build_withdrawn_operation_entry(
    item: dict[str, Any],
    *,
    withdrawn_at: str,
    withdrawn_by: str | None,
) -> dict[str, Any]:
    """Registro de retirada individual — identidade canônica + contexto de exibição."""
    return {
        "work_center": str(item.get("work_center") or "").strip(),
        "production_order": normalize_order_code(item.get("production_order")),
        "operation_code": normalize_order_code(item.get("operation_code")),
        "withdrawn_at": withdrawn_at,
        "withdrawn_by": withdrawn_by,
        "pa_product_code": item.get("pa_product_code") or None,
        "pa_due_date": str(item.get("pa_due_date") or "")[:10] or None,
    }


def withdraw_operation_entries(
    entries: list[dict[str, Any]],
    *,
    items: list[dict[str, Any]],
    withdrawn_at: str,
    withdrawn_by: str | None,
) -> tuple[list[dict[str, Any]], int]:
    """Marca operações como retiradas. Devolve (novas entradas, quantas mudaram)."""
    existing = {_operation_withdrawn_key(item) for item in entries}
    next_entries = list(entries)
    added = 0
    for item in items:
        if _operation_withdrawn_key(item) in existing:
            continue
        next_entries.append(
            build_withdrawn_operation_entry(
                item, withdrawn_at=withdrawn_at, withdrawn_by=withdrawn_by
            )
        )
        added += 1
    return next_entries, added


def restore_operation_entries(
    entries: list[dict[str, Any]],
    *,
    keys: list[tuple[str, str, str]],
) -> tuple[list[dict[str, Any]], int]:
    """Remove marcas de retirada individual. Devolve (novas entradas, removidas)."""
    wanted = {
        (_norm_center(center), normalize_order_code(order), normalize_order_code(op))
        for center, order, op in keys
    }
    kept = [
        item for item in entries if _operation_withdrawn_key(item) not in wanted
    ]
    return kept, len(entries) - len(kept)


def build_withdrawal_entry(
    *,
    order_number: str,
    operations: list[dict[str, Any]],
    withdrawn_at: str,
    withdrawn_by: str | None,
) -> dict[str, Any]:
    """Resumo do conjunto retirado, para a lista «Fora da programação»."""
    key = normalize_order_code(order_number)
    members = [
        item for item in operations if order_belongs_to_conjunto(item.get("production_order"), key)
    ]
    centers: list[str] = []
    for item in members:
        center = str(item.get("work_center") or "").strip()
        if center and center not in centers:
            centers.append(center)

    pa_code = next(
        (
            code
            for item in members
            if (code := str(item.get("pa_product_code") or "").strip())
        ),
        None,
    )
    due_dates = sorted(
        due
        for item in members
        if (due := str(item.get("pa_due_date") or "").strip()[:10])
    )
    return {
        "order_number": key,
        "withdrawn_at": withdrawn_at,
        "withdrawn_by": withdrawn_by,
        "operation_count": len(members),
        "work_centers": centers,
        "pa_product_code": pa_code,
        "pa_due_date": due_dates[0] if due_dates else None,
    }


def withdraw_conjunto(
    entries: list[dict[str, Any]],
    *,
    order_number: str,
    operations: list[dict[str, Any]],
    withdrawn_at: str,
    withdrawn_by: str | None,
) -> tuple[list[dict[str, Any]], bool]:
    """Adiciona o conjunto à lista de retirados. O bool diz se houve mudança."""
    key = conjunto_key_from_order(order_number)
    if not key:
        return list(entries), False
    if any(normalize_order_code(item.get("order_number")) == key for item in entries):
        return list(entries), False

    entry = build_withdrawal_entry(
        order_number=key,
        operations=operations,
        withdrawn_at=withdrawn_at,
        withdrawn_by=withdrawn_by,
    )
    return [*entries, entry], True


def restore_conjunto(
    entries: list[dict[str, Any]],
    *,
    order_number: str,
) -> tuple[list[dict[str, Any]], bool]:
    """Remove o conjunto da lista de retirados. O bool diz se havia algo para devolver."""
    key = conjunto_key_from_order(order_number)
    if not key:
        return list(entries), False
    remaining = [
        item for item in entries if normalize_order_code(item.get("order_number")) != key
    ]
    return remaining, len(remaining) != len(entries)
