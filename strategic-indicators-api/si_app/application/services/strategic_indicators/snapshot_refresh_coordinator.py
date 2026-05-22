from __future__ import annotations

import logging
import threading

from si_app.config import settings

logger = logging.getLogger("strategic_indicators.snapshot_refresh_coordinator")

_coordinator_lock = threading.Lock()
_refresh_timer: threading.Timer | None = None

_DEBOUNCE_SECONDS = 2.0


def schedule_period_scores_refresh_after_config_change() -> None:
    if not settings.SI_PERIOD_SCORES_REFRESH_ON_CONFIG_CHANGE:
        return
    if not settings.SI_PERIOD_SCORES_REFRESH_ENABLED:
        return
    if not settings.SI_PERIOD_SCORES_ENABLED:
        return

    global _refresh_timer

    def _run_refresh() -> None:
        from si_app.application.services.strategic_indicators.period_scores_scheduler import (
            run_period_scores_refresh_once,
        )

        try:
            run_period_scores_refresh_once()
        except Exception:
            logger.exception("si_period_scores_refresh_after_config_change_failed")

    with _coordinator_lock:
        if _refresh_timer is not None:
            _refresh_timer.cancel()
        _refresh_timer = threading.Timer(_DEBOUNCE_SECONDS, _run_refresh)
        _refresh_timer.daemon = True
        _refresh_timer.start()
