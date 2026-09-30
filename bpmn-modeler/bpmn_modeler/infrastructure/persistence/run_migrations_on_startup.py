from __future__ import annotations

import logging
import os

from bpmn_modeler.infrastructure.persistence.migrations_runner import (
    MigrationError,
    run_migrations,
)

logger = logging.getLogger("bpmn_modeler.migrations")


def run_migrations_on_startup() -> None:
    enabled = (
        str(os.getenv("BPMN_RUN_MIGRATIONS_ON_STARTUP", "true") or "true").lower()
        in {"1", "true", "yes", "on"}
    )
    if not enabled:
        return

    logger.info("bpmn_migrations_startup_begin")
    try:
        run_migrations()
    except MigrationError as exc:
        logger.exception("bpmn_migrations_startup_failed")
        raise RuntimeError(f"Falha ao executar migrations no startup: {exc}") from exc

    logger.info("bpmn_migrations_startup_done")
