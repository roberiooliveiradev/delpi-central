"""Agenda notificação dos consumidores OpenAPI após o startup da api-delpi."""

from __future__ import annotations

import logging
import os
import threading
import time

from app.application.services.openapi_consumer_notify_service import (
    OpenApiConsumerNotifyService,
)

logger = logging.getLogger(__name__)


def _env_bool(name: str, default: bool) -> bool:
    raw = str(os.getenv(name, "1" if default else "0") or "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)) or default)
    except (TypeError, ValueError):
        return default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)) or default)
    except (TypeError, ValueError):
        return default


def schedule_openapi_consumer_notify_on_startup() -> None:
    """Dispara notify em thread daemon (não bloqueia o lifespan)."""
    if not _env_bool("OPENAPI_CONSUMER_NOTIFY_ON_STARTUP", True):
        logger.info("OPENAPI_CONSUMER_NOTIFY_ON_STARTUP=false — skip")
        return

    delay = _env_float("OPENAPI_CONSUMER_NOTIFY_DELAY_SECONDS", 15.0)
    retries = max(1, _env_int("OPENAPI_CONSUMER_NOTIFY_RETRIES", 3))
    retry_wait = _env_float("OPENAPI_CONSUMER_NOTIFY_RETRY_SECONDS", 20.0)

    def _worker() -> None:
        logger.info(
            "OpenAPI consumer notify agendado (delay=%.0fs, retries=%s)",
            delay,
            retries,
        )
        time.sleep(max(0.0, delay))
        service = OpenApiConsumerNotifyService()
        last: dict = {}
        for attempt in range(1, retries + 1):
            last = service.notify_safe()
            if last.get("ok") or last.get("skipped"):
                return
            if attempt < retries:
                logger.warning(
                    "OpenAPI consumer notify tentativa %s/%s falhou; retry em %.0fs",
                    attempt,
                    retries,
                    retry_wait,
                )
                time.sleep(max(0.0, retry_wait))
        logger.warning("OpenAPI consumer notify esgotou retries: %s", last)

    thread = threading.Thread(
        target=_worker,
        name="openapi-consumer-notify",
        daemon=True,
    )
    thread.start()
