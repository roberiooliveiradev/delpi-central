from __future__ import annotations

import logging

from tv_app.config import settings
from tv_app.infrastructure.persistence.migrations_runner import run_migrations

logger = logging.getLogger(__name__)


def run_migrations_on_startup() -> None:
    if not settings.TV_DASHBOARD_RUN_MIGRATIONS_ON_STARTUP:
        logger.info("TV Dashboard migrations on startup desabilitadas.")
        return
    try:
        run_migrations()
    except Exception:
        logger.exception("Falha ao executar migrations do TV Dashboard on startup.")
        raise
