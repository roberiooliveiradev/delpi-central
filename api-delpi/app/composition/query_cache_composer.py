from __future__ import annotations

import logging

from app.config import settings
from app.domain.ports.query_cache_port import QueryCachePort
from app.infrastructure.cache.memory_query_cache import MemoryQueryCache
from app.infrastructure.cache.redis_query_cache import RedisQueryCache
from app.infrastructure.cache.stats_tracking_query_cache import StatsTrackingQueryCache

logger = logging.getLogger(__name__)

_query_cache: StatsTrackingQueryCache | None = None
_query_cache_backend = "memory"


def build_query_cache() -> QueryCachePort:
    global _query_cache, _query_cache_backend

    if _query_cache is not None:
        return _query_cache

    backend = (settings.QUERY_CACHE_BACKEND or "memory").strip().lower()
    ttl_seconds = float(settings.QUERY_CACHE_TTL_SECONDS or 300)
    inner: QueryCachePort

    if backend == "redis" and settings.REDIS_URL:
        try:
            inner = RedisQueryCache(
                redis_url=settings.REDIS_URL,
                ttl_seconds=ttl_seconds,
            )
            _query_cache_backend = "redis"
            logger.info("Query cache backend: redis")
        except Exception as error:
            logger.warning(
                "Query cache redis unavailable, using memory: %s",
                error,
            )
            inner = MemoryQueryCache(ttl_seconds=ttl_seconds)
            _query_cache_backend = "memory"
    else:
        inner = MemoryQueryCache(ttl_seconds=ttl_seconds)
        _query_cache_backend = "memory"
        logger.info("Query cache backend: memory")

    _query_cache = StatsTrackingQueryCache(inner)
    return _query_cache


def get_query_cache_backend_name() -> str:
    build_query_cache()
    return _query_cache_backend


def get_query_cache_storage() -> MemoryQueryCache | RedisQueryCache | None:
    build_query_cache()
    if _query_cache is None:
        return None
    inner = _query_cache._inner
    if isinstance(inner, (MemoryQueryCache, RedisQueryCache)):
        return inner
    return None


def reset_query_cache_for_tests() -> None:
    global _query_cache, _query_cache_backend
    _query_cache = None
    _query_cache_backend = "memory"
