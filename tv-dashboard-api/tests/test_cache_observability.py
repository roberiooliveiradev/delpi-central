"""Decision counters for the bounded TTL cache and the single-flight registry.

Covers TV-OBS-001: cache_hit, miss_absent, consumer_stale, physical_expired,
lru_eviction and singleflight leader/waiter/error accounting. Counters must be
thread-safe, deterministic and free of key material or secrets.
"""

from __future__ import annotations

import threading
import time

import pytest

from tv_app.infrastructure.cache.bounded_ttl_lru_cache import BoundedTtlLruCache
from tv_app.infrastructure.cache.single_flight import SingleFlightRegistry


class TestCacheDecisionCounters:
    def test_hit_counts_fresh_read(self):
        cache = BoundedTtlLruCache(max_entries=8, ttl_seconds=60, retention_seconds=60)
        cache.set("k", {"v": 1})
        assert cache.get("k") == {"v": 1}
        stats = cache.stats()
        assert stats["hits"] == 1
        assert stats["missesAbsent"] == 0

    def test_missing_key_counts_absent(self):
        cache = BoundedTtlLruCache(max_entries=8, ttl_seconds=60, retention_seconds=60)
        assert cache.get("missing") is None
        assert cache.stats()["missesAbsent"] == 1

    def test_stale_for_consumer_counts_stale_and_retains_entry(self):
        now = [1000.0]
        cache = BoundedTtlLruCache(
            max_entries=8, ttl_seconds=60, retention_seconds=300, clock=lambda: now[0]
        )
        cache.set("k", "v")
        now[0] += 30  # within ttl (60) but beyond this consumer's bound (10)
        assert cache.get("k", max_age_seconds=10) is None
        stats = cache.stats()
        assert stats["missesStale"] == 1
        assert stats["entries"] == 1  # retained for a more permissive consumer
        now[0] += 1
        assert cache.get("k", max_age_seconds=60) == "v"
        assert cache.stats()["hits"] == 1

    def test_physical_expiry_counts_expired(self):
        now = [0.0]
        cache = BoundedTtlLruCache(
            max_entries=8, ttl_seconds=10, retention_seconds=10, clock=lambda: now[0]
        )
        cache.set("k", "v")
        now[0] += 11
        assert cache.get("k") is None
        stats = cache.stats()
        assert stats["missesExpired"] == 1
        assert stats["entries"] == 0

    def test_lru_eviction_counts_eviction(self):
        cache = BoundedTtlLruCache(max_entries=2, ttl_seconds=60, retention_seconds=60)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)  # evicts "a"
        stats = cache.stats()
        assert stats["evictionsLru"] == 1
        assert stats["entries"] == 2
        assert cache.get("a") is None

    def test_stats_shape_and_no_key_material(self):
        cache = BoundedTtlLruCache(max_entries=4, ttl_seconds=60, retention_seconds=60)
        cache.set("SECRET_SENTINEL_KEY", "v")
        cache.get("SECRET_SENTINEL_KEY")
        cache.get("other")
        stats = cache.stats()
        for field in ("hits", "missesAbsent", "missesExpired", "missesStale", "evictionsLru"):
            assert isinstance(stats[field], int)
        assert "SECRET_SENTINEL_KEY" not in repr(stats)


class TestSingleFlightCounters:
    def test_leader_and_waiters_counted(self):
        registry = SingleFlightRegistry[str]()
        barrier = threading.Barrier(5)
        results: list[str] = []
        fetch_calls = [0]
        fetch_lock = threading.Lock()

        def fetch() -> str:
            with fetch_lock:
                fetch_calls[0] += 1
            time.sleep(0.05)
            return "payload"

        def worker() -> None:
            barrier.wait()
            results.append(registry.run("key", fetch))

        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert results == ["payload"] * 5
        assert fetch_calls[0] == 1
        stats = registry.stats()
        assert stats["leaders"] == 1
        assert stats["waiters"] == 4
        assert stats["in_flight"] == 0
        assert stats["errors"] == 0

    def test_error_counted_and_propagated_to_waiters(self):
        registry = SingleFlightRegistry[str]()
        barrier = threading.Barrier(3)

        def fetch() -> str:
            time.sleep(0.05)
            raise RuntimeError("downstream failure")

        errors: list[Exception] = []

        def worker() -> None:
            barrier.wait()
            try:
                registry.run("key", fetch)
            except RuntimeError as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 3  # leader raises; waiters see the same error
        stats = registry.stats()
        assert stats["errors"] == 1
        assert stats["leaders"] + stats["waiters"] == 3
