from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.domain.entities.kaizen.kaizen import Kaizen, KaizenDetail
from app.domain.services.kaizen.kaizen_indicator_eligibility import (
    quantity_anchor_from_row,
)
from app.domain.services.kaizen.kaizen_legacy_id import build_legacy_sheet_id


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


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_date(value: Any) -> str | None:
    parsed = _as_date(value)
    if parsed is None:
        return None
    return parsed.isoformat()


def _hours_saved_per_day(row: dict[str, Any]) -> float | None:
    seconds = _as_float(row.get("seconds_per_occurrence"))
    occurrences = _as_float(row.get("occurrences_per_day"))
    if seconds is None or occurrences is None:
        return None
    return round((seconds * occurrences) / 3600, 4)


def row_to_kaizen(row: dict[str, Any]) -> Kaizen:
    return Kaizen(
        id=str(row["id"]),
        title=str(row.get("title") or ""),
        date_implemented=_format_date(row.get("date_implemented")),
        status=row.get("status"),
        accountable=row.get("accountable"),
        sector=row.get("sector"),
        investment=_as_float(row.get("investment")),
        daily_savings=_as_float(row.get("daily_savings")),
        annual_savings=_as_float(row.get("annual_savings")),
        branch=row.get("branch_code"),
        quantity_date=_format_date(quantity_anchor_from_row(row)),
    )


def row_to_kaizen_detail(row: dict[str, Any]) -> KaizenDetail:
    return KaizenDetail(
        id=str(row["id"]),
        title=str(row.get("title") or ""),
        date_implemented=_format_date(row.get("date_implemented")),
        status=row.get("status"),
        accountable=row.get("accountable"),
        sector=row.get("sector"),
        investment=_as_float(row.get("investment")),
        daily_savings=_as_float(row.get("daily_savings")),
        annual_savings=_as_float(row.get("annual_savings")),
        branch=row.get("branch_code"),
        seconds_per_occurrence=_as_float(row.get("seconds_per_occurrence")),
        occurrences_per_day=_as_float(row.get("occurrences_per_day")),
        hourly_cost=_as_float(row.get("hourly_cost")),
        hours_saved_per_day=_hours_saved_per_day(row),
        quantity_date=_format_date(quantity_anchor_from_row(row)),
    )


def row_legacy_sheet_id(row: dict[str, Any]) -> str:
    return build_legacy_sheet_id(
        branch=row.get("branch_code"),
        date_implemented=_as_date(row.get("date_implemented")),
        title=row.get("title"),
    )
