from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class ResolvedPeriod:
    competence: str
    start_date: str
    end_date: str


def normalize_dashboard_period_date(value: str | None) -> str | None:
    """Aceita DD-MM-YYYY (padrão Delpi) ou YYYY-MM-DD (inputs HTML)."""
    if value is None:
        return None

    trimmed = value.strip()
    if not trimmed:
        return None

    parts = _parse_dashboard_date_parts(trimmed)
    if parts is None:
        return trimmed

    day, month, year = parts
    return f"{str(day).zfill(2)}-{str(month).zfill(2)}-{year}"


def _parse_dashboard_date_parts(value: str) -> tuple[int, int, int] | None:
    parts = value.split("-")
    if len(parts) != 3:
        return None

    first, second, third = parts
    if len(first) == 4:
        try:
            return int(third), int(second), int(first)
        except ValueError:
            return None

    try:
        return int(first), int(second), int(third)
    except ValueError:
        return None


def resolve_period(
    *,
    competence: str | None,
    start_date: str | None,
    end_date: str | None,
) -> ResolvedPeriod:
    start_date = normalize_dashboard_period_date(start_date)
    end_date = normalize_dashboard_period_date(end_date)

    resolved_competence = competence or _resolve_competence_from_dates(
        start_date=start_date,
        end_date=end_date,
    )

    if start_date and end_date:
        return ResolvedPeriod(
            competence=resolved_competence,
            start_date=start_date,
            end_date=end_date,
        )

    month_start, month_end = build_month_range(resolved_competence)

    return ResolvedPeriod(
        competence=resolved_competence,
        start_date=start_date or month_start,
        end_date=end_date or month_end,
    )


def previous_period(period: ResolvedPeriod) -> ResolvedPeriod:
    previous_comp = previous_competence(period.competence)
    start_date, end_date = build_month_range(previous_comp)

    return ResolvedPeriod(
        competence=previous_comp,
        start_date=start_date,
        end_date=end_date,
    )


def current_competence() -> str:
    return date.today().strftime("%Y-%m")


def previous_competence(competence: str) -> str:
    year_str, month_str = competence.split("-")
    year = int(year_str)
    month = int(month_str)

    if month == 1:
        return f"{year - 1}-12"
    return f"{year}-{str(month - 1).zfill(2)}"


def is_standard_competence_period(period: ResolvedPeriod) -> bool:
    expected_start, expected_end = build_month_range(period.competence)
    return period.start_date == expected_start and period.end_date == expected_end


def build_trend_periods(
    *,
    reference_competence: str | None = None,
    months: int = 6,
) -> list[ResolvedPeriod]:
    reference = _parse_competence_date(reference_competence)
    resolved_months = max(2, min(months, 12))
    periods: list[ResolvedPeriod] = []

    year = reference.year
    month = reference.month

    for offset in range(resolved_months - 1, -1, -1):
        current_year = year
        current_month = month - offset

        while current_month <= 0:
            current_month += 12
            current_year -= 1

        while current_month > 12:
            current_month -= 12
            current_year += 1

        competence = f"{current_year}-{str(current_month).zfill(2)}"
        first_day = f"01-{str(current_month).zfill(2)}-{current_year}"
        last_day = monthrange(current_year, current_month)[1]
        last_date = (
            f"{str(last_day).zfill(2)}-{str(current_month).zfill(2)}-{current_year}"
        )

        periods.append(
            ResolvedPeriod(
                competence=competence,
                start_date=first_day,
                end_date=last_date,
            )
        )

    return periods


def competence_reference_date(
    *,
    competence: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> date:
    """Último dia do mês da competência (ou hoje) para filtrar vigência de metas."""
    if competence:
        parsed = _parse_competence_date(competence)
        last_day = monthrange(parsed.year, parsed.month)[1]
        return date(parsed.year, parsed.month, last_day)

    for value in (end_date, start_date):
        normalized = normalize_dashboard_period_date(value)
        parts = _parse_dashboard_date_parts(normalized) if normalized else None
        if parts:
            day, month, year = parts
            return date(year, month, day)

    return date.today()


def _parse_competence_date(competence: str | None) -> date:
    if competence:
        year_str, month_str = competence.split("-")
        return date(int(year_str), int(month_str), 1)

    today = date.today()
    return date(today.year, today.month, 1)


def build_month_range(competence: str) -> tuple[str, str]:
    year_str, month_str = competence.split("-")
    year = int(year_str)
    month = int(month_str)

    first_day = f"01-{str(month).zfill(2)}-{year}"
    last_day = monthrange(year, month)[1]
    last_date = f"{str(last_day).zfill(2)}-{str(month).zfill(2)}-{year}"
    return first_day, last_date


def _resolve_competence_from_dates(
    *,
    start_date: str | None,
    end_date: str | None,
) -> str:
    for value in (end_date, start_date):
        normalized = normalize_dashboard_period_date(value)
        parts = _parse_dashboard_date_parts(normalized) if normalized else None
        if parts:
            _day, month, year = parts
            return f"{year}-{str(month).zfill(2)}"
    return date.today().strftime("%Y-%m")