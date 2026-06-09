from __future__ import annotations

import logging

from app.config import settings
from app.domain.ports.sql_telemetry_store_port import SqlTelemetryStorePort
from app.infrastructure.observability.memory_sql_telemetry_store import MemorySqlTelemetryStore
from app.infrastructure.observability.redis_sql_telemetry_store import RedisSqlTelemetryStore

logger = logging.getLogger(__name__)

_sql_telemetry_store: SqlTelemetryStorePort | None = None


def build_sql_telemetry_store() -> SqlTelemetryStorePort:
    global _sql_telemetry_store

    if _sql_telemetry_store is not None:
        return _sql_telemetry_store

    backend = (settings.SQL_TELEMETRY_BACKEND or "memory").strip().lower()
    max_entries = int(settings.SQL_TELEMETRY_MAX_ENTRIES or 800)

    if backend == "redis" and settings.REDIS_URL:
        try:
            _sql_telemetry_store = RedisSqlTelemetryStore(
                redis_url=settings.REDIS_URL,
                max_entries=max_entries,
            )
            logger.info("SQL telemetry backend: redis")
            return _sql_telemetry_store
        except Exception as error:
            logger.warning(
                "SQL telemetry redis unavailable, using memory: %s",
                error,
            )

    _sql_telemetry_store = MemorySqlTelemetryStore(max_entries=max_entries)
    logger.info("SQL telemetry backend: memory")
    return _sql_telemetry_store


def reset_sql_telemetry_store_for_tests() -> None:
    global _sql_telemetry_store
    _sql_telemetry_store = None
