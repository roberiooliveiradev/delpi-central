"""Periodic scan of commercial integration jobs (ready_to_invoice, task due).

Badge «Meus pedidos» grows from live open-orders; portal/toast notifications only
fire when these scans detect a delta and publish the outbox. Without a scheduler
the HTTP job endpoints stay idle and users never get notified.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)

_scheduler_task: asyncio.Task[None] | None = None


def _run_ready_to_invoice_scan() -> dict[str, Any]:
    from commercial_app.composition.commercial_composer import (
        build_scan_ready_to_invoice_notifications_use_case,
    )

    return build_scan_ready_to_invoice_notifications_use_case().execute()


def _run_task_due_scan() -> dict[str, Any]:
    from commercial_app.composition.commercial_composer import (
        build_scan_task_due_notifications_use_case,
    )

    return build_scan_task_due_notifications_use_case().execute()


async def _tick(
    *,
    run_ready: Callable[[], dict[str, Any]],
    run_task_due: Callable[[], dict[str, Any]],
) -> None:
    loop = asyncio.get_running_loop()
    try:
        ready = await loop.run_in_executor(None, run_ready)
        logger.info(
            "integration_jobs_ready_to_invoice_scan previous=%s current=%s entered=%s "
            "enqueued=%s published=%s failed=%s",
            ready.get("previousKeyCount"),
            ready.get("currentKeyCount"),
            ready.get("enteredCount"),
            ready.get("enqueued"),
            ready.get("outboxPublished"),
            ready.get("outboxFailed"),
        )
    except Exception:
        logger.exception("integration_jobs_ready_to_invoice_scan_failed")

    try:
        due = await loop.run_in_executor(None, run_task_due)
        logger.info(
            "integration_jobs_task_due_scan enqueued=%s published=%s failed=%s",
            due.get("enqueued"),
            due.get("outboxPublished"),
            due.get("outboxFailed"),
        )
    except Exception:
        logger.exception("integration_jobs_task_due_scan_failed")


async def _scheduler_loop(
    *,
    poll_seconds: float,
    run_ready: Callable[[], dict[str, Any]] | None = None,
    run_task_due: Callable[[], dict[str, Any]] | None = None,
) -> None:
    ready_fn = run_ready or _run_ready_to_invoice_scan
    due_fn = run_task_due or _run_task_due_scan
    logger.info(
        "integration_jobs_scheduler_started poll_seconds=%s",
        poll_seconds,
    )
    # First tick soon after boot so checkpoint seeds without waiting a full interval.
    await asyncio.sleep(min(15.0, max(1.0, poll_seconds)))
    while True:
        await _tick(run_ready=ready_fn, run_task_due=due_fn)
        await asyncio.sleep(poll_seconds)


def start_integration_jobs_scheduler(
    *,
    enabled: bool,
    poll_seconds: float,
) -> asyncio.Task[None] | None:
    """Start background loop; no-op when disabled or already running."""
    global _scheduler_task

    if not enabled:
        logger.info("integration_jobs_scheduler_disabled")
        return None
    if _scheduler_task is not None and not _scheduler_task.done():
        return _scheduler_task

    seconds = max(30.0, float(poll_seconds or 60.0))
    _scheduler_task = asyncio.create_task(
        _scheduler_loop(poll_seconds=seconds),
        name="commercial-integration-jobs-scheduler",
    )
    return _scheduler_task


async def stop_integration_jobs_scheduler() -> None:
    global _scheduler_task
    task = _scheduler_task
    _scheduler_task = None
    if task is None:
        return
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task
