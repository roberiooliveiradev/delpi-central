from unittest.mock import patch

from app.composition.sql_telemetry_composer import (
    build_sql_telemetry_store,
    reset_sql_telemetry_store_for_tests,
)
from app.infrastructure.observability.memory_sql_telemetry_store import MemorySqlTelemetryStore


def setup_function() -> None:
    reset_sql_telemetry_store_for_tests()


def test_build_sql_telemetry_store_defaults_to_memory() -> None:
    store = build_sql_telemetry_store()
    assert isinstance(store, MemorySqlTelemetryStore)
    assert store.backend_name() == "memory"


def test_build_sql_telemetry_store_falls_back_to_memory_when_redis_unavailable() -> None:
    reset_sql_telemetry_store_for_tests()

    with patch("app.composition.sql_telemetry_composer.settings") as settings:
        settings.SQL_TELEMETRY_BACKEND = "redis"
        settings.SQL_TELEMETRY_MAX_ENTRIES = "800"
        settings.REDIS_URL = "redis://127.0.0.1:6399/0"

        with patch(
            "app.composition.sql_telemetry_composer.RedisSqlTelemetryStore",
            side_effect=ConnectionError("redis down"),
        ):
            store = build_sql_telemetry_store()

    assert isinstance(store, MemorySqlTelemetryStore)
