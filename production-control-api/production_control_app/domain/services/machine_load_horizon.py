"""Horizonte temporário por centro de trabalho (exceção por geração WORKING).

Ampliação seletiva da janela de entrega do PA para um CT, sem alterar o
horizonte global da filial. A exceção vive só no payload WORKING da geração
atual e some no próximo refresh — sem migration e sem preferência permanente.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from production_control_app.domain.services.machine_load_delivery_window import (
    operation_due_date,
)
from production_control_app.domain.services.machine_load_transfer import (
    normalize_work_center,
    operation_identity,
)

HORIZON_EXCEPTIONS_KEY = "horizon_exceptions"
HORIZON_EXPANDED_FLAG = "horizon_expanded"

# Presets de produto — dias a partir de «hoje» no timezone da carga máquina.
HORIZON_PRESET_DAYS: tuple[int, ...] = (21, 28, 42)

# Teto absoluto além do «hoje» de referência (data personalizada inclusa).
MAX_HORIZON_DAYS_FROM_TODAY = 90


def parse_horizon_end(value: str | None) -> date | None:
    text = str(value or "").strip()[:10]
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def additional_period_start(base_end: date) -> date:
    """Primeiro dia *após* o fim da janela-base — evita reconsultar o já puxado."""
    return base_end + timedelta(days=1)


def validate_horizon_end(
    *,
    requested_end: date,
    base_end: date,
    today: date,
) -> None:
    """Valida data final da ampliação contra a janela-base e o teto operacional."""
    if requested_end <= base_end:
        raise ValueError(
            "A data final do horizonte ampliado deve ultrapassar o fim da "
            f"janela-base ({base_end.isoformat()})."
        )
    max_end = today + timedelta(days=MAX_HORIZON_DAYS_FROM_TODAY)
    if requested_end > max_end:
        raise ValueError(
            "A data final do horizonte ampliado não pode ultrapassar "
            f"{max_end.isoformat()} (limite de {MAX_HORIZON_DAYS_FROM_TODAY} dias)."
        )


def horizon_exceptions_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = payload.get(HORIZON_EXCEPTIONS_KEY)
    if not isinstance(raw, dict):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for key, value in raw.items():
        center = normalize_work_center(key)
        if not center or not isinstance(value, dict):
            continue
        out[center] = dict(value)
    return out


def present_horizon_exceptions(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Lista estável para o contrato autenticado (F5 / troca de CT)."""
    items: list[dict[str, Any]] = []
    for center, entry in sorted(horizon_exceptions_map(payload).items()):
        items.append(
            {
                "work_center": center,
                "end_date": str(entry.get("end_date") or "")[:10] or None,
                "base_end_date": str(entry.get("base_end_date") or "")[:10] or None,
                "added_count": int(entry.get("added_count") or 0),
                "expanded_at": entry.get("expanded_at"),
                "expanded_by": entry.get("expanded_by"),
            }
        )
    return items


def existing_operation_identities(
    operations: list[dict[str, Any]],
) -> set[tuple[str, str]]:
    """Identidade canônica OP+operação — cobre transferências entre CTs."""
    return {operation_identity(item) for item in operations}


def filter_new_horizon_operations(
    *,
    candidates: list[dict[str, Any]],
    work_center: str,
    existing: set[tuple[str, str]],
    additional_start: date,
    additional_end: date,
) -> list[dict[str, Any]]:
    """Operações elegíveis ainda ausentes da fila, no CT e no intervalo adicional."""
    center = normalize_work_center(work_center)
    start_s = additional_start.isoformat()
    end_s = additional_end.isoformat()
    added: list[dict[str, Any]] = []
    seen = set(existing)
    for item in candidates:
        if normalize_work_center(item.get("work_center")) != center:
            continue
        identity = operation_identity(item)
        if identity in seen:
            continue
        due = operation_due_date(item)
        # Sem entrega: mantém a regra da janela — o PCP precisa ver para corrigir.
        if due is not None and (due < start_s or due > end_s):
            continue
        marked = dict(item)
        marked[HORIZON_EXPANDED_FLAG] = True
        added.append(marked)
        seen.add(identity)
    return added


def append_operations_after_center(
    operations: list[dict[str, Any]],
    *,
    work_center: str,
    new_operations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Insere novas ops logo após a última operação já presente do CT."""
    if not new_operations:
        return list(operations)
    center = normalize_work_center(work_center)
    last_index = -1
    for index, item in enumerate(operations):
        if normalize_work_center(item.get("work_center")) == center:
            last_index = index
    if last_index < 0:
        return list(operations) + list(new_operations)
    head = operations[: last_index + 1]
    tail = operations[last_index + 1 :]
    return list(head) + list(new_operations) + list(tail)


def upsert_horizon_exception(
    payload: dict[str, Any],
    *,
    work_center: str,
    end_date: date,
    base_end_date: date,
    added_count: int,
    expanded_at: str,
    expanded_by: str | None,
) -> None:
    """Grava/atualiza a exceção do CT sem apagar as dos demais."""
    center = normalize_work_center(work_center)
    exceptions = horizon_exceptions_map(payload)
    previous = exceptions.get(center) or {}
    previous_added = int(previous.get("added_count") or 0)
    exceptions[center] = {
        "end_date": end_date.isoformat(),
        "base_end_date": base_end_date.isoformat(),
        "added_count": previous_added + max(0, added_count),
        "expanded_at": expanded_at,
        "expanded_by": expanded_by,
    }
    payload[HORIZON_EXCEPTIONS_KEY] = exceptions


def days_from_today(end: date, *, today: date) -> int:
    return (end - today).days
