"""Mapper — linha da SH8010 enriquecida → item canônico EN snake_case."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from app.domain.production.machine_load_scope import MANUAL_LABOR_TOOL_CODE
from app.domain.totvs.protheus_operation_appointments import (
    PRODUCTION_STATUS_IN_PROGRESS,
    PRODUCTION_STATUS_NOT_STARTED,
    PRODUCTION_STATUS_STARTED,
    split_active_marker,
)


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _iso_date(value: Any) -> str | None:
    """Aceita YYYYMMDD (Protheus) e date/datetime/ISO (view PCP)."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    if not text:
        return None
    if text.isdigit() and len(text) == 8:
        if text == "00000000":
            return None
        return f"{text[0:4]}-{text[4:6]}-{text[6:8]}"
    if "T" in text:
        text = text.split("T", 1)[0]
    if " " in text:
        text = text.split(" ", 1)[0]
    return text[:10] or None


def _time_of_day(value: Any) -> str | None:
    text = _clean(value)
    return text or None


def _as_float(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    return float(value)


def _as_int(value: Any) -> int:
    if value is None or value == "":
        return 0
    return int(float(value))


def _production_status(
    row: dict[str, Any], *, operation_pending_qty: float | None = None
) -> dict[str, Any]:
    """Deriva o estado de produção da operação a partir do agregado da HZA.

    ``in_progress`` exige apontamento aberto e recente; ``started`` marca a
    operação que já passou pela máquina mas não está rodando agora. Em ambos
    os casos o operador vem do marcador HZA (ativo ou último do histórico).

    OP encerrada no SC2 (``C2_DATRF``) ou **sem saldo** nunca fica
    ``in_progress``, mesmo com apontamento aberto e recente: o operador que não
    encerra no coletor deixaria a fila mostrando «Em produção» para sempre.
    O saldo que manda é o da própria operação (``operation_pending_qty``); o do
    cabeçalho só entra quando o apontamento por operação não veio.
    """
    active_count = _as_int(row.get("active_appointment_count"))
    appointment_count = _as_int(row.get("appointment_count"))
    order_finished = bool(_as_int(row.get("order_is_finished")))
    balance_exhausted = _balance_exhausted(
        row, operation_pending_qty=operation_pending_qty
    )
    finish_date = _iso_date(row.get("order_finish_date") or row.get("finish_date"))
    started_date, started_time, operator_code, operator_name = split_active_marker(
        _clean(row.get("active_marker"))
    )
    last_date, last_time, last_operator_code, last_operator_name = split_active_marker(
        _clean(row.get("last_marker"))
    )
    in_production = (
        active_count > 0
        and bool(started_date)
        and not order_finished
        and not balance_exhausted
    )

    if in_production:
        status = PRODUCTION_STATUS_IN_PROGRESS
    elif appointment_count > 0 or order_finished or balance_exhausted:
        status = PRODUCTION_STATUS_STARTED
    else:
        status = PRODUCTION_STATUS_NOT_STARTED

    if in_production:
        display_date, display_time = started_date, started_time
        display_code, display_name = operator_code, operator_name
    elif status == PRODUCTION_STATUS_STARTED and last_date:
        display_date, display_time = last_date, last_time
        display_code, display_name = last_operator_code, last_operator_name
    elif status == PRODUCTION_STATUS_STARTED and finish_date:
        display_date, display_time = finish_date, ""
        display_code = display_name = ""
    else:
        display_date = display_time = display_code = display_name = ""

    return {
        "production_status": status,
        "is_in_production": in_production,
        "production_started_date": _iso_date(display_date) if display_date else None,
        "production_started_time": (display_time or None) if display_time else None,
        "active_operator_code": (display_code or None) if display_code else None,
        "active_operator_name": (display_name or None) if display_name else None,
        "active_operator_count": (
            _as_int(row.get("active_operator_count")) if in_production else 0
        ),
        "appointment_count": appointment_count,
        "last_appointment_date": _iso_date(row.get("last_appointment_date")),
    }


def _balance_exhausted(
    row: dict[str, Any], *, operation_pending_qty: float | None = None
) -> bool:
    """Saldo zerado — o da operação manda; o da OP é fallback.

    O enrich vivo de apontamento **não** deve inventar saldo ``0``: ausência do
    campo significa «saldo desconhecido», não «saldo esgotado».
    """
    if operation_pending_qty is not None:
        return operation_pending_qty <= 1e-9
    if "pending_qty" not in row:
        return False
    pending = row.get("pending_qty")
    if pending is None or pending == "":
        return False
    try:
        return float(pending) <= 1e-9
    except (TypeError, ValueError):
        return False


def _optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _operation_balance(
    row: dict[str, Any], *, planned_qty: float
) -> tuple[float | None, float | None]:
    """Produzido e saldo da **própria operação** (SH6010), não do cabeçalho.

    ``C2_QUJE`` só anda no apontamento que dá entrada em estoque, então o saldo
    do SC2 vem igual em todas as operações da OP. Aqui o saldo é
    ``C2_QUANT − SUM(H6_QTDPROD)`` da operação, sem descontar refugo: peça
    refugada continua faltando na bancada.

    Devolve ``(None, None)`` quando o apontamento por operação não veio no row —
    saldo desconhecido não pode virar zero. OP encerrada ou já sem saldo no
    cabeçalho zeram a operação: operação que nunca é apontada não pode ficar
    eternamente pendente.
    """
    produced = _optional_float(row.get("operation_produced_qty"))
    if produced is None:
        return None, None
    produced = round(produced, 6)
    if bool(_as_int(row.get("order_is_finished"))) or _balance_exhausted(row):
        return produced, 0.0
    if planned_qty <= 0:
        return produced, None
    return produced, round(max(planned_qty - produced, 0.0), 6)


class MachineLoadOperationMapper:
    """Converte a operação alocada em item de API (datas ISO, códigos trimados)."""

    @classmethod
    def map_operation(cls, row: dict[str, Any]) -> dict[str, Any]:
        planned = _as_float(row.get("planned_qty"))
        produced = _as_float(row.get("produced_qty"))
        pending = row.get("pending_qty")
        pending_qty = (
            round(planned - produced, 6)
            if pending is None or pending == ""
            else round(_as_float(pending), 6)
        )

        operation_produced_qty, operation_pending_qty = _operation_balance(
            row, planned_qty=planned
        )

        tool = _clean(row.get("tool"))
        work_center = _clean(row.get("work_center"))

        return {
            "branch": _clean(row.get("branch")),
            "work_center": work_center,
            "work_center_name": _clean(row.get("work_center_name")),
            "scheduled_date": _iso_date(row.get("scheduled_date")),
            "scheduled_start_time": _time_of_day(row.get("scheduled_start_time")),
            "scheduled_end_date": _iso_date(row.get("scheduled_end_date")),
            "scheduled_end_time": _time_of_day(row.get("scheduled_end_time")),
            "production_order": _clean(row.get("production_order")),
            "operation_code": _clean(row.get("operation_code")),
            "operation_description": _clean(row.get("operation_description")),
            "tool": tool,
            "is_manual_operation": tool.upper() == MANUAL_LABOR_TOOL_CODE,
            "resource": _clean(row.get("resource")) or None,
            "product_code": _clean(row.get("product_code")),
            "product_description": _clean(row.get("product_description")),
            "unit": _clean(row.get("unit")) or None,
            "planned_qty": round(planned, 6),
            "produced_qty": round(produced, 6),
            "pending_qty": pending_qty,
            "operation_produced_qty": operation_produced_qty,
            "operation_pending_qty": operation_pending_qty,
            "pa_due_date": _iso_date(row.get("pa_due_date")),
            "due_date": _iso_date(row.get("due_date")),
            "due_date_source": _clean(row.get("due_date_source")) or None,
            "pa_production_order": _clean(row.get("pa_production_order")) or None,
            "pa_product_code": _clean(row.get("pa_product_code")) or None,
            "pa_product_description": _clean(row.get("pa_product_description")) or None,
            **_production_status(row, operation_pending_qty=operation_pending_qty),
        }

    @classmethod
    def map_operations(cls, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [cls.map_operation(row) for row in rows]

    @classmethod
    def map_work_center(cls, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "work_center": _clean(row.get("work_center")),
            "work_center_name": _clean(row.get("work_center_name")),
            "operation_count": _as_int(row.get("operation_count")),
            "order_count": _as_int(row.get("order_count")),
            "in_production_count": _as_int(row.get("in_production_count")),
            "first_scheduled_date": _iso_date(row.get("first_scheduled_date")),
            "last_scheduled_date": _iso_date(row.get("last_scheduled_date")),
            "first_due_date": _iso_date(row.get("first_due_date")),
            "last_due_date": _iso_date(row.get("last_due_date")),
            "missing_due_date_count": _as_int(row.get("missing_due_date_count")),
        }

    @classmethod
    def map_work_centers(cls, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [cls.map_work_center(row) for row in rows]
