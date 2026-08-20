from __future__ import annotations

from datetime import date, datetime, timedelta
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


def forward_window_bounds(
    *,
    timezone: str,
    days: int,
    today: date | None = None,
) -> tuple[date, date]:
    """Hoje até hoje + N dias — janela de programação olhando para frente."""
    if today is None:
        today = today_in_timezone(timezone)
    return today, today + timedelta(days=max(0, days))
