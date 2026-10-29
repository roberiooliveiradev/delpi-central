"""PROC-0076 R10 — scheduled ingestion runtime.

Pure-logic coverage for ``app.jobs.ingest_scheduler``: due
semantics (once-per-day attempt, interval-gated success, manual
attempt suppression, pre-run_at gating), per-feed interval env
override and the tick wiring (unknown feeds skipped, disabled
scheduling inert). No DB, no upstream — repository and runner are
fakes.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, time as dtime
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.jobs import ingest_scheduler as sched

RUN_AT = dtime(hour=20, minute=30)
NOW = datetime(2026, 10, 29, 21, 0)  # after RUN_AT


def _dt(day: int, hour: int = 4, minute: int = 0) -> datetime:
    return datetime(2026, 10, day, hour, minute)


# --- feed_due ---------------------------------------------------------------

def test_due_when_never_attempted_after_run_at():
    assert sched.feed_due(
        now=NOW,
        last_attempt_at=None,
        last_success_at=None,
        interval_days=3,
        run_at=RUN_AT,
    ) is True


def test_not_due_before_run_at():
    assert sched.feed_due(
        now=NOW.replace(hour=9, minute=0),
        last_attempt_at=None,
        last_success_at=None,
        interval_days=3,
        run_at=RUN_AT,
    ) is False


def test_not_due_when_attempted_today_failure_or_success():
    for attempt in (_dt(29, 4), _dt(29, 23)):
        assert sched.feed_due(
            now=NOW,
            last_attempt_at=attempt,
            last_success_at=None,
            interval_days=3,
            run_at=RUN_AT,
        ) is False


def test_due_next_day_after_failed_attempt():
    assert sched.feed_due(
        now=NOW + timedelta(days=1),
        last_attempt_at=_dt(29, 21),
        last_success_at=_dt(26, 20),
        interval_days=3,
        run_at=RUN_AT,
    ) is True


def test_not_due_within_interval_after_success():
    # success on the 27th, interval 3 → due again on the 30th
    for day in (28, 29):
        assert sched.feed_due(
            now=NOW.replace(day=day),
            last_attempt_at=_dt(27, 21),
            last_success_at=_dt(27, 21),
            interval_days=3,
            run_at=RUN_AT,
        ) is False


def test_due_when_interval_elapsed():
    assert sched.feed_due(
        now=NOW.replace(day=30),
        last_attempt_at=_dt(27, 21),
        last_success_at=_dt(27, 21),
        interval_days=3,
        run_at=RUN_AT,
    ) is True


def test_manual_attempt_today_suppresses_scheduled_run():
    # a manual recovery run earlier today already consumed upstream
    # weight — the scheduler must not repeat it.
    assert sched.feed_due(
        now=NOW,
        last_attempt_at=_dt(29, 4, 48),
        last_success_at=_dt(29, 4, 48),
        interval_days=3,
        run_at=RUN_AT,
    ) is False


def test_invalid_run_at_fails_closed():
    assert sched._parse_run_at("garbage") == dtime(hour=20, minute=30)
    assert sched._parse_run_at("25:99") == dtime(hour=20, minute=30)
    assert sched._parse_run_at("06:15") == dtime(hour=6, minute=15)


# --- interval resolution ------------------------------------------------------

def test_interval_default_and_env_override(monkeypatch):
    monkeypatch.delenv(
        "EXTERNAL_DATA_SCHEDULER_METALS_DAILY_INTERVAL_DAYS",
        raising=False,
    )
    assert sched._interval_days("metals-daily") == max(
        1, sched.Settings.EXTERNAL_DATA_SCHEDULER_INTERVAL_DAYS
    )
    monkeypatch.setenv(
        "EXTERNAL_DATA_SCHEDULER_METALS_DAILY_INTERVAL_DAYS", "7"
    )
    assert sched._interval_days("metals-daily") == 7
    monkeypatch.setenv(
        "EXTERNAL_DATA_SCHEDULER_METALS_DAILY_INTERVAL_DAYS", "oops"
    )
    assert sched._interval_days("metals-daily") == max(
        1, sched.Settings.EXTERNAL_DATA_SCHEDULER_INTERVAL_DAYS
    )


# --- _tick wiring -------------------------------------------------------------

class _FakeRepo:
    def __init__(self, statuses):
        self._statuses = statuses

    def feed_statuses(self):
        return list(self._statuses)


def test_tick_runs_due_feed_and_skips_fresh_one():
    ran: list[str] = []
    repo = _FakeRepo(
        [
            {
                "feed": "metals-daily",
                "last_run_started_at": _dt(25, 21),
                "last_successful_at": _dt(25, 21),
            }
        ]
    )
    sched._tick(
        repo=repo,
        feeds=("metals-daily",),
        now=NOW,
        run_at=RUN_AT,
        runner=ran.append,
    )
    assert ran == ["metals-daily"]


def test_tick_skips_feed_attempted_today():
    ran: list[str] = []
    repo = _FakeRepo(
        [
            {
                "feed": "metals-daily",
                "last_run_started_at": _dt(29, 4),
                "last_successful_at": None,
            }
        ]
    )
    sched._tick(
        repo=repo,
        feeds=("metals-daily",),
        now=NOW,
        run_at=RUN_AT,
        runner=ran.append,
    )
    assert ran == []


def test_tick_skips_unknown_feed(caplog):
    ran: list[str] = []
    repo = _FakeRepo([])
    with caplog.at_level("WARNING"):
        sched._tick(
            repo=repo,
            feeds=("not-a-feed",),
            now=NOW,
            run_at=RUN_AT,
            runner=ran.append,
        )
    assert ran == []
    assert "scheduler_unknown_feed" in caplog.text
