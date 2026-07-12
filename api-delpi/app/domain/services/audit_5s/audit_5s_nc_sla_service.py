from __future__ import annotations

from datetime import date, datetime
from typing import Any

ACTION_DUE_SOON_DAYS = 2
TERMINAL_NC_STATUSES = frozenset({"closed", "cancelled"})


def _as_date(value: date | datetime | str | None) -> date | None:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return None
        try:
            return date.fromisoformat(cleaned[:10])
        except ValueError:
            return None
    return None


def is_nc_plan_complete(row: dict[str, Any]) -> bool:
    description = str(row.get("description") or "").strip()
    root_cause = str(row.get("root_cause") or "").strip()
    corrective_action = str(row.get("corrective_action") or "").strip()
    responsible_name = str(row.get("responsible_name") or "").strip()
    due_date = row.get("due_date")
    return (
        len(description) >= 3
        and len(root_cause) >= 3
        and len(corrective_action) >= 3
        and len(responsible_name) >= 2
        and bool(due_date)
    )


def resolve_nc_due_sla(
    *,
    status: str | None,
    due_date: date | datetime | str | None,
    reference: date | None = None,
) -> dict[str, Any]:
    ref = reference or date.today()
    normalized_status = str(status or "").strip().lower()
    if normalized_status in TERMINAL_NC_STATUSES:
        return {"due_sla_level": "none", "days_until_due": None}

    due = _as_date(due_date)
    if due is None:
        return {"due_sla_level": "none", "days_until_due": None}

    days_until_due = (due - ref).days
    if days_until_due < 0:
        level = "overdue"
    elif days_until_due <= ACTION_DUE_SOON_DAYS:
        level = "due_soon"
    else:
        level = "ok"
    return {"due_sla_level": level, "days_until_due": days_until_due}


def resolve_nc_workflow(
    *,
    status: str | None,
    plan_complete: bool,
    has_before_evidence: bool,
    has_after_evidence: bool,
) -> dict[str, Any]:
    normalized_status = str(status or "").strip().lower()
    if normalized_status == "closed":
        return {"plan_started": True, "workflow_step": 3}

    plan_started = normalized_status != "open" or plan_complete
    if not plan_complete:
        return {"plan_started": plan_started, "workflow_step": 1}
    if not (has_before_evidence and has_after_evidence):
        return {"plan_started": True, "workflow_step": 2}
    return {"plan_started": True, "workflow_step": 3}
