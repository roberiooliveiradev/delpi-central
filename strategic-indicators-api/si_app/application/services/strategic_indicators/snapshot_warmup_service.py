from __future__ import annotations

import logging
import threading

from si_app.application.dto.strategic_indicators.get_executive_summary_real_request import (
    GetExecutiveSummaryRealRequest,
)
from si_app.application.dto.strategic_indicators.get_trends_real_request import (
    GetStrategicIndicatorsTrendsRealRequest,
)
from si_app.application.use_cases.strategic_indicators.period_resolution import (
    current_competence,
)
from si_app.composition.strategic_indicators_composer import (
    build_get_strategic_indicators_executive_summary_use_case,
    build_get_strategic_indicators_trends_use_case,
)
from si_app.config import settings

logger = logging.getLogger("strategic_indicators.warmup")

_warmup_lock = threading.Lock()
_warmup_started = False


def warmup_strategic_indicators_snapshots(
    *,
    competence: str | None = None,
    trends_months: int | None = None,
) -> None:
    resolved_competence = competence or current_competence()
    resolved_months = trends_months or settings.SI_WARMUP_TRENDS_MONTHS

    logger.info(
        "si_warmup_start competence=%s trends_months=%s",
        resolved_competence,
        resolved_months,
    )

    build_get_strategic_indicators_executive_summary_use_case().execute(
        GetExecutiveSummaryRealRequest(competence=resolved_competence)
    )
    build_get_strategic_indicators_trends_use_case().execute(
        GetStrategicIndicatorsTrendsRealRequest(
            competence=resolved_competence,
            months=resolved_months,
        )
    )

    logger.info("si_warmup_done competence=%s", resolved_competence)


def schedule_strategic_indicators_warmup() -> None:
    global _warmup_started

    if not settings.SI_WARMUP_ON_STARTUP:
        return

    with _warmup_lock:
        if _warmup_started:
            return
        _warmup_started = True

    def _run() -> None:
        try:
            warmup_strategic_indicators_snapshots()
        except Exception:
            logger.exception("si_warmup_failed")

    thread = threading.Thread(
        target=_run,
        name="si-snapshot-warmup",
        daemon=True,
    )
    thread.start()
