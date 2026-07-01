from __future__ import annotations

import logging
import os

from cx_app.infrastructure.persistence.migrations_runner import MigrationError, run_migrations

logger = logging.getLogger("customer_experience.migrations")


def run_migrations_on_startup() -> None:
    enabled = (
        str(os.getenv("CX_RUN_MIGRATIONS_ON_STARTUP", "false") or "false").lower()
        in {"1", "true", "yes", "on"}
    )
    if not enabled:
        return

    logger.info("cx_migrations_startup_begin")
    try:
        run_migrations()
    except MigrationError as exc:
        logger.exception("cx_migrations_startup_failed")
        raise RuntimeError(f"Falha ao executar migrations no startup: {exc}") from exc

    logger.info("cx_migrations_startup_done")
