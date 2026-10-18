"""Transferência de operação(ões) para outro centro de trabalho.

Regra de negócio: o PCP pode mover **uma** operação (OP + operação) ou **todas
as operações do conjunto que estão no centro atual** para a fila de outro
centro. As operações entram no fim da fila do destino — de lá o analista
reordena ou prioriza como qualquer outra.

A decisão é local do Portal PCP: o snapshot é reescrito, e a lista
``transferred_operations`` no ``payload_json`` guarda o histórico para que o
«Atualizar» do TOTVS reaplique as transferências em cima da fila nova.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from production_control_app.domain.services.production_order_key import (
    normalize_order_code,
    order_belongs_to_conjunto,
)

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


@dataclass(frozen=True)
class ConjuntoCenterTransfer:
    """Resultado de mover o conjunto **só** no centro de origem informado."""

    operations: list[dict[str, Any]]
    moved: list[dict[str, Any]]
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
    work_center: str | None = None,
) -> dict[str, Any] | None:
    """Localiza a operação; com ``work_center`` a busca fica restrita ao centro.

    Sem centro informado (chamador legado) devolve o primeiro match — a mesma
    OP/operação em centros distintos é ambígua e quem precisa de identidade
    inequívoca deve passar o centro.
    """
    wanted = (normalize_order_code(production_order), normalize_order_code(operation_code))
    center = normalize_work_center(work_center) if work_center else None
    for item in operations:
        if center is not None and normalize_work_center(item.get("work_center")) != center:
            continue
        if operation_identity(item) == wanted:
            return item
    return None


def operation_matches_in_center(
    item: dict[str, Any],
    *,
    production_order: str,
    operation_code: str,
    work_center: str,
) -> bool:
    """Identidade canônica CT + OP + operação — único jeito inequívoco."""
    return (
        operation_identity(item)
        == (normalize_order_code(production_order), normalize_order_code(operation_code))
    ) and normalize_work_center(item.get("work_center")) == normalize_work_center(work_center)


def original_work_center(
    entries: list[dict[str, Any]],
    *,
    production_order: str,
    operation_code: str,
    fallback: str,
    work_center: str | None = None,
) -> str:
    """Centro de onde a operação saiu no TOTVS — preservado entre transferências.

    ``work_center`` deve ser a origem ERP conhecida da instância —
    ``item.transferred_from`` quando já transferida, senão o centro atual.
    Com a mesma OP/operação em dois centros, só a entrada cuja origem bate
    com a instância é aceita; match ambíguo nunca escolhe arbitrariamente.
    """
    wanted = (normalize_order_code(production_order), normalize_order_code(operation_code))
    origin_hint = normalize_work_center(work_center) if work_center else None
    for item in entries:
        identity = (
            normalize_order_code(item.get("production_order")),
            normalize_order_code(item.get("operation_code")),
        )
        if identity != wanted:
            continue
        origin = normalize_work_center(item.get("source_work_center"))
        if not origin:
            continue
        if origin_hint is None or origin == origin_hint:
            return origin
    return normalize_work_center(fallback)


def _apply_center_move(
    item: dict[str, Any],
    *,
    target: str,
    target_work_center_name: str | None,
    origin: str,
) -> dict[str, Any]:
    moved = dict(item)
    moved["work_center"] = target
    if target_work_center_name is not None:
        moved["work_center_name"] = target_work_center_name
    if origin and origin != target:
        moved["transferred_from"] = origin
    else:
        moved.pop("transferred_from", None)
    return moved


def _insert_at_end_of_center(
    operations: list[dict[str, Any]],
    *,
    target: str,
    batch: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not batch:
        return list(operations)
    last_target = next(
        (
            pos
            for pos in range(len(operations) - 1, -1, -1)
            if normalize_work_center(operations[pos].get("work_center")) == target
        ),
        None,
    )
    insert_at = len(operations) if last_target is None else last_target + 1
    return [*operations[:insert_at], *batch, *operations[insert_at:]]


def move_operation(
    operations: list[dict[str, Any]],
    *,
    production_order: str,
    operation_code: str,
    target_work_center: str,
    target_work_center_name: str | None = None,
    origin_work_center: str | None = None,
    source_work_center: str | None = None,
) -> OperationTransfer | None:
    """Move a operação para o fim da fila do centro destino.

    ``source_work_center`` restringe o match à instância que está naquele
    centro — sem ele o comportamento legado (primeiro match OP+op) é mantido.
    Devolve ``None`` quando a operação não está no snapshot. A lista original não
    é mutada — o chamador grava o resultado.
    """
    wanted = (normalize_order_code(production_order), normalize_order_code(operation_code))
    target = normalize_work_center(target_work_center)
    source = normalize_work_center(source_work_center) if source_work_center else None
    index = next(
        (
            pos
            for pos, item in enumerate(operations)
            if operation_identity(item) == wanted
            and (source is None or normalize_work_center(item.get("work_center")) == source)
        ),
        None,
    )
    if index is None or not target:
        return None

    current = operations[index]
    source = normalize_work_center(current.get("work_center"))
    origin = normalize_work_center(origin_work_center) or source
    moved = _apply_center_move(
        current,
        target=target,
        target_work_center_name=target_work_center_name,
        origin=origin,
    )

    remaining = [item for pos, item in enumerate(operations) if pos != index]
    next_operations = _insert_at_end_of_center(remaining, target=target, batch=[moved])
    return OperationTransfer(
        operations=next_operations,
        operation=moved,
        source_work_center=source,
        target_work_center=target,
    )


def move_conjunto_at_work_center(
    operations: list[dict[str, Any]],
    *,
    conjunto_key: str,
    source_work_center: str,
    target_work_center: str,
    target_work_center_name: str | None = None,
    transfer_log: list[dict[str, Any]] | None = None,
) -> ConjuntoCenterTransfer | None:
    """Move só as OPs do conjunto que estão no centro de origem.

    OPs do mesmo C2_NUM em **outros** centros ficam onde estão. A ordem relativa
    entre as movidas é preservada; elas entram no fim da fila do destino.
    """
    key = normalize_order_code(conjunto_key)
    source = normalize_work_center(source_work_center)
    target = normalize_work_center(target_work_center)
    if not key or not source or not target or source == target:
        return None

    entries = transfer_log or []
    selected_indexes: list[int] = []
    for pos, item in enumerate(operations):
        if normalize_work_center(item.get("work_center")) != source:
            continue
        if not order_belongs_to_conjunto(item.get("production_order"), key):
            continue
        selected_indexes.append(pos)

    if not selected_indexes:
        return None

    selected_set = set(selected_indexes)
    batch: list[dict[str, Any]] = []
    for pos in selected_indexes:
        current = operations[pos]
        origin_hint = normalize_work_center(current.get("transferred_from")) or source
        origin = original_work_center(
            entries,
            production_order=str(current.get("production_order") or ""),
            operation_code=str(current.get("operation_code") or ""),
            fallback=source,
            work_center=origin_hint,
        )
        batch.append(
            _apply_center_move(
                current,
                target=target,
                target_work_center_name=target_work_center_name,
                origin=origin,
            )
        )

    remaining = [item for pos, item in enumerate(operations) if pos not in selected_set]
    next_operations = _insert_at_end_of_center(remaining, target=target, batch=batch)
    return ConjuntoCenterTransfer(
        operations=next_operations,
        moved=batch,
        source_work_center=source,
        target_work_center=target,
    )


def move_operations_at_work_center(
    operations: list[dict[str, Any]],
    *,
    keys: list[tuple[str, str]],
    source_work_center: str,
    target_work_center: str,
    target_work_center_name: str | None = None,
    transfer_log: list[dict[str, Any]] | None = None,
) -> ConjuntoCenterTransfer | None:
    """Move as operações listadas (OP + operação) que estão no centro de origem.

    Seleção arbitrária do PCP — não é conjunto: só as chaves pedidas saem da
    origem, preservando a ordem relativa, e entram no fim da fila do destino.
    ``keys`` sem correspondência na origem devolvem ``None`` — a validação de
    existência/ambiguidade é responsabilidade do chamador (antes do move).
    """
    source = normalize_work_center(source_work_center)
    target = normalize_work_center(target_work_center)
    if not keys or not source or not target or source == target:
        return None
    wanted = {
        (normalize_order_code(order), normalize_order_code(operation))
        for order, operation in keys
    }

    entries = transfer_log or []
    selected_indexes = [
        pos
        for pos, item in enumerate(operations)
        if normalize_work_center(item.get("work_center")) == source
        and operation_identity(item) in wanted
    ]
    if not selected_indexes or len(selected_indexes) != len(wanted):
        return None

    selected_set = set(selected_indexes)
    batch: list[dict[str, Any]] = []
    for pos in selected_indexes:
        current = operations[pos]
        origin_hint = normalize_work_center(current.get("transferred_from")) or source
        origin = original_work_center(
            entries,
            production_order=str(current.get("production_order") or ""),
            operation_code=str(current.get("operation_code") or ""),
            fallback=source,
            work_center=origin_hint,
        )
        batch.append(
            _apply_center_move(
                current,
                target=target,
                target_work_center_name=target_work_center_name,
                origin=origin,
            )
        )

    remaining = [item for pos, item in enumerate(operations) if pos not in selected_set]
    next_operations = _insert_at_end_of_center(remaining, target=target, batch=batch)
    return ConjuntoCenterTransfer(
        operations=next_operations,
        moved=batch,
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
    """Guarda a transferência para o replay pós-refresh (uma entrada por operação).

    A identidade do registro é ``(OP, operação, source_work_center)`` — a mesma
    OP/operação pode existir em dois centros ERP e cada instância tem a sua
    transferência. Entrada legada sem ``source_work_center`` é substituída
    quando OP+op coincidem (era a melhor informação disponível).
    """
    order = normalize_order_code(production_order)
    operation = normalize_order_code(operation_code)
    origin = normalize_work_center(origin_work_center)
    target = normalize_work_center(target_work_center)
    kept = [
        item
        for item in entries
        if not (
            (
                normalize_order_code(item.get("production_order")),
                normalize_order_code(item.get("operation_code")),
            )
            == (order, operation)
            and (
                normalize_work_center(item.get("source_work_center")) == origin
                or not normalize_work_center(item.get("source_work_center"))
            )
        )
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
    """Reaplica as transferências sobre a fila recém-puxada do TOTVS.

    O match usa a identidade completa ``(OP, operação, centro de origem ERP)``:
    depois do refresh a operação volta para o centro em que o TOTVS a criou,
    e é essa instância — não um homônimo em outro centro — que é movida.
    Entrada sem ``source_work_center`` só é aplicada quando OP+op é inequívoco
    na fila; ambiguidade é ignorada (nunca «adivinha» a instância).
    """
    names = work_center_names or {}
    result = list(operations)
    for entry in entries:
        target = normalize_work_center(entry.get("target_work_center"))
        source = normalize_work_center(entry.get("source_work_center"))
        if not source:
            wanted = (
                normalize_order_code(entry.get("production_order")),
                normalize_order_code(entry.get("operation_code")),
            )
            matches = [
                item for item in result if operation_identity(item) == wanted
            ]
            if len(matches) != 1:
                continue
        moved = move_operation(
            result,
            production_order=str(entry.get("production_order") or ""),
            operation_code=str(entry.get("operation_code") or ""),
            target_work_center=target,
            target_work_center_name=names.get(target),
            origin_work_center=source,
            source_work_center=source or None,
        )
        if moved is not None:
            result = moved.operations
    return result
