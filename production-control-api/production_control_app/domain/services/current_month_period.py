from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo


def today_in_timezone(timezone: str) -> date:
    """Hoje no fuso operacional, com fallback para o fuso do host."""
    try:
        return datetime.now(ZoneInfo(timezone)).date()
    except Exception:
        return date.today()


def current_month_bounds(*, timezone: str, today: date | None = None) -> tuple[date, date]:
    """Primeiro dia do mês até hoje no fuso operacional (mês corrente)."""
    if today is None:
        today = today_in_timezone(timezone)
    start = today.replace(day=1)
    return start, today


def parse_iso_date(value: str | None) -> date | None:
    text = (value or "").strip()
    if len(text) != 10 or text[4] != "-" or text[7] != "-":
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def resolve_overview_period(
    *,
    timezone: str,
    today: date | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> tuple[date, date]:
    """Período explícito (ISO) ou mês corrente até hoje. Inválido/invertido → default."""
    default_start, default_end = current_month_bounds(timezone=timezone, today=today)
    parsed_start = parse_iso_date(start_date)
    parsed_end = parse_iso_date(end_date)
    if parsed_start is None or parsed_end is None:
        return default_start, default_end
    if parsed_start > parsed_end:
        return default_start, default_end
    return parsed_start, parsed_end
