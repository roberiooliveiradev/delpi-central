"""Regra da janela de entrega do PA — o período que o PCP usa para planejar.

A api-delpi entrega ``due_date`` (entrega efetiva: OP mãe e, sem ela, a previsão
da própria OP). ``pa_due_date`` fica como retaguarda para snapshot antigo, gravado
antes de a entrega efetiva existir no contrato.
"""

from __future__ import annotations

from datetime import date
from typing import Any

DUE_DATE_FIELD = "due_date"
FALLBACK_DUE_DATE_FIELD = "pa_due_date"


def operation_due_date(operation: dict[str, Any]) -> str | None:
    """Entrega da operação em ISO (YYYY-MM-DD), ou None quando o TOTVS não tem."""
    for field in (DUE_DATE_FIELD, FALLBACK_DUE_DATE_FIELD):
        text = str(operation.get(field) or "").strip()[:10]
        if text:
            return text
    return None


def within_delivery_window(
    operation: dict[str, Any],
    *,
    start: date | None,
    end: date | None,
) -> bool:
    """Operação sem entrega nunca some da fila: o PCP precisa vê-la para corrigir."""
    due = operation_due_date(operation)
    if due is None:
        return True
    if start is not None and due < start.isoformat():
        return False
    if end is not None and due > end.isoformat():
        return False
    return True


def filter_by_delivery_window(
    operations: list[dict[str, Any]],
    *,
    start: date | None,
    end: date | None,
) -> list[dict[str, Any]]:
    if start is None and end is None:
        return operations
    return [
        item for item in operations if within_delivery_window(item, start=start, end=end)
    ]


def delivery_bounds(operations: list[dict[str, Any]]) -> tuple[str | None, str | None]:
    """Entrega mais antiga e mais distante da fila — alimenta o campo «De» da tela."""
    dates = [due for item in operations if (due := operation_due_date(item))]
    if not dates:
        return None, None
    return min(dates), max(dates)


def missing_due_date_count(operations: list[dict[str, Any]]) -> int:
    return sum(1 for item in operations if operation_due_date(item) is None)
