from __future__ import annotations

import logging
import os

from cec_app.infrastructure.persistence.migrations_runner import (
    MigrationError,
    run_migrations,
)

logger = logging.getLogger("comite_etica.migrations")


def run_migrations_on_startup() -> None:
    enabled = (
        str(os.getenv("CEC_RUN_MIGRATIONS_ON_STARTUP", "false") or "false").lower()
        in {"1", "true", "yes", "on"}
    )
    if not enabled:
        return

    logger.info("cec_migrations_startup_begin")
    try:
        run_migrations()
    except MigrationError as exc:
        logger.exception("cec_migrations_startup_failed")
        raise RuntimeError(f"Falha ao executar migrations no startup: {exc}") from exc

    logger.info("cec_migrations_startup_done")
