"""Série temporal de ganhos financeiros vs investimento (painel Kaizômetro).

Regras alinhadas ao ``PostgresKaizenRepository.summary``:

- **Ganhos** (``savings``): kaizens ``implantado`` com ``daily_savings > 0``;
  em cada bucket, ``daily_savings × active_days_in_range`` (validade 1 ano,
  sem projetar dias futuros).
- **Investimento** (``investment``): soma de ``investment`` alocada no bucket
  da âncora ``COALESCE(date_committee_approved, date_implemented)`` — mesmo
  conjunto de ``period_rows`` do summary.
"""

from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Literal

from app.domain.services.kaizen.kaizen_indicator_eligibility import (
    quantity_anchor_from_row,
)
from app.domain.services.kaizen import kaizen_savings_validity

Granularity = Literal["day", "month"]


def _as_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _as_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _month_start(day: date) -> date:
    return day.replace(day=1)


def _month_end(day: date) -> date:
    return day.replace(day=monthrange(day.year, day.month)[1])


def _iter_day_buckets(start: date, end: date) -> list[tuple[str, date, date]]:
    buckets: list[tuple[str, date, date]] = []
    cursor = start
    while cursor <= end:
        key = cursor.isoformat()
        buckets.append((key, cursor, cursor))
        cursor += timedelta(days=1)
    return buckets


def _iter_month_buckets(start: date, end: date) -> list[tuple[str, date, date]]:
    buckets: list[tuple[str, date, date]] = []
    cursor = _month_start(start)
    last = _month_start(end)
    while cursor <= last:
        key = f"{cursor.year:04d}-{cursor.month:02d}"
        bucket_start = max(cursor, start)
        bucket_end = min(_month_end(cursor), end)
        buckets.append((key, bucket_start, bucket_end))
        if cursor.month == 12:
            cursor = date(cursor.year + 1, 1, 1)
        else:
            cursor = date(cursor.year, cursor.month + 1, 1)
    return buckets


def resolve_series_range(
    *,
    date_start: str | date | None,
    date_end: str | date | None,
    today: date | None = None,
) -> tuple[date, date]:
    """Intervalo efetivo da série (defaults: início do mês corrente → hoje)."""
    reference = today or date.today()
    start = _as_date(date_start) or _month_start(reference)
    end = _as_date(date_end) or reference
    if end < start:
        start, end = end, start
    return start, end


def build_savings_investment_series(
    rows: list[dict[str, Any]],
    *,
    granularity: Granularity = "month",
    date_start: str | date | None = None,
    date_end: str | date | None = None,
    branch_code: str | None = None,
    today: date | None = None,
) -> dict[str, Any]:
    """Agrega pontos ``{periodo, savings, investment}`` para o painel."""
    reference = today or date.today()
    start, end = resolve_series_range(
        date_start=date_start, date_end=date_end, today=reference
    )
    grain: Granularity = "day" if granularity == "day" else "month"
    buckets = (
        _iter_day_buckets(start, end)
        if grain == "day"
        else _iter_month_buckets(start, end)
    )

    savings_by_key = {key: 0.0 for key, _, _ in buckets}
    investment_by_key = {key: 0.0 for key, _, _ in buckets}

    for row in rows:
        if branch_code and str(row.get("branch_code") or "") != branch_code:
            continue

        status = row.get("status")
        implemented = _as_date(row.get("date_implemented"))
        daily = _as_float(row.get("daily_savings"))
        if status == "implantado" and daily > 0 and implemented is not None:
            for key, bucket_start, bucket_end in buckets:
                days = kaizen_savings_validity.active_days_in_range(
                    implemented,
                    bucket_start,
                    bucket_end,
                    today=reference,
                )
                if days:
                    savings_by_key[key] += daily * days

        anchor = quantity_anchor_from_row(row) or implemented
        if anchor is None:
            continue
        if anchor < start or anchor > end:
            continue
        investment = _as_float(row.get("investment"))
        if not investment:
            continue
        if grain == "day":
            key = anchor.isoformat()
        else:
            key = f"{anchor.year:04d}-{anchor.month:02d}"
        if key in investment_by_key:
            investment_by_key[key] += investment

    points = [
        {
            "periodo": key,
            "savings": round(savings_by_key[key], 2),
            "investment": round(investment_by_key[key], 2),
        }
        for key, _, _ in buckets
    ]
    total_savings = round(sum(point["savings"] for point in points), 2)
    total_investment = round(sum(point["investment"] for point in points), 2)

    return {
        "granularity": grain,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "branch_code": branch_code,
        "total_savings": total_savings,
        "total_investment": total_investment,
        "total": len(points),
        "points": points,
    }
