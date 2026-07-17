from __future__ import annotations

import logging
import os

from cipa_app.infrastructure.persistence.migrations_runner import (
    MigrationError,
    run_migrations,
)

logger = logging.getLogger("cipa.migrations")


def run_migrations_on_startup() -> None:
    enabled = (
        str(os.getenv("CIPA_RUN_MIGRATIONS_ON_STARTUP", "false") or "false").lower()
        in {"1", "true", "yes", "on"}
    )
    if not enabled:
        return

    logger.info("cipa_migrations_startup_begin")
    try:
        run_migrations()
    except MigrationError as exc:
        logger.exception("cipa_migrations_startup_failed")
        raise RuntimeError(f"Falha ao executar migrations no startup: {exc}") from exc

    logger.info("cipa_migrations_startup_done")
