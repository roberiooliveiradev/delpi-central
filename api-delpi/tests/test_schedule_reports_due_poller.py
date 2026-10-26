"""Unit — poller interno de agendas Delpi Reports."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.startup.schedule_reports_due_poller import (
    schedule_reports_due_poller_on_startup,
    stop_reports_due_poller_for_tests,
)


def test_poller_disabled_when_interval_zero(monkeypatch) -> None:
    monkeypatch.setenv("REPORTS_SCHEDULE_POLL_SECONDS", "0")
    with patch("app.startup.schedule_reports_due_poller.threading.Thread") as thread_cls:
        schedule_reports_due_poller_on_startup()
        thread_cls.assert_not_called()


def test_poller_starts_daemon_thread(monkeypatch) -> None:
    monkeypatch.setenv("REPORTS_SCHEDULE_POLL_SECONDS", "60")
    monkeypatch.setenv("REPORTS_SCHEDULE_POLL_LIMIT", "5")
    stop_reports_due_poller_for_tests()
    with patch("app.startup.schedule_reports_due_poller.threading.Thread") as thread_cls:
        fake = MagicMock()
        thread_cls.return_value = fake
        schedule_reports_due_poller_on_startup()
        thread_cls.assert_called_once()
        kwargs = thread_cls.call_args.kwargs
        assert kwargs["name"] == "reports-schedule-poller"
        assert kwargs["daemon"] is True
        fake.start.assert_called_once()
        stop_reports_due_poller_for_tests()
