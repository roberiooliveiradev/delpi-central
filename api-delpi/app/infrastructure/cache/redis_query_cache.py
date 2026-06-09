from __future__ import annotations

import json
from typing import Any

from collections import defaultdict

from app.domain.ports.query_cache_port import QueryCachePort
from app.domain.services.query_cache_stats_service import cache_namespace_from_key


class RedisQueryCache(QueryCachePort):
    def __init__(
        self,
        *,
        redis_url: str,
        ttl_seconds: float,
        key_prefix: str = "api-delpi:query:",
    ) -> None:
        import redis

        self._client = redis.from_url(redis_url, decode_responses=True)
        self._ttl_seconds = max(1, int(ttl_seconds))
        self._key_prefix = key_prefix
        self._client.ping()

    def get(self, key: str) -> Any | None:
        raw = self._client.get(self._storage_key(key))
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    def set(self, key: str, value: Any) -> None:
        self._client.setex(
            self._storage_key(key),
            self._ttl_seconds,
            json.dumps(value, default=str),
        )

    def invalidate_all(self) -> None:
        pattern = f"{self._key_prefix}*"
        cursor = 0
        while True:
            cursor, keys = self._client.scan(cursor=cursor, match=pattern, count=200)
            if keys:
                self._client.delete(*keys)
            if cursor == 0:
                break

    def _storage_key(self, key: str) -> str:
        return f"{self._key_prefix}{key}"

    def count_keys_by_namespace(self) -> dict[str, int]:
        counts: dict[str, int] = defaultdict(int)
        cursor = 0
        pattern = f"{self._key_prefix}*"
        while True:
            cursor, keys = self._client.scan(cursor=cursor, match=pattern, count=200)
            for storage_key in keys:
                logical_key = storage_key.removeprefix(self._key_prefix)
                counts[cache_namespace_from_key(logical_key)] += 1
            if cursor == 0:
                break
        return dict(counts)
