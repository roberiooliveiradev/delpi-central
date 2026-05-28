from __future__ import annotations

import logging
import threading
import time

from si_app.application.services.strategic_indicators.period_scores_refresh_service import (
    refresh_period_scores_materialized,
)
from si_app.config import settings

logger = logging.getLogger("strategic_indicators.period_scores_scheduler")

_scheduler_lock = threading.Lock()
_scheduler_started = False


def run_period_scores_refresh_once() -> None:
    if not settings.SI_PERIOD_SCORES_REFRESH_ENABLED:
        return

    try:
        # Não apaga period_scores a cada ciclo — só invalida cache in-process em
        # mudanças de config (snapshot_shared_cache.invalidate_*).
        refresh_period_scores_materialized(invalidate_cache=False)
    except Exception:
        logger.exception("si_period_scores_refresh_cycle_failed")


def schedule_period_scores_refresh() -> None:
    global _scheduler_started

    if not settings.SI_PERIOD_SCORES_REFRESH_ENABLED:
        logger.info("si_period_scores_scheduler_disabled")
        return

    with _scheduler_lock:
        if _scheduler_started:
            return
        _scheduler_started = True

    interval = max(60, settings.SI_PERIOD_SCORES_REFRESH_INTERVAL_SECONDS)

    def _loop() -> None:
        logger.info(
            "si_period_scores_scheduler_started interval_seconds=%s",
            interval,
        )
        run_period_scores_refresh_once()

        while True:
            time.sleep(interval)
            run_period_scores_refresh_once()

    thread = threading.Thread(
        target=_loop,
        name="si-period-scores-refresh",
        daemon=True,
    )
    thread.start()
