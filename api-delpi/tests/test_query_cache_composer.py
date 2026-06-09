from unittest.mock import patch

from app.composition.query_cache_composer import (
    build_query_cache,
    reset_query_cache_for_tests,
)
from app.composition.query_cache_composer import get_query_cache_storage
from app.infrastructure.cache.memory_query_cache import MemoryQueryCache
from app.infrastructure.cache.stats_tracking_query_cache import StatsTrackingQueryCache


def setup_function() -> None:
    reset_query_cache_for_tests()


def test_build_query_cache_defaults_to_memory() -> None:
    cache = build_query_cache()
    assert isinstance(cache, StatsTrackingQueryCache)
    assert isinstance(get_query_cache_storage(), MemoryQueryCache)


def test_build_query_cache_falls_back_to_memory_when_redis_unavailable() -> None:
    reset_query_cache_for_tests()

    with patch("app.composition.query_cache_composer.settings") as settings:
        settings.QUERY_CACHE_BACKEND = "redis"
        settings.REDIS_URL = "redis://127.0.0.1:6399/0"
        settings.QUERY_CACHE_TTL_SECONDS = "300"

        with patch(
            "app.composition.query_cache_composer.RedisQueryCache",
            side_effect=ConnectionError("redis down"),
        ):
            cache = build_query_cache()

    assert isinstance(cache, StatsTrackingQueryCache)
    assert isinstance(get_query_cache_storage(), MemoryQueryCache)
