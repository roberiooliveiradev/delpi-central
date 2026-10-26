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

    try:
        applied = run_migrations()
    except Exception:
        # Degraded boot: market-data routes already fail closed (503) when
        # storage is unreachable, so a missing schema grant must not take
        # the CNPJ surface down with it.
        logger.exception("market_data_migrations failed — degraded boot")
        return
    logger.info("market_data_migrations applied=%s", applied or "none")
