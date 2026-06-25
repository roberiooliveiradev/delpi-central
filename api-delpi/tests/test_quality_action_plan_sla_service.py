from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.domain.services.quality_action_plans.quality_action_plan_sla_service import (
    ACTION_DUE_SOON_DAYS,
    CRITICAL_STALL_DAYS,
    PLAN_SLA_DAYS_BY_SEVERITY,
    calendar_days_since,
    resolve_action_due_sla,
    resolve_plan_sla,
)


def test_critical_stall_days_matches_playbook():
    assert CRITICAL_STALL_DAYS == PLAN_SLA_DAYS_BY_SEVERITY["critical"]["breach"] == 5


def test_resolve_plan_sla_ok_for_recent_critical():
    now = datetime(2026, 6, 25, 12, 0, tzinfo=timezone.utc)
    updated = now - timedelta(days=2)
    sla = resolve_plan_sla(
        severity="critical",
        status="in_progress",
        updated_at=updated,
        reference=now,
    )
    assert sla["sla_level"] == "ok"
    assert sla["days_without_update"] == 2


def test_resolve_plan_sla_warning_and_breach_for_critical():
    now = datetime(2026, 6, 25, 12, 0, tzinfo=timezone.utc)
    warning = resolve_plan_sla(
        severity="critical",
        status="in_progress",
        updated_at=now - timedelta(days=3),
        reference=now,
    )
    breach = resolve_plan_sla(
        severity="critical",
        status="in_progress",
        updated_at=now - timedelta(days=5),
        reference=now,
    )
    assert warning["sla_level"] == "warning"
    assert breach["sla_level"] == "breached"


def test_resolve_plan_sla_skips_terminal_status():
    now = datetime(2026, 6, 25, 12, 0, tzinfo=timezone.utc)
    sla = resolve_plan_sla(
        severity="critical",
        status="completed",
        updated_at=now - timedelta(days=30),
        reference=now,
    )
    assert sla["sla_level"] == "ok"


def test_resolve_action_due_soon_within_two_days():
    now = datetime(2026, 6, 25, 12, 0, tzinfo=timezone.utc)
    due = (now + timedelta(days=1)).date()
    sla = resolve_action_due_sla(due_date=due, is_overdue=False, reference=now)
    assert sla["due_sla_level"] == "due_soon"
    assert sla["days_until_due"] == 1


def test_resolve_action_overdue_takes_precedence():
    now = datetime(2026, 6, 25, 12, 0, tzinfo=timezone.utc)
    sla = resolve_action_due_sla(
        due_date=(now - timedelta(days=1)).date(),
        is_overdue=True,
        reference=now,
    )
    assert sla["due_sla_level"] == "overdue"


def test_calendar_days_since_handles_iso_string():
    days = calendar_days_since("2026-06-20T10:00:00+00:00", reference=datetime(2026, 6, 25, tzinfo=timezone.utc))
    assert days == 5


def test_action_due_soon_window_is_two_days():
    assert ACTION_DUE_SOON_DAYS == 2
