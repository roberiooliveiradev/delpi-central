"""Contagem de dias por mês/recorte para prorrata do Transformômetro (dias corridos por padrão)."""

from __future__ import annotations

import calendar
from datetime import date, datetime, timedelta
from typing import Optional

# Desativado: quando True, conta só seg–sex e desconta feriados nacionais.
USE_ONLY_BUSINESS_DAYS = False

if USE_ONLY_BUSINESS_DAYS:
    from tm_app.core.brazil_national_holidays import is_national_holiday


def is_counted_day(value: date) -> bool:
    if not USE_ONLY_BUSINESS_DAYS:
        return True
    return value.weekday() < 5 and not is_national_holiday(value)


def is_business_day(value: date) -> bool:
    """Alias legado — respeita USE_ONLY_BUSINESS_DAYS."""
    return is_counted_day(value)


def count_days_in_range(start: date, end: date) -> int:
    if end < start:
        return 0
    total = 0
    current = start
    while current <= end:
        if is_counted_day(current):
            total += 1
        current += timedelta(days=1)
    return total


def count_business_days(start: date, end: date) -> int:
    return count_days_in_range(start, end)


def days_in_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def business_days_in_month(year: int, month: int) -> int:
    last = days_in_month(year, month)
    return count_days_in_range(date(year, month, 1), date(year, month, last))


def parse_competencia_month(competencia: str) -> Optional[date]:
    try:
        return datetime.strptime(str(competencia).strip()[:7], "%Y-%m").date()
    except (ValueError, TypeError):
        return None


def days_overlap_in_competencia(
    competencia: str,
    range_start: date,
    range_end: date,
) -> int:
    month_start = parse_competencia_month(competencia)
    if month_start is None:
        return 0

    year = month_start.year
    month = month_start.month
    month_end = date(year, month, days_in_month(year, month))
    overlap_start = max(range_start, month_start)
    overlap_end = min(range_end, month_end)
    return count_days_in_range(overlap_start, overlap_end)


def business_days_overlap_in_competencia(
    competencia: str,
    range_start: date,
    range_end: date,
) -> int:
    return days_overlap_in_competencia(competencia, range_start, range_end)


def day_fraction_in_competencia_range(
    competencia: str,
    start_date: Optional[str],
    end_date: Optional[str],
    *,
    uses_day_level_filter: bool,
) -> float:
    """Fração dos dias do mês (corridos) incluída no recorte YYYY-MM-DD … YYYY-MM-DD."""
    if not uses_day_level_filter:
        return 1.0

    month_start = parse_competencia_month(competencia)
    if month_start is None:
        return 1.0

    try:
        start_obj = datetime.strptime(str(start_date).strip()[:10], "%Y-%m-%d").date()
        end_obj = datetime.strptime(str(end_date).strip()[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return 1.0

    year = month_start.year
    month = month_start.month
    month_days = business_days_in_month(year, month)
    if month_days <= 0:
        return 0.0

    overlap = days_overlap_in_competencia(competencia, start_obj, end_obj)
    return overlap / month_days


def business_day_fraction_in_competencia_range(
    competencia: str,
    start_date: Optional[str],
    end_date: Optional[str],
    *,
    uses_day_level_filter: bool,
) -> float:
    return day_fraction_in_competencia_range(
        competencia,
        start_date,
        end_date,
        uses_day_level_filter=uses_day_level_filter,
    )


def total_days_for_competencias(
    competencias: set[str] | list[str],
    *,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    uses_day_level_filter: bool,
) -> float:
    total = 0.0
    unique = sorted({str(c).strip()[:7] for c in competencias if c})
    if not unique:
        return 0.0

    if uses_day_level_filter and start_date and end_date:
        try:
            start_obj = datetime.strptime(str(start_date).strip()[:10], "%Y-%m-%d").date()
            end_obj = datetime.strptime(str(end_date).strip()[:10], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            uses_day_level_filter = False
        else:
            for competencia in unique:
                total += days_overlap_in_competencia(competencia, start_obj, end_obj)
            return total

    for competencia in unique:
        month_start = parse_competencia_month(competencia)
        if month_start is None:
            continue
        total += business_days_in_month(month_start.year, month_start.month)

    return total


def total_business_days_for_competencias(
    competencias: set[str] | list[str],
    *,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    uses_day_level_filter: bool,
) -> float:
    return total_days_for_competencias(
        competencias,
        start_date=start_date,
        end_date=end_date,
        uses_day_level_filter=uses_day_level_filter,
    )


def business_month_calendar_factor(year: int, month: int) -> float:
    """Com dias corridos ativos, não reduz o valor mensal da medição."""
    if not USE_ONLY_BUSINESS_DAYS:
        return 1.0
    calendar_days = days_in_month(year, month)
    if calendar_days <= 0:
        return 1.0
    return business_days_in_month(year, month) / calendar_days
