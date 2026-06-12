from __future__ import annotations

import logging
import os

from maint_app.infrastructure.persistence.plugins.migrations_runner import (
    MigrationError,
    run_migrations,
)

logger = logging.getLogger("maintenance.migrations")


def run_migrations_on_startup() -> None:
    enabled = (
        str(os.getenv("MAINT_RUN_MIGRATIONS_ON_STARTUP", "false") or "false").lower()
        in {"1", "true", "yes", "on"}
    )
    if not enabled:
        return

    logger.info("maint_migrations_startup_begin")
    try:
        run_migrations()
    except MigrationError as exc:
        logger.exception("maint_migrations_startup_failed")
        raise RuntimeError(f"Falha ao executar migrations no startup: {exc}") from exc

    logger.info("maint_migrations_startup_done")
