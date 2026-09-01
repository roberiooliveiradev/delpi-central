from __future__ import annotations

import logging

import psycopg

from production_pulse_app.config import settings
from production_pulse_app.infrastructure.persistence.migrations_runner import up

logger = logging.getLogger(__name__)


def _plugins_dsn() -> str | None:
    if not all(
        [
            settings.PLUGINS_DB_HOST,
            settings.PLUGINS_DB_NAME,
            settings.PLUGINS_DB_USER,
            settings.PLUGINS_DB_PASSWORD,
        ]
    ):
        return None
    return (
        f"postgresql://{settings.PLUGINS_DB_USER}:{settings.PLUGINS_DB_PASSWORD}"
        f"@{settings.PLUGINS_DB_HOST}:{settings.PLUGINS_DB_PORT}/{settings.PLUGINS_DB_NAME}"
        f"?connect_timeout={settings.PLUGINS_DB_CONNECT_TIMEOUT}&sslmode={settings.PLUGINS_DB_SSLMODE}"
    )


def run_migrations_on_startup() -> None:
    if not settings.PRODUCTION_PULSE_RUN_MIGRATIONS_ON_STARTUP:
        return

    dsn = _plugins_dsn()
    if dsn is None:
        logger.warning(
            "PRODUCTION_PULSE_RUN_MIGRATIONS_ON_STARTUP=true but plugins DB is not configured"
        )
        return

    with psycopg.connect(dsn) as conn:
        applied = up(conn)
        if applied:
            logger.info("Production Pulse migrations applied: %s", applied)
