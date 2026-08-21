"""Views do volume de produção na gestão à vista do PCP.

``day`` — mês corrente, série diária (default).
``month_yoy`` — jan→hoje do ano, buckets mensais + mesmo período do ano anterior.
"""

from __future__ import annotations

from calendar import monthrange
from datetime import date
from typing import Any, Literal

VolumeView = Literal["day", "month_yoy"]

VOLUME_VIEWS: frozenset[str] = frozenset({"day", "month_yoy"})

_MONTH_LABELS_PT = (
    "jan",
    "fev",
    "mar",
    "abr",
    "mai",
    "jun",
    "jul",
    "ago",
    "set",
    "out",
    "nov",
    "dez",
)


def parse_volume_view(raw: str | None) -> VolumeView:
    value = str(raw or "").strip().lower()
    if value in VOLUME_VIEWS:
        return value  # type: ignore[return-value]
    return "day"


def year_to_date_bounds(*, today: date) -> tuple[date, date]:
    """1º de janeiro do ano até ``today``."""
    return date(today.year, 1, 1), today


def shift_date_by_years(day: date, years: int) -> date:
    """Desloca o calendário por anos inteiros; clampa 29/02 em ano não bissexto."""
    target_year = day.year + years
    last_day = monthrange(target_year, day.month)[1]
    return date(target_year, day.month, min(day.day, last_day))


def shift_bounds_by_years(start: date, end: date, years: int) -> tuple[date, date]:
    return shift_date_by_years(start, years), shift_date_by_years(end, years)


def _month_number(point: dict[str, Any]) -> int | None:
    for key in ("start_date", "appointment_date", "periodo"):
        text = str(point.get(key) or "").strip()
        if len(text) >= 7 and text[4] == "-":
            try:
                return int(text[5:7])
            except ValueError:
                continue
        if len(text) >= 6 and text[:4].isdigit() and text[4:6].isdigit() and "-" not in text[:6]:
            # YYYYMM…
            try:
                return int(text[4:6])
            except ValueError:
                continue
    return None


def _qty(point: dict[str, Any]) -> float:
    try:
        value = float(point.get("qty_produced") if "qty_produced" in point else point.get("value"))
    except (TypeError, ValueError):
        return 0.0
    if value != value:  # NaN
        return 0.0
    return value


def index_by_month(points: list[dict[str, Any]]) -> dict[int, float]:
    """Soma qty por mês civil (1–12)."""
    out: dict[int, float] = {}
    for point in points:
        month = _month_number(point)
        if month is None or month < 1 or month > 12:
            continue
        out[month] = out.get(month, 0.0) + _qty(point)
    return out


def build_month_yoy_series(
    *,
    current_points: list[dict[str, Any]],
    prior_points: list[dict[str, Any]],
    year: int,
    through_month: int,
) -> list[dict[str, Any]]:
    """Uma linha por mês de jan até ``through_month``, com valor atual e do ano anterior."""
    current = index_by_month(current_points)
    prior = index_by_month(prior_points)
    last = max(1, min(12, through_month))
    rows: list[dict[str, Any]] = []
    for month in range(1, last + 1):
        label = _MONTH_LABELS_PT[month - 1]
        value = round(current.get(month, 0.0), 6)
        prior_value = round(prior.get(month, 0.0), 6)
        rows.append(
            {
                "label": label,
                "value": value,
                "prior_value": prior_value,
                "start_date": f"{year}-{month:02d}-01",
                "end_date": f"{year}-{month:02d}-{monthrange(year, month)[1]:02d}",
            }
        )
    return rows
