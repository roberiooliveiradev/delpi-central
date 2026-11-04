"""Projeção da fila PUBLISHED para o Alimentador de Linha.

Lê a mesma publicação que alimenta o cockpit do operador. Não usa WORKING,
não reordena por horário TOTVS e não inventa saldo zero quando o saldo é
desconhecido.

A ordem efetiva é a do array ``operations`` após retiradas — a mesma sequência
disponibilizada ao chão de fábrica após mutações do PCP (incluindo LIVE).
"""

from __future__ import annotations

from typing import Any

from production_control_app.domain.services.machine_load_handoff import (
    operation_balance_state,
)
from production_control_app.domain.services.machine_load_snapshot_payload import (
    decode_snapshot_payload,
    payload_operations,
    payload_work_centers,
)
from production_control_app.domain.services.machine_load_transfer import (
    normalize_work_center,
)
from production_control_app.domain.services.machine_load_withdrawal import (
    visible_operations,
    withdrawn_marks,
)

BALANCE_SOURCE_OPERATION = "operation_pending_qty"
BALANCE_SOURCE_HEADER = "pending_qty"
BALANCE_SOURCE_UNAVAILABLE = "unavailable"


def _literal(value: Any) -> str:
    """Identidade literal: preserva zeros à esquerda; só remove espaços laterais."""
    return str(value if value is not None else "").strip()


def _optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number:  # NaN
        return None
    return number


def pending_balance(item: dict[str, Any]) -> tuple[float | None, str, str]:
    """(qty|None, balance_state, balance_source) — espelho do cockpit/handoff."""
    operation_pending = _optional_float(item.get("operation_pending_qty"))
    if operation_pending is not None:
        state = "open" if operation_pending > 1e-9 else "closed"
        return operation_pending, state, BALANCE_SOURCE_OPERATION
    header_pending = _optional_float(item.get("pending_qty"))
    if header_pending is not None:
        state = "open" if header_pending > 1e-9 else "closed"
        return header_pending, state, BALANCE_SOURCE_HEADER
    # Desconhecido: nunca virar zero. Estado alinhado a operation_balance_state.
    assert operation_balance_state(item) == "unknown"
    return None, "unknown", BALANCE_SOURCE_UNAVAILABLE


def build_operation_id(
    *,
    branch: str,
    work_center: str,
    production_order: str,
    operation_code: str,
) -> str:
    """Identidade estável e literal da operação na fila publicada."""
    return "|".join(
        (
            _literal(branch),
            _literal(work_center),
            _literal(production_order),
            _literal(operation_code),
        )
    )


def _iso(value: Any) -> str | None:
    if value is None or value == "":
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _has_cockpit_open_balance(item: dict[str, Any]) -> bool:
    """Mesma regra de ``open_only`` do cockpit: fecha só saldo conhecido <= 0."""
    _qty, state, _source = pending_balance(item)
    return state != "closed"


def project_published_queue(
    row: dict[str, Any],
    *,
    branch: str,
    work_center: str | None = None,
) -> dict[str, Any]:
    """Projeta a publicação vigente no contrato de leitura do Alimentador.

    ``row`` é a linha de ``MachineLoadPublicationRepositoryPort.get`` — nunca o
    snapshot WORKING. Filtra retiradas e operações com saldo comprovadamente
    zero; mantém saldo desconhecido. Agrupa por CT preservando a ordem do
    array publicado.
    """
    code = _literal(branch)
    payload = decode_snapshot_payload(row)
    marks = withdrawn_marks(payload)
    visible = visible_operations(payload_operations(payload), marks)
    eligible = [item for item in visible if _has_cockpit_open_balance(item)]

    requested = normalize_work_center(work_center) if work_center else ""
    if requested:
        eligible = [
            item
            for item in eligible
            if normalize_work_center(item.get("work_center")) == requested
        ]

    names = {
        normalize_work_center(item.get("work_center")): _literal(
            item.get("work_center_name")
        )
        for item in payload_work_centers(payload)
        if normalize_work_center(item.get("work_center"))
    }

    groups: list[dict[str, Any]] = []
    index_by_center: dict[str, int] = {}
    for item in eligible:
        center = normalize_work_center(item.get("work_center"))
        if not center:
            continue
        if center not in index_by_center:
            index_by_center[center] = len(groups)
            groups.append(
                {
                    "work_center": center,
                    "work_center_name": names.get(center)
                    or _literal(item.get("work_center_name")),
                    "operations": [],
                }
            )
        group = groups[index_by_center[center]]
        position = len(group["operations"]) + 1
        pending_qty, balance_state, balance_source = pending_balance(item)
        production_order = _literal(item.get("production_order"))
        operation_code = _literal(item.get("operation_code"))
        group["operations"].append(
            {
                "operation_id": build_operation_id(
                    branch=code,
                    work_center=center,
                    production_order=production_order,
                    operation_code=operation_code,
                ),
                "sequence_position": position,
                "branch": code,
                "work_center": center,
                "work_center_name": group["work_center_name"],
                "production_order": production_order,
                "operation_code": operation_code,
                "product_code": _literal(item.get("product_code")),
                "product_description": _literal(item.get("product_description")),
                "unit": _literal(item.get("unit")),
                "pieces_conversion_factor": _optional_float(
                    item.get("pieces_conversion_factor")
                ),
                "pending_qty": pending_qty,
                "balance_state": balance_state,
                "balance_source": balance_source,
                "planned_qty": _optional_float(item.get("planned_qty")),
                "pa_product_code": _literal(item.get("pa_product_code")) or None,
            }
        )

    revision = _literal(row.get("row_version"))
    operation_count = sum(len(group["operations"]) for group in groups)
    return {
        "branch": code,
        "filters": {"work_center": requested or None},
        "publication": {
            "generation_id": _literal(row.get("generation_id")) or None,
            "publication_revision": revision or None,
            "published_at": _iso(row.get("published_at")),
            "published_by": _literal(row.get("published_by")) or None,
            "source_refreshed_at": _iso(row.get("source_refreshed_at")),
            "start_date": _iso(row.get("start_date")),
            "end_date": _iso(row.get("end_date")),
        },
        "queue_status": "empty" if operation_count == 0 else "available",
        # Catálogo de seleção: código do CT em ordem alfabética.
        # work_center_queues mantém a ordem de primeira aparição na PUBLISHED
        # (sequência operacional por CT permanece intacta).
        "work_centers": sorted(
            [
                {
                    "work_center": group["work_center"],
                    "work_center_name": group["work_center_name"],
                    "operation_count": len(group["operations"]),
                }
                for group in groups
            ],
            key=lambda item: str(item["work_center"]).casefold(),
        ),
        "work_center_queues": groups,
        "operation_count": operation_count,
        "work_center_count": len(groups),
    }


def list_visible_published_queues(
    row: dict[str, Any],
    *,
    branch: str,
    work_centers: list[str] | None = None,
) -> dict[str, Any]:
    """Fila PUBLISHED visível por CT **sem** filtrar saldo fechado do snapshot.

    O motor de horizonte (Etapa 2) precisa consultar o saldo vivo antes de
    descartar operações — o ``pending`` congelado na publicação pode estar
    desatualizado.
    """
    code = _literal(branch)
    payload = decode_snapshot_payload(row)
    marks = withdrawn_marks(payload)
    visible = visible_operations(payload_operations(payload), marks)

    wanted = {
        normalize_work_center(center)
        for center in (work_centers or [])
        if normalize_work_center(center)
    }
    if wanted:
        visible = [
            item
            for item in visible
            if normalize_work_center(item.get("work_center")) in wanted
        ]

    names = {
        normalize_work_center(item.get("work_center")): _literal(
            item.get("work_center_name")
        )
        for item in payload_work_centers(payload)
        if normalize_work_center(item.get("work_center"))
    }

    groups: list[dict[str, Any]] = []
    index_by_center: dict[str, int] = {}
    for item in visible:
        center = normalize_work_center(item.get("work_center"))
        if not center:
            continue
        if center not in index_by_center:
            index_by_center[center] = len(groups)
            groups.append(
                {
                    "work_center": center,
                    "work_center_name": names.get(center)
                    or _literal(item.get("work_center_name")),
                    "operations": [],
                }
            )
        group = groups[index_by_center[center]]
        position = len(group["operations"]) + 1
        production_order = _literal(item.get("production_order"))
        operation_code = _literal(item.get("operation_code"))
        group["operations"].append(
            {
                "operation_id": build_operation_id(
                    branch=code,
                    work_center=center,
                    production_order=production_order,
                    operation_code=operation_code,
                ),
                "sequence_position": position,
                "branch": code,
                "work_center": center,
                "work_center_name": group["work_center_name"],
                "production_order": production_order,
                "operation_code": operation_code,
                "product_code": _literal(item.get("product_code")),
                "product_description": _literal(item.get("product_description")),
                "pa_product_code": _literal(item.get("pa_product_code")) or None,
                "unit": _literal(item.get("unit")),
                "pieces_conversion_factor": _optional_float(
                    item.get("pieces_conversion_factor")
                ),
                # Snapshot — apenas referência; o motor usa saldo vivo.
                "snapshot_pending_qty": pending_balance(item)[0],
                "snapshot_balance_state": pending_balance(item)[1],
            }
        )

    return {
        "branch": code,
        "publication": {
            "generation_id": _literal(row.get("generation_id")) or None,
            "publication_revision": _literal(row.get("row_version")) or None,
            "published_at": _iso(row.get("published_at")),
            "published_by": _literal(row.get("published_by")) or None,
            "source_refreshed_at": _iso(row.get("source_refreshed_at")),
            "start_date": _iso(row.get("start_date")),
            "end_date": _iso(row.get("end_date")),
        },
        "work_center_queues": groups,
        "available_work_centers": [
            {
                "work_center": normalize_work_center(item.get("work_center")),
                "work_center_name": _literal(item.get("work_center_name")),
            }
            for item in payload_work_centers(payload)
            if normalize_work_center(item.get("work_center"))
        ],
    }
