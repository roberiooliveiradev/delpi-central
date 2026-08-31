"""Unit tests for integration jobs scheduler bootstrap helpers."""

from __future__ import annotations

import asyncio

from commercial_app.infrastructure.schedulers.integration_jobs_scheduler import (
    start_integration_jobs_scheduler,
    stop_integration_jobs_scheduler,
)


def test_scheduler_disabled_is_noop() -> None:
    async def _run() -> None:
        task = start_integration_jobs_scheduler(enabled=False, poll_seconds=60)
        assert task is None
        await stop_integration_jobs_scheduler()

    asyncio.run(_run())


def test_scheduler_runs_ticks(monkeypatch) -> None:
    calls: list[str] = []

    def ready() -> dict:
        calls.append("ready")
        return {
            "previousKeyCount": 0,
            "currentKeyCount": 0,
            "enteredCount": 0,
            "enqueued": 0,
            "outboxPublished": 0,
            "outboxFailed": 0,
        }

    def due() -> dict:
        calls.append("due")
        return {"enqueued": 0, "outboxPublished": 0, "outboxFailed": 0}

    from commercial_app.infrastructure.schedulers import integration_jobs_scheduler as mod

    async def _run() -> None:
        await stop_integration_jobs_scheduler()

        async def _fast_loop(*, poll_seconds: float, **_kwargs):
            await mod._tick(run_ready=ready, run_task_due=due)
            await asyncio.sleep(0.01)

        monkeypatch.setattr(mod, "_scheduler_loop", _fast_loop)
        task = start_integration_jobs_scheduler(enabled=True, poll_seconds=30)
        assert task is not None
        await asyncio.sleep(0.05)
        await stop_integration_jobs_scheduler()

    asyncio.run(_run())
    assert "ready" in calls
    assert "due" in calls
