from __future__ import annotations

import json

from app.domain.services.sql_query_telemetry_models import SqlQueryRecord


class RedisSqlTelemetryStore:
    def __init__(
        self,
        *,
        redis_url: str,
        max_entries: int = 800,
        key_prefix: str = "api-delpi:sql-telemetry:",
    ) -> None:
        import redis

        self._client = redis.from_url(redis_url, decode_responses=True)
        self._max_entries = max(1, int(max_entries))
        self._buffer_key = f"{key_prefix}buffer"
        self._client.ping()

    def backend_name(self) -> str:
        return "redis"

    def append(self, record: SqlQueryRecord) -> None:
        payload = json.dumps(record.__dict__, default=str)
        pipe = self._client.pipeline()
        pipe.lpush(self._buffer_key, payload)
        pipe.ltrim(self._buffer_key, 0, self._max_entries - 1)
        pipe.execute()

    def list_entries(self) -> list[SqlQueryRecord]:
        raw_entries = self._client.lrange(self._buffer_key, 0, -1)
        records: list[SqlQueryRecord] = []
        for raw in reversed(raw_entries):
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                continue
            records.append(SqlQueryRecord(**parsed))
        return records
