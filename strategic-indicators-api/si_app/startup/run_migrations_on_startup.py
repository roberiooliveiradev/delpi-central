from __future__ import annotations

import logging
import os

from si_app.infrastructure.persistence.plugins.migrations_runner import (
    MigrationError,
    run_migrations,
)

logger = logging.getLogger("strategic_indicators.migrations")


def run_migrations_on_startup() -> None:
    enabled = (
        str(os.getenv("SI_RUN_MIGRATIONS_ON_STARTUP", "false") or "false").lower()
        in {"1", "true", "yes", "on"}
    )
    if not enabled:
        return

    logger.info("si_migrations_startup_begin")
    try:
        run_migrations()
    except MigrationError as exc:
        logger.exception("si_migrations_startup_failed")
        raise RuntimeError(f"Falha ao executar migrations no startup: {exc}") from exc

    logger.info("si_migrations_startup_done")
