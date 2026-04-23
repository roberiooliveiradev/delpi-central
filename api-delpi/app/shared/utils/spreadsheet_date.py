# app/sahred/utils/spreadsheet_date.py

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any


EXCEL_EPOCH = date(1899, 12, 30)


def parse_spreadsheet_date(value: Any) -> date | None:
    """
    Converte valores vindos de planilhas para datetime.date.

    Suporta:
    - dd/mm/yyyy
    - dd-mm-yyyy
    - yyyy-mm-dd
    - yyyy/mm/dd
    - strings com hora
    - serial numérico do Excel (ex: 45567)
    - inteiros/floats/strings numéricas

    Retorna None se não for possível interpretar.
    """
    if value is None:
        return None

    if isinstance(value, date) and not isinstance(value, datetime):
        return value

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, (int, float)):
        return _parse_excel_serial(value)

    raw = str(value).strip()
    if not raw:
        return None

    numeric_date = _parse_numeric_string_as_excel_date(raw)
    if numeric_date is not None:
        return numeric_date

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

    for fmt in (
        "%d/%m/%Y %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d-%m-%Y %H:%M:%S",
    ):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            pass

    try:
        return datetime.fromisoformat(raw).date()
    except ValueError:
        return None


def spreadsheet_date_in_range(
    value: Any,
    *,
    start_date: str | date | None = None,
    end_date: str | date | None = None,
) -> bool:
    row_date = parse_spreadsheet_date(value)
    if row_date is None:
        return False

    start = _coerce_to_date(start_date)
    end = _coerce_to_date(end_date)

    if start is not None and row_date < start:
        return False
    if end is not None and row_date > end:
        return False
    return True


def format_date_ddmmyyyy(value: Any) -> str | None:
    parsed = parse_spreadsheet_date(value)
    if parsed is None:
        return None
    return parsed.strftime("%d/%m/%Y")


def format_date_yyyymmdd(value: Any) -> str | None:
    parsed = parse_spreadsheet_date(value)
    if parsed is None:
        return None
    return parsed.strftime("%Y%m%d")


def _coerce_to_date(value: str | date | None) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    return parse_spreadsheet_date(value)


def _parse_numeric_string_as_excel_date(raw: str) -> date | None:
    compact = raw.replace(",", ".").strip()

    try:
        numeric = Decimal(compact)
    except InvalidOperation:
        return None

    if numeric < 1:
        return None

    return _parse_excel_serial(float(numeric))


def _parse_excel_serial(value: int | float) -> date | None:
    try:
        days = int(float(value))
    except (TypeError, ValueError):
        return None

    if days <= 0:
        return None

    try:
        return EXCEL_EPOCH + timedelta(days=days)
    except OverflowError:
        return None