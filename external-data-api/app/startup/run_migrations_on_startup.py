"""Startup migrations gate — same convention as the other plugin APIs.

Runs only when explicitly enabled and the plugins database is configured;
without DB env the service stays in its original stateless posture.
"""

from __future__ import annotations

import logging

from app.infrastructure.config.settings import Settings

logger = logging.getLogger("external-data-api.startup")


def run_migrations_on_startup() -> None:
    if not Settings.RUN_MIGRATIONS_ON_STARTUP:
        logger.info("market_data_migrations skipped: disabled")
        return
    if not Settings.plugins_db_configured():
        logger.info("market_data_migrations skipped: db not configured")
        return
    from app.infrastructure.persistence.migrations_runner import run_migrations

    applied = run_migrations()
    logger.info("market_data_migrations applied=%s", applied or "none")
