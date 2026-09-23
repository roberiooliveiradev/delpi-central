"""Lente de corte por horário programado — o que a bancada precisa até um horário.

Semântica diferente da janela de entrega (`machine_load_delivery_window`): lá o
recorte é a entrega do PA, aqui é o **início programado da operação**
(``scheduled_date`` + ``scheduled_start_time``, vindos de ``H8_DTINI``/``H8_HRINI``).
O alimentador não pergunta "o que entrega dia 30", ele pergunta "o que precisa
estar na bancada às 14h".

Operação sem hora entra pelo corte da data, no mesmo princípio da janela de
entrega: o que o TOTVS não informou aparece para ser corrigido, não desaparece.
"""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Any

SCHEDULED_DATE_FIELD = "scheduled_date"
SCHEDULED_START_TIME_FIELD = "scheduled_start_time"

_MIDNIGHT = time(0, 0)


def parse_cutoff(cutoff_date: str | None, cutoff_time: str | None) -> datetime:
    """Monta o corte a partir de data ISO e hora ``HH:MM``.

    Sem hora, o corte é o fim do dia: pedir "dia 30" significa o dia inteiro.
    """
    day = _parse_date(cutoff_date)
    if day is None:
        raise ValueError("Informe a data de corte (cutoffDate) no formato AAAA-MM-DD.")

    if not str(cutoff_time or "").strip():
        return datetime.combine(day, time(23, 59, 59))

    moment = _parse_time(cutoff_time)
    if moment is None:
        raise ValueError("Informe a hora de corte (cutoffTime) no formato HH:MM.")
    return datetime.combine(day, moment)


def operation_scheduled_start(operation: dict[str, Any]) -> datetime | None:
    """Início programado da operação, ou ``None`` quando não há data no snapshot."""
    day = _parse_date(operation.get(SCHEDULED_DATE_FIELD))
    if day is None:
        return None
    moment = _parse_time(operation.get(SCHEDULED_START_TIME_FIELD)) or _MIDNIGHT
    return datetime.combine(day, moment)


def within_cutoff(operation: dict[str, Any], *, cutoff: datetime) -> bool:
    """Operação sem data programada nunca é escondida do alimentador."""
    start = operation_scheduled_start(operation)
    if start is None:
        return True
    return start <= cutoff


def filter_by_cutoff(
    operations: list[dict[str, Any]],
    *,
    cutoff: datetime,
) -> list[dict[str, Any]]:
    return [item for item in operations if within_cutoff(item, cutoff=cutoff)]


def sort_by_scheduled_start(operations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Ordem de consumo da bancada: quem começa mais cedo vem primeiro.

    Operação sem data programada vai para o fim: ela não pode furar a fila de
    quem tem horário definido ao disputar o mesmo material.
    """
    return sorted(operations, key=_scheduled_sort_key)


def _scheduled_sort_key(operation: dict[str, Any]) -> tuple[int, str, str, str, str]:
    start = operation_scheduled_start(operation)
    return (
        1 if start is None else 0,
        start.isoformat() if start is not None else "",
        str(operation.get("work_center") or ""),
        str(operation.get("production_order") or ""),
        str(operation.get("operation_code") or ""),
    )


def _parse_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value or "").strip()[:10]
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _parse_time(value: Any) -> time | None:
    if isinstance(value, datetime):
        return value.time()
    if isinstance(value, time):
        return value
    text = str(value or "").strip()
    if not text:
        return None
    # O TOTVS entrega HHMM em alguns campos de hora; a api-delpi normaliza para
    # HH:MM, mas snapshot antigo pode ter a forma crua.
    if ":" not in text and text.isdigit() and len(text) == 4:
        text = f"{text[:2]}:{text[2:]}"
    parts = text.split(":")
    if len(parts) < 2:
        return None
    try:
        hour = int(parts[0])
        minute = int(parts[1])
        second = int(parts[2]) if len(parts) > 2 else 0
    except ValueError:
        return None
    if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
        return None
    return time(hour, minute, second)
