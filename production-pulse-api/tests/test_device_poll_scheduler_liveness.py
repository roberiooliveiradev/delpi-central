"""Resilience and liveness of DevicePollSchedulerService (RQ-01..04)."""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from production_pulse_app.application.services.device_poll_scheduler_service import (
    DevicePollSchedulerService,
    get_device_poll_scheduler,
    reset_device_poll_scheduler_for_tests,
    resolve_scheduler_liveness_stale_ms,
)
from production_pulse_app.config import settings
from production_pulse_app.infrastructure.content.device_validation_content_service import (
    load_device_validation_content,
    scheduler_liveness_stale_ms,
)
from production_pulse_app.main import app


@pytest.fixture(autouse=True)
def _reset_scheduler_singleton():
    yield
    reset_device_poll_scheduler_for_tests()


def test_scheduler_liveness_stale_ms_matches_content():
    load_device_validation_content.cache_clear()
    assert scheduler_liveness_stale_ms() == 30_000
    assert resolve_scheduler_liveness_stale_ms() == 30_000


def test_safe_tick_survives_tick_exception_and_updates_heartbeat():
    """Positive: exception in _tick does not prevent last_tick heartbeat."""
    scheduler = DevicePollSchedulerService()
    scheduler._tick = AsyncMock(side_effect=RuntimeError("list_due boom"))

    asyncio.run(scheduler._safe_tick())

    assert scheduler._last_tick_monotonic is not None
    snap = scheduler.liveness_snapshot()
    assert snap["lastTickAgeMs"] is not None
    assert snap["lastTickAgeMs"] < 5_000


def test_safe_tick_survives_distinct_tick_exception():
    """Sibling: a second failure class also keeps the heartbeat advancing."""
    scheduler = DevicePollSchedulerService()
    scheduler._tick = AsyncMock(side_effect=ConnectionError("ota path boom"))
    before = time.monotonic()

    asyncio.run(scheduler._safe_tick())

    assert scheduler._last_tick_monotonic is not None
    assert scheduler._last_tick_monotonic >= before


def test_liveness_healthy_when_scheduler_disabled(monkeypatch):
    """Negative: disabled scheduler never requires a running task."""
    monkeypatch.setattr(settings, "PP_POLL_SCHEDULER_ENABLED", False)
    scheduler = DevicePollSchedulerService()
    snap = scheduler.liveness_snapshot()
    assert snap["enabled"] is False
    assert snap["running"] is False
    assert snap["healthy"] is True


def test_liveness_unhealthy_when_enabled_and_not_running(monkeypatch):
    monkeypatch.setattr(settings, "PP_POLL_SCHEDULER_ENABLED", True)
    scheduler = DevicePollSchedulerService()
    snap = scheduler.liveness_snapshot()
    assert snap["enabled"] is True
    assert snap["running"] is False
    assert snap["healthy"] is False


def test_liveness_unhealthy_when_last_tick_stale(monkeypatch):
    monkeypatch.setattr(settings, "PP_POLL_SCHEDULER_ENABLED", True)
    monkeypatch.setattr(settings, "PP_SCHEDULER_LIVENESS_STALE_MS", 100)
    scheduler = DevicePollSchedulerService()

    async def _scenario() -> None:
        async def _noop() -> None:
            await asyncio.Event().wait()

        task = asyncio.create_task(_noop())
        scheduler._task = task
        scheduler._started_monotonic = time.monotonic() - 10
        scheduler._last_tick_monotonic = time.monotonic() - 5
        try:
            snap = scheduler.liveness_snapshot()
            assert snap["running"] is True
            assert snap["healthy"] is False
            assert snap["lastTickAgeMs"] is not None
            assert snap["lastTickAgeMs"] > 100
        finally:
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

    asyncio.run(_scenario())


def test_health_ok_when_scheduler_disabled(monkeypatch):
    monkeypatch.setattr(settings, "PP_POLL_SCHEDULER_ENABLED", False)
    reset_device_poll_scheduler_for_tests()
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "ok"
    assert body["data"]["scheduler"]["enabled"] is False
    assert body["data"]["scheduler"]["healthy"] is True


def test_health_503_when_scheduler_unhealthy(monkeypatch):
    monkeypatch.setattr(settings, "PP_POLL_SCHEDULER_ENABLED", False)
    reset_device_poll_scheduler_for_tests()
    scheduler = get_device_poll_scheduler()
    monkeypatch.setattr(
        scheduler,
        "liveness_snapshot",
        lambda: {
            "enabled": True,
            "running": False,
            "healthy": False,
            "lastTickAgeMs": None,
            "inFlightCount": 0,
            "staleThresholdMs": 30_000,
        },
    )
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 503
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "scheduler_unhealthy"
    assert body["error"]["details"]["scheduler"]["healthy"] is False
