"""Transferência de uma operação para outro centro de trabalho.

Regra de negócio: o PCP pode mover **uma** operação (OP + operação) para a fila de
outro centro. A operação entra no fim da fila do destino — de lá o analista
reordena ou prioriza como qualquer outra.

A decisão é local do Portal PCP: o snapshot é reescrito, e a lista
``transferred_operations`` no ``payload_json`` guarda o histórico para que o
«Atualizar» do TOTVS reaplique as transferências em cima da fila nova.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from production_control_app.domain.services.production_order_key import normalize_order_code

TRANSFERRED_OPERATIONS_KEY = "transferred_operations"


def operation_identity(item: dict[str, Any]) -> tuple[str, str]:
    return (
        normalize_order_code(item.get("production_order")),
        normalize_order_code(item.get("operation_code")),
    )


def normalize_work_center(value: Any) -> str:
    return str(value or "").strip()


@dataclass(frozen=True)
class OperationTransfer:
    operations: list[dict[str, Any]]
    operation: dict[str, Any]
    source_work_center: str
    target_work_center: str


def transfer_entries(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Transferências já gravadas no snapshot (sempre uma cópia)."""
    raw = payload.get(TRANSFERRED_OPERATIONS_KEY)
    if not isinstance(raw, list):
        return []
    return [
        dict(item)
        for item in raw
        if isinstance(item, dict) and item.get("production_order") and item.get("target_work_center")
    ]


def find_operation(
    operations: list[dict[str, Any]],
    *,
    production_order: str,
    operation_code: str,
) -> dict[str, Any] | None:
    wanted = (normalize_order_code(production_order), normalize_order_code(operation_code))
    for item in operations:
        if operation_identity(item) == wanted:
            return item
    return None


def original_work_center(
    entries: list[dict[str, Any]],
    *,
    production_order: str,
    operation_code: str,
    fallback: str,
) -> str:
    """Centro de onde a operação saiu no TOTVS — preservado entre transferências."""
    wanted = (normalize_order_code(production_order), normalize_order_code(operation_code))
    for item in entries:
        identity = (
            normalize_order_code(item.get("production_order")),
            normalize_order_code(item.get("operation_code")),
        )
        if identity == wanted and normalize_work_center(item.get("source_work_center")):
            return normalize_work_center(item.get("source_work_center"))
    return normalize_work_center(fallback)


def move_operation(
    operations: list[dict[str, Any]],
    *,
    production_order: str,
    operation_code: str,
    target_work_center: str,
    target_work_center_name: str | None = None,
    origin_work_center: str | None = None,
) -> OperationTransfer | None:
    """Move a operação para o fim da fila do centro destino.

    Devolve ``None`` quando a operação não está no snapshot. A lista original não
    é mutada — o chamador grava o resultado.
    """
    wanted = (normalize_order_code(production_order), normalize_order_code(operation_code))
    target = normalize_work_center(target_work_center)
    index = next(
        (pos for pos, item in enumerate(operations) if operation_identity(item) == wanted),
        None,
    )
    if index is None or not target:
        return None

    current = operations[index]
    source = normalize_work_center(current.get("work_center"))
    origin = normalize_work_center(origin_work_center) or source
    moved = dict(current)
    moved["work_center"] = target
    if target_work_center_name is not None:
        moved["work_center_name"] = target_work_center_name
    # Voltar ao centro de origem tira a marca: a operação não está mais transferida.
    if origin and origin != target:
        moved["transferred_from"] = origin
    else:
        moved.pop("transferred_from", None)

    remaining = [item for pos, item in enumerate(operations) if pos != index]
    last_target = next(
        (
            pos
            for pos in range(len(remaining) - 1, -1, -1)
            if normalize_work_center(remaining[pos].get("work_center")) == target
        ),
        None,
    )
    insert_at = len(remaining) if last_target is None else last_target + 1
    next_operations = [*remaining[:insert_at], moved, *remaining[insert_at:]]
    return OperationTransfer(
        operations=next_operations,
        operation=moved,
        source_work_center=source,
        target_work_center=target,
    )


def register_transfer(
    entries: list[dict[str, Any]],
    *,
    production_order: str,
    operation_code: str,
    origin_work_center: str,
    target_work_center: str,
    transferred_at: str,
    transferred_by: str | None,
) -> list[dict[str, Any]]:
    """Guarda a transferência para o replay pós-refresh (uma entrada por operação)."""
    order = normalize_order_code(production_order)
    operation = normalize_order_code(operation_code)
    origin = normalize_work_center(origin_work_center)
    target = normalize_work_center(target_work_center)
    kept = [
        item
        for item in entries
        if (
            normalize_order_code(item.get("production_order")),
            normalize_order_code(item.get("operation_code")),
        )
        != (order, operation)
    ]
    # Voltar ao centro de origem desfaz a transferência: nada a reaplicar no refresh.
    if not target or origin == target:
        return kept
    return [
        *kept,
        {
            "production_order": order,
            "operation_code": operation,
            "source_work_center": origin,
            "target_work_center": target,
            "transferred_at": transferred_at,
            "transferred_by": transferred_by,
        },
    ]


def apply_transfers(
    operations: list[dict[str, Any]],
    entries: list[dict[str, Any]],
    *,
    work_center_names: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Reaplica as transferências sobre a fila recém-puxada do TOTVS."""
    names = work_center_names or {}
    result = list(operations)
    for entry in entries:
        target = normalize_work_center(entry.get("target_work_center"))
        moved = move_operation(
            result,
            production_order=str(entry.get("production_order") or ""),
            operation_code=str(entry.get("operation_code") or ""),
            target_work_center=target,
            target_work_center_name=names.get(target),
            origin_work_center=normalize_work_center(entry.get("source_work_center")),
        )
        if moved is not None:
            result = moved.operations
    return result
