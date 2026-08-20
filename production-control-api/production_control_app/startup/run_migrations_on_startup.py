from __future__ import annotations

import logging
import os

from production_control_app.infrastructure.persistence.migrations_runner import (
    MigrationError,
    run_migrations,
)

logger = logging.getLogger("production_control.migrations")


def run_migrations_on_startup() -> None:
    enabled = (
        str(os.getenv("PC_RUN_MIGRATIONS_ON_STARTUP", "false") or "false").lower()
        in {"1", "true", "yes", "on"}
    )
    if not enabled:
        return

    logger.info("pc_migrations_startup_begin")
    try:
        run_migrations()
    except MigrationError as exc:
        logger.exception("pc_migrations_startup_failed")
        raise RuntimeError(f"Falha ao executar migrations no startup: {exc}") from exc
    logger.info("pc_migrations_startup_done")
