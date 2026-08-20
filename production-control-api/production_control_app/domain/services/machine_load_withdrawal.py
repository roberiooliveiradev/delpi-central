"""Conjuntos retirados da programação.

Regra de negócio: o PCP pode tirar um conjunto (C2_NUM) da programação. As OPs
somem da fila de todos os centros e do cockpit do operador, mas **continuam no
snapshot na posição original** — devolver à fila é só remover a chave da lista.

A fonte de verdade é ``withdrawn_conjuntos`` no ``payload_json``; a marca por
operação é derivada na leitura, nunca gravada na própria operação.
"""

from __future__ import annotations

from typing import Any

from production_control_app.domain.services.production_order_key import (
    conjunto_key_from_order,
    normalize_order_code,
    order_belongs_to_conjunto,
)

WITHDRAWN_CONJUNTOS_KEY = "withdrawn_conjuntos"


def withdrawn_entries(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Lista de conjuntos retirados gravada no snapshot (sempre uma cópia)."""
    raw = payload.get(WITHDRAWN_CONJUNTOS_KEY)
    if not isinstance(raw, list):
        return []
    return [dict(item) for item in raw if isinstance(item, dict) and item.get("order_number")]


def withdrawn_order_numbers(payload: dict[str, Any]) -> set[str]:
    return {
        key
        for item in withdrawn_entries(payload)
        if (key := normalize_order_code(item.get("order_number")))
    }


def is_withdrawn(operation: dict[str, Any], keys: set[str]) -> bool:
    if not keys:
        return False
    order = operation.get("production_order")
    return any(order_belongs_to_conjunto(order, key) for key in keys)


def visible_operations(
    operations: list[dict[str, Any]],
    keys: set[str],
) -> list[dict[str, Any]]:
    """Operações que continuam na programação."""
    if not keys:
        return list(operations)
    return [item for item in operations if not is_withdrawn(item, keys)]


def withdrawn_operations(
    operations: list[dict[str, Any]],
    keys: set[str],
) -> list[dict[str, Any]]:
    if not keys:
        return []
    return [item for item in operations if is_withdrawn(item, keys)]


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
