from __future__ import annotations

import logging

from commercial_app.config import settings
from commercial_app.infrastructure.persistence.plugins.migrations_runner import (
    MigrationError,
    run_migrations,
)

logger = logging.getLogger("commercial.migrations")


def run_migrations_on_startup() -> None:
    if not settings.COMMERCIAL_RUN_MIGRATIONS_ON_STARTUP:
        return

    logger.info("commercial_migrations_startup_begin")
    try:
        run_migrations()
    except MigrationError as exc:
        logger.exception("commercial_migrations_startup_failed")
        raise RuntimeError(f"Falha ao executar migrations no startup: {exc}") from exc

    logger.info("commercial_migrations_startup_done")
