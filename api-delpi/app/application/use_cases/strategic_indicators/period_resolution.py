from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ResolvedPeriod:
    competence: str
    start_date: str
    end_date: str


def resolve_period(
    *,
    competence: str | None,
    start_date: str | None,
    end_date: str | None,
) -> ResolvedPeriod:
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


def previous_competence(competence: str) -> str:
    year_str, month_str = competence.split("-")
    year = int(year_str)
    month = int(month_str)

    if month == 1:
        return f"{year - 1}-12"
    return f"{year}-{str(month - 1).zfill(2)}"


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
    if end_date and len(end_date) >= 10:
        _day, month, year = end_date.split("-")
        return f"{year}-{month}"
    if start_date and len(start_date) >= 10:
        _day, month, year = start_date.split("-")
        return f"{year}-{month}"
    return date.today().strftime("%Y-%m")