"""Poller interno — agendas vencidas do Delpi Reports (sem depender de cron no host)."""

from __future__ import annotations

import logging
import os
import threading
import time

logger = logging.getLogger(__name__)

_DEFAULT_POLL_SECONDS = 900
_STOP = threading.Event()


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)) or default)
    except (TypeError, ValueError):
        return default


def schedule_reports_due_poller_on_startup() -> None:
    """Inicia thread daemon que chama ``process-pending`` periodicamente.

    ``REPORTS_SCHEDULE_POLL_SECONDS``:
    - default ``900`` (15 min)
    - ``0`` desliga o poller (ex.: só cron externo)
    """
    interval = _env_int("REPORTS_SCHEDULE_POLL_SECONDS", _DEFAULT_POLL_SECONDS)
    if interval <= 0:
        logger.info("REPORTS_SCHEDULE_POLL_SECONDS=%s — poller de agendas desligado", interval)
        return

    limit = max(1, min(_env_int("REPORTS_SCHEDULE_POLL_LIMIT", 20), 100))
    _STOP.clear()

    def _worker() -> None:
        logger.info(
            "reports_schedule_poller_started interval_seconds=%s limit=%s",
            interval,
            limit,
        )
        # Evita disputa com migrations/bootstrap logo no boot.
        time.sleep(min(30.0, float(interval)))
        while not _STOP.is_set():
            try:
                from app.composition.reports_composer import (
                    build_process_due_report_schedules_use_case,
                )

                result = build_process_due_report_schedules_use_case().execute(
                    limit=limit
                )
                logger.info(
                    "reports_schedule_poller_tick due=%s processed=%s errors=%s",
                    result.get("dueCount"),
                    result.get("processedCount"),
                    result.get("errorCount"),
                )
            except Exception as exc:  # noqa: BLE001 — poller não derruba o processo
                logger.warning(
                    "reports_schedule_poller_failed error=%s",
                    str(exc)[:400],
                )
            _STOP.wait(timeout=float(interval))

    thread = threading.Thread(
        target=_worker,
        name="reports-schedule-poller",
        daemon=True,
    )
    thread.start()


def stop_reports_due_poller_for_tests() -> None:
    """Sinaliza parada (testes / shutdown opcional)."""
    _STOP.set()
