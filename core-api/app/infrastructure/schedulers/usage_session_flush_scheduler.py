# app/infrastructure/schedulers/usage_session_flush_scheduler.py

from __future__ import annotations

import logging

from flask import Flask

from app.application.services.usage_session_flush_service import (
    flush_stale_usage_sessions,
)
from app.extensions.socket import socketio

logger = logging.getLogger(__name__)

_scheduler_started = False


def _scheduler_loop(app: Flask, *, poll_seconds: int) -> None:
    logger.info(
        "Usage session flush scheduler started (poll=%ss)",
        poll_seconds,
    )
    while True:
        try:
            with app.app_context():
                flushed = flush_stale_usage_sessions()
                if flushed:
                    logger.debug("usage_session_flush flushed=%s", flushed)
        except Exception:
            logger.exception("Usage session flush scheduler tick failed")
        socketio.sleep(poll_seconds)


def start_usage_session_flush_scheduler(app: Flask) -> None:
    global _scheduler_started

    if app.config.get("TESTING"):
        return

    if not app.config.get("APP_USAGE_ENABLED", True):
        logger.info("Usage session flush scheduler disabled (app usage off)")
        return

    poll_seconds = max(
        30,
        int(app.config.get("APP_USAGE_TTL_SECONDS", 90)) * 2,
    )

    if _scheduler_started:
        return
    _scheduler_started = True

    socketio.start_background_task(
        _scheduler_loop,
        app,
        poll_seconds=poll_seconds,
    )
