from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

TERMINAL_PLAN_STATUSES = frozenset({"completed", "cancelled"})

# Dias corridos sem atualização do plano — limiar por severidade (Onda 4.6).
PLAN_SLA_DAYS_BY_SEVERITY: dict[str, dict[str, int]] = {
    "critical": {"warning": 3, "breach": 5},
    "high": {"warning": 5, "breach": 10},
    "medium": {"warning": 8, "breach": 15},
    "low": {"warning": 12, "breach": 20},
}

ACTION_DUE_SOON_DAYS = 2
CRITICAL_STALL_DAYS = PLAN_SLA_DAYS_BY_SEVERITY["critical"]["breach"]


def _as_utc_datetime(value: datetime | date | str | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, date):
        dt = datetime(value.year, value.month, value.day, tzinfo=timezone.utc)
    elif isinstance(value, str):
        cleaned = value.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(cleaned)
        except ValueError:
            return None
    else:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def calendar_days_since(
    value: datetime | date | str | None,
    *,
    reference: datetime | None = None,
) -> int:
    start = _as_utc_datetime(value)
    if start is None:
        return 0
    end = reference or datetime.now(timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    else:
        end = end.astimezone(timezone.utc)
    delta_days = (end.date() - start.date()).days
    return max(delta_days, 0)


def resolve_plan_sla(
    *,
    severity: str | None,
    status: str | None,
    updated_at: datetime | date | str | None,
    reference: datetime | None = None,
) -> dict[str, Any]:
    days = calendar_days_since(updated_at, reference=reference)
    level = "ok"
    warning_days = PLAN_SLA_DAYS_BY_SEVERITY["medium"]["warning"]
    breach_days = PLAN_SLA_DAYS_BY_SEVERITY["medium"]["breach"]

    if status not in TERMINAL_PLAN_STATUSES:
        thresholds = PLAN_SLA_DAYS_BY_SEVERITY.get(
            str(severity or "").lower(),
            PLAN_SLA_DAYS_BY_SEVERITY["medium"],
        )
        warning_days = thresholds["warning"]
        breach_days = thresholds["breach"]
        if days >= breach_days:
            level = "breached"
        elif days >= warning_days:
            level = "warning"

    return {
        "sla_level": level,
        "days_without_update": days,
        "sla_warning_days": warning_days,
        "sla_breach_days": breach_days,
    }


def resolve_action_due_sla(
    *,
    due_date: datetime | date | str | None,
    is_overdue: bool,
    reference: datetime | None = None,
) -> dict[str, Any]:
    if is_overdue:
        return {"due_sla_level": "overdue", "days_until_due": None}

    due = _as_utc_datetime(due_date)
    if due is None:
        return {"due_sla_level": "ok", "days_until_due": None}

    end = reference or datetime.now(timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    else:
        end = end.astimezone(timezone.utc)

    days_until = (due.date() - end.date()).days
    if days_until <= ACTION_DUE_SOON_DAYS:
        level = "due_soon"
    else:
        level = "ok"
    return {"due_sla_level": level, "days_until_due": days_until}


def enrich_plan_row_sla(row: dict[str, Any], *, reference: datetime | None = None) -> dict[str, Any]:
    sla = resolve_plan_sla(
        severity=row.get("severity"),
        status=row.get("status"),
        updated_at=row.get("updated_at"),
        reference=reference,
    )
    return {**row, **sla}
