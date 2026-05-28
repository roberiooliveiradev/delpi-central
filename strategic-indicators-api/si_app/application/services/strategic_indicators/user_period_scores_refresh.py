from __future__ import annotations

import logging
import threading

from si_app.application.services.strategic_indicators.period_scores_refresh_service import (
    refresh_period_scores_materialized,
)
from si_app.application.services.strategic_indicators.snapshot_shared_cache import (
    clear_in_process_snapshot_cache,
)
from si_app.config import settings
from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_refresh_state_repository import (
    PostgresStrategicIndicatorsRefreshStateRepository,
)

logger = logging.getLogger("strategic_indicators.user_period_scores_refresh")


def is_period_scores_refresh_in_progress() -> bool:
    row = PostgresStrategicIndicatorsRefreshStateRepository().get_status()
    if not row:
        return False

    started_at = row.get("last_started_at")
    completed_at = row.get("last_completed_at")
    if started_at is None:
        return False
    if row.get("last_error"):
        return False
    if completed_at is None:
        return True
    return completed_at < started_at


def schedule_user_period_scores_refresh(
    *,
    reference_competence: str | None = None,
    trends_months: int | None = None,
) -> str:
    """
    Dispara refresh materializado como o job de 5 min (sem apagar period_scores).
    Mantém a versão limpa atual até uma nova versão is_clean ser gravada.

    Retorna: accepted | already_running | disabled
    """
    if not settings.SI_PERIOD_SCORES_ENABLED or not settings.SI_PERIOD_SCORES_REFRESH_ENABLED:
        return "disabled"

    if is_period_scores_refresh_in_progress():
        return "already_running"

    def _run() -> None:
        try:
            clear_in_process_snapshot_cache()
            refresh_period_scores_materialized(
                reference_competence=reference_competence,
                trends_months=trends_months,
                invalidate_cache=False,
            )
        except Exception:
            logger.exception("si_user_period_scores_refresh_failed")

    thread = threading.Thread(
        target=_run,
        name="si-user-period-scores-refresh",
        daemon=True,
    )
    thread.start()
    logger.info(
        "si_user_period_scores_refresh_scheduled competence=%s trends_months=%s",
        reference_competence,
        trends_months,
    )
    return "accepted"
