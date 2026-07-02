from __future__ import annotations

from unittest.mock import patch

from tm_app.application.services.dashboard_query_cache import DashboardQueryCache

_SETTINGS = "tm_app.application.services.dashboard_query_cache.settings"


def _cache(ttl: int = 120, enabled: bool = True) -> DashboardQueryCache:
    return DashboardQueryCache()


def test_caches_result_and_avoids_recompute():
    cache = DashboardQueryCache()
    calls = {"n": 0}

    def compute():
        calls["n"] += 1
        return calls["n"]

    with patch(_SETTINGS) as s:
        s.TM_DASHBOARD_QUERY_CACHE = True
        s.TM_DASHBOARD_QUERY_CACHE_TTL_SECONDS = 120
        first = cache.get_or_compute("ns", ("a",), compute)
        second = cache.get_or_compute("ns", ("a",), compute)

    assert first == 1
    assert second == 1  # veio do cache
    assert calls["n"] == 1


def test_distinct_keys_are_isolated():
    cache = DashboardQueryCache()
    with patch(_SETTINGS) as s:
        s.TM_DASHBOARD_QUERY_CACHE = True
        s.TM_DASHBOARD_QUERY_CACHE_TTL_SECONDS = 120
        a = cache.get_or_compute("ns", ("a",), lambda: "A")
        b = cache.get_or_compute("ns", ("b",), lambda: "B")

    assert a == "A"
    assert b == "B"


def test_invalidate_forces_recompute():
    cache = DashboardQueryCache()
    calls = {"n": 0}

    def compute():
        calls["n"] += 1
        return calls["n"]

    with patch(_SETTINGS) as s:
        s.TM_DASHBOARD_QUERY_CACHE = True
        s.TM_DASHBOARD_QUERY_CACHE_TTL_SECONDS = 120
        cache.get_or_compute("ns", ("a",), compute)
        cleared = cache.invalidate()
        cache.get_or_compute("ns", ("a",), compute)

    assert cleared == 1
    assert calls["n"] == 2


def test_disabled_cache_always_computes():
    cache = DashboardQueryCache()
    calls = {"n": 0}

    def compute():
        calls["n"] += 1
        return calls["n"]

    with patch(_SETTINGS) as s:
        s.TM_DASHBOARD_QUERY_CACHE = False
        s.TM_DASHBOARD_QUERY_CACHE_TTL_SECONDS = 120
        cache.get_or_compute("ns", ("a",), compute)
        cache.get_or_compute("ns", ("a",), compute)

    assert calls["n"] == 2


def test_no_cache_when_invalidated_mid_compute():
    """Se uma invalidação ocorre durante o cálculo, o valor obsoleto não é cacheado."""
    cache = DashboardQueryCache()

    with patch(_SETTINGS) as s:
        s.TM_DASHBOARD_QUERY_CACHE = True
        s.TM_DASHBOARD_QUERY_CACHE_TTL_SECONDS = 120

        def compute_with_invalidate():
            cache.invalidate()  # CRUD no meio da leitura
            return "stale"

        cache.get_or_compute("ns", ("a",), compute_with_invalidate)

        calls = {"n": 0}

        def compute():
            calls["n"] += 1
            return "fresh"

        result = cache.get_or_compute("ns", ("a",), compute)

    assert result == "fresh"
    assert calls["n"] == 1
