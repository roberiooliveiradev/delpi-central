"""Hook de startup: migrations gated por flag (padrão das APIs irmãs)."""

from __future__ import annotations

import logging

from it_portal_app.config import settings
from it_portal_app.infrastructure.persistence.db import db_configured
from it_portal_app.infrastructure.persistence.migrations_runner import (
    MigrationError,
    run_migrations,
)

logger = logging.getLogger(__name__)


def run_migrations_on_startup() -> None:
    if not settings.RUN_MIGRATIONS_ON_STARTUP:
        return
    if not db_configured():
        logger.warning("it_portal_migrations_skipped_db_not_configured")
        return
    try:
        applied = run_migrations()
    except MigrationError:
        logger.exception("it_portal_migrations_failed_startup")
        raise
    if applied:
        logger.info("it_portal_migrations_startup_applied count=%d", len(applied))
