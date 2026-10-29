"""Datas e dias úteis do domínio LMP (R05 + parse de fonte).

R05 — dias úteis = seg-sex; feriados NÃO descontados no comportamento
vigente (DIV-03 / TO_INVENTORY na spec lmp_semantics.v1.yaml).
Parse cobre os formatos efetivamente emitidos pelos contratos facts
(ISO `YYYY-MM-DD`) e os formatos de fonte Protheus (`YYYYMMDD`,
`dd/mm/yyyy`) — espelha `parse_spreadsheet_date` da api-delpi sem
importar código entre bounded contexts.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

EXCEL_EPOCH = date(1899, 12, 30)


def parse_date(value: Any) -> date | None:
    """Interpreta datas ISO/Protheus/planilha; retorna None se inválido."""
    if value is None:
        return None

    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, (int, float)):
        try:
            return EXCEL_EPOCH + timedelta(days=int(value))
        except (OverflowError, ValueError):
            # Serial fora do range de date (ex.: int 20260501) cai no
            # strptime abaixo — paridade com parse_spreadsheet_date.
            pass

    raw = str(value).strip()
    if not raw:
        return None

    try:
        numeric = float(raw.replace(",", "."))
    except ValueError:
        numeric = None
    if numeric is not None and numeric >= 1:
        try:
            return EXCEL_EPOCH + timedelta(days=int(numeric))
        except OverflowError:
            # Serial fora do range de date (ex.: "20260501") cai no strptime.
            pass

    normalized = raw.replace(".", "/").replace("-", "/")
    normalized_head = normalized.split("T")[0].split(" ")[0].strip()

    for fmt in (
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%d/%m/%y",
        "%Y%m%d",
    ):
        try:
            return datetime.strptime(normalized_head, fmt).date()
        except ValueError:
            pass

    try:
        return datetime.fromisoformat(raw).date()
    except ValueError:
        return None


def format_date_ymd(value: date | None) -> str | None:
    """Formato interno Protheus (YYYYMMDD). Não usar em payload HTTP."""
    if not value:
        return None
    return value.strftime("%Y%m%d")


def format_date_iso(value: Any) -> str | None:
    """Serialização HTTP do domínio: ISO ``YYYY-MM-DD``; inválido → None."""
    parsed = parse_date(value)
    return parsed.isoformat() if parsed else None


def is_weekend(value: date) -> bool:
    return value.weekday() >= 5


def add_business_days(start: date, business_days: int) -> date:
    """R03/R05 — soma dias úteis (fds excluídos; feriados TO_INVENTORY)."""
    result = start
    added = 0
    while added < business_days:
        result += timedelta(days=1)
        if not is_weekend(result):
            added += 1
    return result


def business_days_between(start: date, end: date) -> int:
    """R05 — dias úteis inclusive entre start e end (0 se end < start)."""
    if end < start:
        return 0

    total_days = (end - start).days + 1
    full_weeks, remaining = divmod(total_days, 7)
    count = full_weeks * 5

    cursor = start + timedelta(days=full_weeks * 7)
    for _ in range(remaining):
        if not is_weekend(cursor):
            count += 1
        cursor += timedelta(days=1)

    return count
