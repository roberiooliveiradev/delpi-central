import json
from unittest.mock import MagicMock, patch

from app.domain.services.sql_query_telemetry_models import SqlQueryRecord
from app.infrastructure.observability.redis_sql_telemetry_store import RedisSqlTelemetryStore


def _sample_record(**overrides) -> SqlQueryRecord:
    payload = {
        "query_hash": "abc123",
        "duration_ms": 12.5,
        "operation_id": "get_ppm_internal_summary",
        "caller_app": "api-delpi-console",
        "repository": "TestRepository",
        "recorded_at": "2026-06-09T12:00:00+00:00",
        "preview": "SELECT 1",
    }
    payload.update(overrides)
    return SqlQueryRecord(**payload)


def test_redis_store_appends_and_lists_entries() -> None:
    fake_client = MagicMock()
    fake_client.ping.return_value = True
    fake_pipe = MagicMock()
    fake_client.pipeline.return_value = fake_pipe

    stored: list[str] = []

    def capture_lpush(_key: str, payload: str) -> None:
        stored.append(payload)

    fake_pipe.lpush.side_effect = capture_lpush

    with patch("redis.from_url", return_value=fake_client):
        store = RedisSqlTelemetryStore(redis_url="redis://127.0.0.1:6379/0", max_entries=3)

    record = _sample_record()
    store.append(record)
    fake_client.lrange.return_value = list(reversed(stored))

    fake_pipe.lpush.assert_called_once()
    fake_pipe.ltrim.assert_called_once_with(store._buffer_key, 0, 2)
    fake_pipe.execute.assert_called_once()

    entries = store.list_entries()
    assert len(entries) == 1
    assert entries[0].query_hash == "abc123"
    assert entries[0].operation_id == "get_ppm_internal_summary"


def test_redis_store_respects_ring_buffer_order() -> None:
    fake_client = MagicMock()
    fake_client.ping.return_value = True
    fake_client.pipeline.return_value = MagicMock()

    payloads = [
        json.dumps(_sample_record(query_hash="first").__dict__),
        json.dumps(_sample_record(query_hash="second").__dict__),
    ]
    fake_client.lrange.return_value = list(reversed(payloads))

    with patch("redis.from_url", return_value=fake_client):
        store = RedisSqlTelemetryStore(redis_url="redis://127.0.0.1:6379/0")

    entries = store.list_entries()
    assert [entry.query_hash for entry in entries] == ["first", "second"]
