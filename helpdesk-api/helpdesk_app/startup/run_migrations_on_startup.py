from __future__ import annotations

import logging
import os

from helpdesk_app.infrastructure.persistence.postgres import MigrationError, run_migrations

logger = logging.getLogger("helpdesk.migrations")


def run_migrations_on_startup() -> None:
    enabled = (
        str(os.getenv("HELPDESK_RUN_MIGRATIONS_ON_STARTUP", "false") or "false").lower()
        in {"1", "true", "yes", "on"}
    )
    if not enabled:
        return
    try:
        run_migrations()
    except MigrationError as exc:
        logger.exception("helpdesk_migrations_failed")
        raise RuntimeError(f"Falha ao executar migrations no startup: {exc}") from exc
