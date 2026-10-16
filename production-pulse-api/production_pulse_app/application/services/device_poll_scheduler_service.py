from __future__ import annotations

import asyncio
import logging
import time
from typing import Any
from uuid import UUID

from production_pulse_app.application.services.device_poll_service import (
    DevicePollFailedError,
    DevicePollService,
)
from production_pulse_app.application.services.device_reading_retention_service import (
    DeviceReadingRetentionService,
)
from production_pulse_app.application.services.firmware_update_job_service import (
    FirmwareUpdateJobService,
)
from production_pulse_app.config import settings
from production_pulse_app.domain.services.device_poll_schedule_service import compute_next_poll_at
from production_pulse_app.infrastructure.content.device_validation_content_service import (
    scheduler_liveness_stale_ms,
    scheduler_tick_ms,
)
from production_pulse_app.infrastructure.content.telemetry_persistence_content_service import (
    purge_interval_ms,
)
from production_pulse_app.infrastructure.persistence.repositories.postgres_device_repository import (
    PostgresDeviceRepository,
)

logger = logging.getLogger(__name__)

_RECREATE_BACKOFF_SECONDS = 1.0


def resolve_scheduler_tick_seconds() -> float:
    """Tick do loop — content canônico, override opcional via env."""
    tick_ms = settings.PP_POLL_SCHEDULER_TICK_MS
    if tick_ms is None:
        tick_ms = scheduler_tick_ms()
    return max(0.01, float(tick_ms) / 1000.0)


def resolve_scheduler_liveness_stale_ms() -> int:
    stale_ms = settings.PP_SCHEDULER_LIVENESS_STALE_MS
    if stale_ms is None:
        stale_ms = scheduler_liveness_stale_ms()
    return max(1, int(stale_ms))


class DevicePollSchedulerService:
    def __init__(
        self,
        poll_service: DevicePollService | None = None,
        device_repository: PostgresDeviceRepository | None = None,
        retention_service: DeviceReadingRetentionService | None = None,
        *,
        max_concurrent_polls: int | None = None,
        tick_seconds: float | None = None,
    ) -> None:
        self._poll_service = poll_service or DevicePollService()
        self._devices = device_repository or PostgresDeviceRepository()
        self._retention = retention_service or DeviceReadingRetentionService()
        self._firmware_jobs = FirmwareUpdateJobService()
        self._max_concurrent = max_concurrent_polls or settings.PP_POLL_MAX_CONCURRENT
        self._tick_seconds = (
            tick_seconds if tick_seconds is not None else resolve_scheduler_tick_seconds()
        )
        self._semaphore = asyncio.Semaphore(max(1, self._max_concurrent))
        self._in_flight: set[UUID] = set()
        self._stop_event = asyncio.Event()
        self._task: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()
        self._last_purge_monotonic = 0.0
        self._purge_in_flight = False
        self._last_tick_monotonic: float | None = None
        self._started_monotonic: float | None = None
        self._recreate_scheduled = False

    @property
    def in_flight_device_ids(self) -> frozenset[UUID]:
        return frozenset(self._in_flight)

    def liveness_snapshot(self) -> dict[str, Any]:
        """Read-only scheduler liveness for /health (no side effects)."""
        enabled = bool(settings.PP_POLL_SCHEDULER_ENABLED)
        running = self._task is not None and not self._task.done()
        now = time.monotonic()
        last_tick_age_ms: int | None = None
        if self._last_tick_monotonic is not None:
            last_tick_age_ms = int(max(0.0, (now - self._last_tick_monotonic) * 1000.0))
        started_age_ms: int | None = None
        if self._started_monotonic is not None:
            started_age_ms = int(max(0.0, (now - self._started_monotonic) * 1000.0))
        stale_ms = resolve_scheduler_liveness_stale_ms()
        healthy = self._evaluate_healthy(
            enabled=enabled,
            running=running,
            last_tick_age_ms=last_tick_age_ms,
            started_age_ms=started_age_ms,
            stale_ms=stale_ms,
        )
        return {
            "enabled": enabled,
            "running": running,
            "healthy": healthy,
            "lastTickAgeMs": last_tick_age_ms,
            "inFlightCount": len(self._in_flight),
            "staleThresholdMs": stale_ms,
        }

    @staticmethod
    def _evaluate_healthy(
        *,
        enabled: bool,
        running: bool,
        last_tick_age_ms: int | None,
        started_age_ms: int | None,
        stale_ms: int,
    ) -> bool:
        if not enabled:
            return True
        if not running:
            return False
        if last_tick_age_ms is not None:
            return last_tick_age_ms <= stale_ms
        # Antes do 1º tick: healthy enquanto uptime < stale (boot grace).
        if started_age_ms is None:
            return True
        return started_age_ms <= stale_ms

    async def start(self) -> None:
        if self._task is not None and not self._task.done():
            return
        self._task = None
        initialized = await asyncio.to_thread(self._devices.initialize_missing_next_poll_at)
        if initialized:
            logger.info("Scheduler initialized next_poll_at for %s device(s).", initialized)
        self._stop_event.clear()
        self._started_monotonic = time.monotonic()
        self._recreate_scheduled = False
        self._task = asyncio.create_task(self._run_loop(), name="device-poll-scheduler")
        self._task.add_done_callback(self._on_task_done)

    async def stop(self) -> None:
        self._stop_event.set()
        task = self._task
        if task is not None:
            try:
                await task
            except asyncio.CancelledError:
                pass
            self._task = None

    def _on_task_done(self, task: asyncio.Task[None]) -> None:
        if self._stop_event.is_set():
            return
        if task.cancelled():
            return
        exc = task.exception()
        if exc is not None:
            logger.error(
                "Device poll scheduler task ended with error; scheduling recreate.",
                exc_info=(type(exc), exc, exc.__traceback__),
            )
        else:
            logger.error("Device poll scheduler task ended unexpectedly; scheduling recreate.")
        if self._recreate_scheduled:
            return
        self._recreate_scheduled = True
        self._task = None
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        loop.create_task(self._recreate_after_backoff(), name="device-poll-scheduler-recreate")

    async def _recreate_after_backoff(self) -> None:
        try:
            await asyncio.sleep(_RECREATE_BACKOFF_SECONDS)
            if self._stop_event.is_set():
                return
            await self.start()
        except Exception:
            logger.exception("Device poll scheduler recreate failed.")
        finally:
            self._recreate_scheduled = False

    async def _run_loop(self) -> None:
        logger.info(
            "Device poll scheduler started (max_concurrent=%s, tick_seconds=%s).",
            self._max_concurrent,
            self._tick_seconds,
        )
        try:
            while not self._stop_event.is_set():
                await self._safe_tick()
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=self._tick_seconds)
                except asyncio.TimeoutError:
                    continue
        finally:
            logger.info("Device poll scheduler stopped.")

    async def _safe_tick(self) -> None:
        try:
            await self._tick()
        except Exception:
            logger.exception("Device poll scheduler tick failed.")
        finally:
            self._last_tick_monotonic = time.monotonic()

    async def _tick(self) -> None:
        await self._maybe_purge_raw()
        await self._maybe_authorize_ota_jobs()
        await self._maybe_retry_ota_wakes()
        await self._maybe_recover_ota_targets()
        due_devices = await asyncio.to_thread(self._devices.list_due_for_scheduled_poll)
        for device in due_devices:
            device_id = device["id"]
            async with self._lock:
                if device_id in self._in_flight:
                    continue
                self._in_flight.add(device_id)
            asyncio.create_task(self._poll_device(device), name=f"poll-{device_id}")

    async def _maybe_authorize_ota_jobs(self) -> None:
        try:
            authorized = await asyncio.to_thread(self._firmware_jobs.authorize_due_scheduled)
            if authorized:
                logger.info("Authorized %s scheduled OTA job(s).", authorized)
        except Exception:
            logger.exception("Firmware OTA scheduled authorization failed.")

    async def _maybe_retry_ota_wakes(self) -> None:
        try:
            retried = await asyncio.to_thread(self._firmware_jobs.retry_authorized_ota_wakes)
            if retried:
                logger.info("Retried OTA wake for %s authorized target(s).", retried)
        except Exception:
            logger.exception("Firmware OTA wake retry failed.")

    async def _maybe_recover_ota_targets(self) -> None:
        try:
            stale = await asyncio.to_thread(self._firmware_jobs.fail_stale_open_targets)
            if stale:
                logger.info("Marked %s stale OTA target(s).", stale)
            reconciled = await asyncio.to_thread(
                self._firmware_jobs.reconcile_matching_installed_versions
            )
            if reconciled:
                logger.info("Reconciled %s OTA target(s) from installed version.", reconciled)
        except Exception:
            logger.exception("Firmware OTA target recovery failed.")

    async def _maybe_purge_raw(self) -> None:
        interval_s = purge_interval_ms() / 1000.0
        now = time.monotonic()
        if self._purge_in_flight:
            return
        if self._last_purge_monotonic and (now - self._last_purge_monotonic) < interval_s:
            return
        self._purge_in_flight = True
        self._last_purge_monotonic = now

        async def _run() -> None:
            try:
                await asyncio.to_thread(self._retention.purge_expired_raw)
            except Exception:
                logger.exception("Raw readings retention purge failed.")
            finally:
                self._purge_in_flight = False

        asyncio.create_task(_run(), name="readings-raw-purge")

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
