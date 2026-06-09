from app.composition.query_cache_composer import build_query_cache, reset_query_cache_for_tests
from app.domain.services.query_cache_stats_service import (
    build_query_cache_stats_payload,
    reset_query_cache_stats_for_tests,
)
from app.infrastructure.cache.stats_tracking_query_cache import StatsTrackingQueryCache


def setup_function() -> None:
    reset_query_cache_stats_for_tests()
    reset_query_cache_for_tests()


def test_stats_tracking_query_cache_records_hits_and_misses() -> None:
    cache = build_query_cache()
    assert isinstance(cache, StatsTrackingQueryCache)

    cache.set("lmp-dashboard|a", {"items": []})
    assert cache.get("lmp-dashboard|a") == {"items": []}
    assert cache.get("lmp-dashboard|missing") is None

    payload = build_query_cache_stats_payload(backend="memory", ttl_seconds=300)
    namespace = next(row for row in payload["namespaces"] if row["namespace"] == "lmp-dashboard")

    assert namespace["hits"] == 1
    assert namespace["misses"] == 1
    assert namespace["sets"] == 1
