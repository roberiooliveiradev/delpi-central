# app/infrastructure/schedulers/notification_dispatch_scheduler.py

from __future__ import annotations

import logging
import threading
import time
from typing import TYPE_CHECKING

from app.application.services.process_pending_notification_dispatches_service import (
    run_process_pending_notification_dispatches,
)

if TYPE_CHECKING:
    from flask import Flask

logger = logging.getLogger(__name__)

_scheduler_started = False
_scheduler_lock = threading.Lock()


def _tick(app: Flask, *, batch_limit: int) -> None:
    with app.app_context():
        result = run_process_pending_notification_dispatches(limit=batch_limit)

    if result.processed:
        logger.info(
            "Notification dispatch scheduler: processed=%s completed=%s failed=%s",
            result.processed,
            result.completed,
            result.failed,
        )
    if result.errors:
        logger.warning(
            "Notification dispatch scheduler errors: %s",
            result.errors,
        )


def _scheduler_loop(app: Flask, *, poll_seconds: int, batch_limit: int) -> None:
    logger.info(
        "Notification dispatch scheduler started (poll=%ss, batch_limit=%s)",
        poll_seconds,
        batch_limit,
    )

    while True:
        try:
            _tick(app, batch_limit=batch_limit)
        except Exception:
            logger.exception("Notification dispatch scheduler tick failed")

        time.sleep(poll_seconds)


def start_notification_dispatch_scheduler(app: Flask) -> None:
    global _scheduler_started

    if app.config.get("TESTING"):
        return

    if not app.config.get("NOTIFICATIONS_DISPATCH_SCHEDULER_ENABLED", True):
        logger.info("Notification dispatch scheduler disabled by configuration")
        return

    poll_seconds = int(app.config.get("NOTIFICATIONS_DISPATCH_POLL_SECONDS", 60))
    batch_limit = int(app.config.get("NOTIFICATIONS_DISPATCH_BATCH_LIMIT", 20))

    with _scheduler_lock:
        if _scheduler_started:
            return
        _scheduler_started = True

    thread = threading.Thread(
        target=_scheduler_loop,
        args=(app,),
        kwargs={"poll_seconds": poll_seconds, "batch_limit": batch_limit},
        name="notification-dispatch-scheduler",
        daemon=True,
    )
    thread.start()
