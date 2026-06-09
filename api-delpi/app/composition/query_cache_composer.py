from __future__ import annotations

import logging

from app.config import settings
from app.domain.ports.query_cache_port import QueryCachePort
from app.infrastructure.cache.memory_query_cache import MemoryQueryCache
from app.infrastructure.cache.redis_query_cache import RedisQueryCache

logger = logging.getLogger(__name__)

_query_cache: QueryCachePort | None = None


def build_query_cache() -> QueryCachePort:
    global _query_cache

    if _query_cache is not None:
        return _query_cache

    backend = (settings.QUERY_CACHE_BACKEND or "memory").strip().lower()
    ttl_seconds = float(settings.QUERY_CACHE_TTL_SECONDS or 300)

    if backend == "redis" and settings.REDIS_URL:
        try:
            _query_cache = RedisQueryCache(
                redis_url=settings.REDIS_URL,
                ttl_seconds=ttl_seconds,
            )
            logger.info("Query cache backend: redis")
            return _query_cache
        except Exception as error:
            logger.warning(
                "Query cache redis unavailable, using memory: %s",
                error,
            )

    _query_cache = MemoryQueryCache(ttl_seconds=ttl_seconds)
    logger.info("Query cache backend: memory")
    return _query_cache


def reset_query_cache_for_tests() -> None:
    global _query_cache
    _query_cache = None
