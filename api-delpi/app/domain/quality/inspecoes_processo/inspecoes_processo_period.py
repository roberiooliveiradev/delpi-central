"""Período de medições (QPR) — parse, lookback e kwargs do repositório."""

from __future__ import annotations

import calendar
from datetime import date

LOOKBACK_MONTHS = 12


def parse_optional_iso_date(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10]).isoformat()
    except ValueError as exc:
        raise ValueError(f"{field_name} inválida. Use YYYY-MM-DD.") from exc


def _months_ago(reference: date, months: int) -> date:
    year = reference.year
    month = reference.month - months
    while month <= 0:
        month += 12
        year -= 1
    day = min(reference.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def lookback_floor(today: date | None = None) -> str:
    """Limite inferior canônico: últimos 12 meses (inclusive)."""
    return _months_ago(today or date.today(), LOOKBACK_MONTHS).isoformat()


def resolve_optional_period(
    start_date: str | None,
    end_date: str | None,
    *,
    field_start: str = "start_date",
    field_end: str = "end_date",
    apply_lookback: bool = True,
    today: date | None = None,
) -> tuple[str | None, str | None]:
    """Normaliza período opcional. Sem datas → (None, None) = views pré-agregadas."""
    parsed_start = parse_optional_iso_date(start_date, field_start)
    parsed_end = parse_optional_iso_date(end_date, field_end)
    if parsed_start is None and parsed_end is None:
        return None, None
    if parsed_start and parsed_end and parsed_start > parsed_end:
        raise ValueError(f"{field_start} não pode ser maior que {field_end}.")
    if apply_lookback:
        floor = lookback_floor(today)
        if parsed_start is None or parsed_start < floor:
            parsed_start = floor
    return parsed_start, parsed_end


def period_repository_kwargs(
    start_date: str | None,
    end_date: str | None,
) -> dict[str, str | None]:
    if start_date or end_date:
        return {"start_date": start_date, "end_date": end_date}
    return {}
