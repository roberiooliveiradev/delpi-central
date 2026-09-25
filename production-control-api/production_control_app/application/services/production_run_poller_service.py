from __future__ import annotations

import asyncio
import logging

from production_control_app.config import settings

logger = logging.getLogger(__name__)


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
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("production_run_poller_stopped")

    async def _loop(self) -> None:
        from production_control_app.composition.pc_composer import build_production_run_service

        while not self._stopped.is_set():
            interval_ms = max(250, int(settings.PC_PRODUCTION_RUN_POLL_MS or 1000))
            try:
                service = build_production_run_service()
                await asyncio.to_thread(service.tick_running_runs)
            except Exception:  # noqa: BLE001
                logger.exception("production_run_poller_tick_failed")
            try:
                await asyncio.wait_for(self._stopped.wait(), timeout=interval_ms / 1000.0)
            except asyncio.TimeoutError:
                continue


production_run_poller = ProductionRunPollerService()
