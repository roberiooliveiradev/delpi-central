from __future__ import annotations

import asyncio
import logging
from typing import Any
from uuid import UUID

from production_pulse_app.application.services.device_poll_service import (
    DevicePollFailedError,
    DevicePollService,
)
from production_pulse_app.config import settings
from production_pulse_app.domain.services.device_poll_schedule_service import compute_next_poll_at
from production_pulse_app.infrastructure.content.device_validation_content_service import (
    scheduler_tick_ms,
)
from production_pulse_app.infrastructure.persistence.repositories.postgres_device_repository import (
    PostgresDeviceRepository,
)

logger = logging.getLogger(__name__)


def resolve_scheduler_tick_seconds() -> float:
    """Tick do loop — content canônico, override opcional via env."""
    tick_ms = settings.PP_POLL_SCHEDULER_TICK_MS
    if tick_ms is None:
        tick_ms = scheduler_tick_ms()
    return max(0.01, float(tick_ms) / 1000.0)


class DevicePollSchedulerService:
    def __init__(
        self,
        poll_service: DevicePollService | None = None,
        device_repository: PostgresDeviceRepository | None = None,
        *,
        max_concurrent_polls: int | None = None,
        tick_seconds: float | None = None,
    ) -> None:
        self._poll_service = poll_service or DevicePollService()
        self._devices = device_repository or PostgresDeviceRepository()
        self._max_concurrent = max_concurrent_polls or settings.PP_POLL_MAX_CONCURRENT
        self._tick_seconds = (
            tick_seconds if tick_seconds is not None else resolve_scheduler_tick_seconds()
        )
        self._semaphore = asyncio.Semaphore(max(1, self._max_concurrent))
        self._in_flight: set[UUID] = set()
        self._stop_event = asyncio.Event()
        self._task: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()

    @property
    def in_flight_device_ids(self) -> frozenset[UUID]:
        return frozenset(self._in_flight)

    async def start(self) -> None:
        if self._task is not None:
            return
        initialized = await asyncio.to_thread(self._devices.initialize_missing_next_poll_at)
        if initialized:
            logger.info("Scheduler initialized next_poll_at for %s device(s).", initialized)
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run_loop(), name="device-poll-scheduler")

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task is not None:
            await self._task
            self._task = None

    async def _run_loop(self) -> None:
        logger.info(
            "Device poll scheduler started (max_concurrent=%s, tick_seconds=%s).",
            self._max_concurrent,
            self._tick_seconds,
        )
        try:
            while not self._stop_event.is_set():
                await self._tick()
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=self._tick_seconds)
                except asyncio.TimeoutError:
                    continue
        finally:
            logger.info("Device poll scheduler stopped.")

    async def _tick(self) -> None:
        due_devices = await asyncio.to_thread(self._devices.list_due_for_scheduled_poll)
        for device in due_devices:
            device_id = device["id"]
            async with self._lock:
                if device_id in self._in_flight:
                    continue
                self._in_flight.add(device_id)
            asyncio.create_task(self._poll_device(device), name=f"poll-{device_id}")

    async def _poll_device(self, device: dict[str, Any]) -> None:
        device_id = device["id"]
        async with self._semaphore:
            try:
                await asyncio.to_thread(
                    self._poll_service.poll_and_persist,
                    device_id,
                    source="poll",
                )
            except DevicePollFailedError as exc:
                logger.debug("Scheduled poll failed for %s: %s", device_id, exc)
            finally:
                await asyncio.to_thread(self._schedule_next, device)
                async with self._lock:
                    self._in_flight.discard(device_id)

    def _schedule_next(self, device: dict[str, Any]) -> None:
        next_at = compute_next_poll_at(float(device["poll_interval_ms"]))
        self._devices.update_next_poll_at(device["id"], next_poll_at=next_at)


_scheduler: DevicePollSchedulerService | None = None


def get_device_poll_scheduler() -> DevicePollSchedulerService:
    global _scheduler
    if _scheduler is None:
        _scheduler = DevicePollSchedulerService()
    return _scheduler


def reset_device_poll_scheduler_for_tests() -> None:
    global _scheduler
    _scheduler = None
