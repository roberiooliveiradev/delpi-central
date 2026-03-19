# app/infrastructure/persistence/plugins/plugin_healthcheck.py
from __future__ import annotations

import logging
from typing import Any

from app.infrastructure.providers.databse.plugins_postgres_connection import (
    PluginsDatabaseConfigError,
    PluginsDatabaseConnectionError,
    check_plugins_connection,
    get_plugins_connection_settings,
)

logger = logging.getLogger(__name__)


def get_plugins_db_health() -> dict[str, Any]:
    """
    Retorna um payload padronizado de saúde do datasource plugins.
    """
    try:
        settings = get_plugins_connection_settings()
        is_healthy = check_plugins_connection()

        return {
            "name": "postgres-plugins",
            "status": "ok" if is_healthy else "error",
            "details": {
                "host": settings.host,
                "port": settings.port,
                "database": settings.database,
            },
        }
    except (PluginsDatabaseConfigError, PluginsDatabaseConnectionError) as exc:
        logger.warning("Plugins DB healthcheck unavailable: %s", exc)
        return {
            "name": "postgres-plugins",
            "status": "error",
            "details": {
                "reason": str(exc),
            },
        }
    except Exception as exc:
        logger.exception("Unexpected plugins DB healthcheck error.")
        return {
            "name": "postgres-plugins",
            "status": "error",
            "details": {
                "reason": "unexpected_error",
                "message": str(exc),
            },
        }