from __future__ import annotations

import asyncio
import logging

from production_control_app.config import settings

logger = logging.getLogger(__name__)


def remaining_cycle_delay(interval_ms: int, elapsed_seconds: float) -> float:
    return max(0.0, interval_ms / 1000.0 - elapsed_seconds)


class ProductionRunPollerService:
    """Poll leve dos runs ``running`` — atualiza peças e emite WS hint."""

    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._stopped = asyncio.Event()

    async def start(self) -> None:
        if self._task is not None:
            return
        self._stopped.clear()
        self._task = asyncio.create_task(self._loop(), name="production-run-poller")
        logger.info("production_run_poller_started")

    async def stop(self) -> None:
        self._stopped.set()
        if self._task is not None:
            await self._task
            self._task = None
        logger.info("production_run_poller_stopped")

    async def _loop(self) -> None:
        from production_control_app.composition.pc_composer import build_production_run_service

        loop = asyncio.get_running_loop()
        while not self._stopped.is_set():
            cycle_started_at = loop.time()
            interval_ms = max(250, int(settings.PC_PRODUCTION_RUN_POLL_MS or 500))
            try:
                service = build_production_run_service()
                await asyncio.to_thread(service.tick_running_runs)
            except Exception:  # noqa: BLE001
                logger.exception("production_run_poller_tick_failed")
            delay = remaining_cycle_delay(interval_ms, loop.time() - cycle_started_at)
            if delay <= 0:
                continue
            try:
                await asyncio.wait_for(self._stopped.wait(), timeout=delay)
            except asyncio.TimeoutError:
                continue


production_run_poller = ProductionRunPollerService()
