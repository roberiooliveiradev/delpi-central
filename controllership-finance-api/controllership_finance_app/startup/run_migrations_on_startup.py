"""Hook de startup: migrations gated por flag (padrão irmão)."""

from __future__ import annotations

import logging

from controllership_finance_app.config import settings
from controllership_finance_app.infrastructure.persistence.migrations_runner import (
    MigrationError,
    run_migrations,
)
from controllership_finance_app.infrastructure.persistence.plugins_db import (
    plugins_db_configured,
)

logger = logging.getLogger(__name__)


def run_migrations_on_startup() -> None:
    if not settings.RUN_MIGRATIONS_ON_STARTUP:
        return
    if not plugins_db_configured():
        logger.warning("migrations_skipped_plugins_db_not_configured")
        return
    try:
        applied = run_migrations()
    except MigrationError:
        logger.exception("migrations_failed_startup")
        raise
    if applied:
        logger.info("migrations_startup_applied count=%d", len(applied))
