# app/infrastructure/schedulers/notification_dispatch_scheduler.py

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.application.services.process_pending_notification_dispatches_service import (
    run_process_pending_notification_dispatches,
)
from app.extensions.socket import socketio

if TYPE_CHECKING:
    from flask import Flask

logger = logging.getLogger(__name__)

_scheduler_started = False


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

        socketio.sleep(poll_seconds)


def start_notification_dispatch_scheduler(app: Flask) -> None:
    global _scheduler_started

    if app.config.get("TESTING"):
        return

    if not app.config.get("NOTIFICATIONS_DISPATCH_SCHEDULER_ENABLED", True):
        logger.info("Notification dispatch scheduler disabled by configuration")
        return

    poll_seconds = int(app.config.get("NOTIFICATIONS_DISPATCH_POLL_SECONDS", 60))
    batch_limit = int(app.config.get("NOTIFICATIONS_DISPATCH_BATCH_LIMIT", 20))

    if _scheduler_started:
        return
    _scheduler_started = True

    socketio.start_background_task(
        _scheduler_loop,
        app,
        poll_seconds=poll_seconds,
        batch_limit=batch_limit,
    )
