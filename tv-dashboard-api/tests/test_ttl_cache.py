import time

from tv_app.infrastructure.cache.ttl_cache import TtlCache


def test_ttl_cache_stores_and_expires():
    cache = TtlCache[str](ttl_seconds=0.05)
    cache.set("key", "value")
    assert cache.get("key") == "value"
    time.sleep(0.06)
    assert cache.get("key") is None


def test_ttl_cache_invalidate_all():
    cache = TtlCache[str](ttl_seconds=60)
    cache.set("a", "1")
    cache.invalidate_all()
    assert cache.get("a") is None


def test_ttl_cache_stats():
    cache = TtlCache[str](ttl_seconds=60)
    assert cache.stats()["entries"] == 0
    cache.set("a", "1")
    assert cache.stats()["entries"] == 1
