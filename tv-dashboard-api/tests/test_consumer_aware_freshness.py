"""PERF-005 — consumer-aware freshness (globalRefreshSec = max cache age).

Deterministic: a fake clock is injected into BoundedTtlLruCache instances;
no sleeps.
"""

import threading
from unittest.mock import MagicMock

import pytest

import tv_app.application.services.comunicado_data_enrichment_service as cdes
import tv_app.application.services.native_screen_cache_service as nscs
from tv_app.application.services.comunicado_data_enrichment_service import (
    ComunicadoDataEnrichmentService,
    reset_comunicado_data_block_cache,
)
from tv_app.application.services.native_screen_cache_service import (
    reset_native_data_cache,
)
from tv_app.application.services.native_screen_data_service import NativeScreenDataService
from tv_app.application.services.tv_data_route_catalog_service import (
    TvDataRouteCatalogService,
)
from tv_app.infrastructure.cache.bounded_ttl_lru_cache import BoundedTtlLruCache


class FakeClock:
    def __init__(self, now: float = 1_000.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture(autouse=True)
def _clean_caches():
    reset_comunicado_data_block_cache()
    reset_native_data_cache()
    yield
    reset_comunicado_data_block_cache()
    reset_native_data_cache()


@pytest.fixture
def data_clock(monkeypatch):
    clock = FakeClock()
    monkeypatch.setattr(cdes._data_block_cache, "_clock", clock)
    return clock


@pytest.fixture
def native_clock(monkeypatch):
    clock = FakeClock()
    monkeypatch.setattr(nscs._native_cache, "_clock", clock)
    return clock


def _payload(value=1):
    return {
        "operationId": "op_demo",
        "meta": {"operationId": "op_demo", "shape": "scalar"},
        "data": {"value": value},
        "route": {"label": "demo"},
    }


def _service(fetch_impl):
    gateway = MagicMock()
    gateway.fetch_by_operation_id.side_effect = fetch_impl
    return ComunicadoDataEnrichmentService(
        catalog=TvDataRouteCatalogService(), gateway=gateway
    ), gateway


def _native_service(fetch_impl):
    gateway = MagicMock()
    gateway.fetch_oee_overview.side_effect = fetch_impl
    return NativeScreenDataService(gateway=gateway), gateway


# --------------------------------------------------------------------------
# BoundedTtlLruCache unit semantics (baseline + freshness matrix)
# --------------------------------------------------------------------------


def _cache(clock: FakeClock, **kw) -> BoundedTtlLruCache:
    kw.setdefault("max_entries", 16)
    return BoundedTtlLruCache[str](
        ttl_seconds=120,
        retention_seconds=3600,
        clock=clock,
        **kw,
    )


def test_baseline_legacy_consumer_serves_31s_entry():
    """Pre-PERF-005 defect, kept for legacy callers: bound = ttl (120s), so a
    31s-old entry is a hit even though a 30s playlist demands fresher data."""
    clock = FakeClock()
    cache = _cache(clock)
    cache.set("k", "v")
    clock.advance(31)
    assert cache.get("k") == "v"  # legacy bound: hit (baseline violation shape)


def test_strict_30s_consumer_rejects_31s_entry():
    clock = FakeClock()
    cache = _cache(clock)
    cache.set("k", "v")
    clock.advance(31)
    assert cache.get("k", max_age_seconds=30) is None


def test_300s_consumer_accepts_90s_entry():
    clock = FakeClock()
    cache = _cache(clock)
    cache.set("k", "v")
    clock.advance(90)
    assert cache.get("k", max_age_seconds=300) == "v"


def test_same_entry_different_consumer_decisions_and_no_eviction():
    clock = FakeClock()
    cache = _cache(clock)
    cache.set("k", "v")
    clock.advance(90)
    assert cache.get("k", max_age_seconds=30) is None
    # Stale-for-A must not evict B's still-valid shared entry.
    assert cache.get("k", max_age_seconds=300) == "v"


def test_3600s_consumer_reuses_physically_retained_entry():
    clock = FakeClock()
    cache = _cache(clock)
    cache.set("k", "v")
    clock.advance(3000)  # far beyond legacy 120s TTL, within retention
    assert cache.get("k", max_age_seconds=3600) == "v"
    assert cache.get("k", max_age_seconds=300) is None  # age 3000 > 300


def test_physical_expiry_evicts_entry():
    clock = FakeClock()
    cache = _cache(clock)
    cache.set("k", "v")
    clock.advance(3601)
    assert cache.get("k", max_age_seconds=3600) is None
    assert cache.stats()["entries"] == 0


def test_3600_boundary_inclusive_contract():
    """Boundary contract: live while age <= retention; fresh while
    age <= max_age. Both layers use the same inclusive comparison."""
    clock = FakeClock()
    cache = _cache(clock)
    cache.set("k", "v")
    clock.advance(3600 - 0.001)
    assert cache.get("k", max_age_seconds=3600) == "v"
    cache.set("k", "v")  # reset stored_at
    clock.advance(3600)  # age exactly == retention == max_age → still usable
    assert cache.get("k", max_age_seconds=3600) == "v"
    cache.set("k", "v")
    clock.advance(3600.001)
    assert cache.get("k", max_age_seconds=3600) is None


def test_max_entries_lru_eviction():
    clock = FakeClock()
    cache = _cache(clock, max_entries=2)
    cache.set("a", "1")
    cache.set("b", "2")
    cache.get("a")  # refresh recency: b becomes oldest
    cache.set("c", "3")
    assert cache.get("a") == "1"
    assert cache.get("b") is None
    assert cache.get("c") == "3"
    assert cache.stats()["entries"] == 2


def test_retention_defaults_to_ttl_when_unset():
    clock = FakeClock()
    cache = BoundedTtlLruCache[str](ttl_seconds=120, max_entries=16, clock=clock)
    cache.set("k", "v")
    clock.advance(121)
    assert cache.get("k", max_age_seconds=3600) is None


def test_get_returns_defensive_copy():
    cache = BoundedTtlLruCache[dict](ttl_seconds=60, max_entries=4)
    cache.set("k", {"rows": [1]})
    cache.get("k")["rows"].append(9)
    assert cache.get("k") == {"rows": [1]}


# --------------------------------------------------------------------------
# Data-block path (service level)
# --------------------------------------------------------------------------


def test_data_block_30s_stale_triggers_refetch(data_clock):
    calls = []

    def fetch(*_a, **_k):
        calls.append(1)
        return _payload(value=len(calls))

    service, _ = _service(fetch)
    first = service._fetch_cached("op_demo", {"a": 1}, None, max_age_seconds=30)
    assert first["data"]["value"] == 1

    data_clock.advance(31)
    second = service._fetch_cached("op_demo", {"a": 1}, None, max_age_seconds=30)
    assert len(calls) == 2
    assert second["data"]["value"] == 2


def test_data_block_300s_consumer_hits_90s_entry(data_clock):
    calls = []

    def fetch(*_a, **_k):
        calls.append(1)
        return _payload()

    service, _ = _service(fetch)
    service._fetch_cached("op_demo", {"a": 1}, None, max_age_seconds=300)
    data_clock.advance(90)
    hit = service._fetch_cached("op_demo", {"a": 1}, None, max_age_seconds=300)
    assert len(calls) == 1
    assert hit["_tvCacheHit"] is True


def test_data_block_cross_playlist_shared_entry(data_clock):
    calls = []

    def fetch(*_a, **_k):
        calls.append(1)
        return _payload(value=len(calls))

    service, _ = _service(fetch)
    # Playlist B (300s) warms the shared entry.
    service._fetch_cached("op_demo", {"a": 1}, None, max_age_seconds=300)
    data_clock.advance(90)

    # Playlist A (30s): same business key, entry stale-for-A → refresh.
    refreshed = service._fetch_cached("op_demo", {"a": 1}, None, max_age_seconds=30)
    assert len(calls) == 2
    assert refreshed["data"]["value"] == 2

    # B reuses A's fresh replacement — one shared entry, no playlist namespace.
    hit = service._fetch_cached("op_demo", {"a": 1}, None, max_age_seconds=300)
    assert len(calls) == 2
    assert hit["_tvCacheHit"] is True
    assert cdes._data_block_cache.stats()["entries"] == 1


def test_data_block_concurrent_stale_single_fetch(data_clock):
    calls = []
    release = threading.Event()

    def fetch(*_a, **_k):
        calls.append(1)
        if len(calls) > 1:
            release.wait(timeout=10)
        return _payload(value=len(calls))

    service, _ = _service(fetch)
    service._fetch_cached("op_demo", {"a": 1}, None, max_age_seconds=30)
    data_clock.advance(31)

    starter = threading.Barrier(6)
    results, errors = [], []

    def caller():
        starter.wait(timeout=10)
        try:
            results.append(
                service._fetch_cached("op_demo", {"a": 1}, None, max_age_seconds=30)
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=caller) for _ in range(5)]
    for t in threads:
        t.start()
    starter.wait(timeout=10)
    release.set()
    for t in threads:
        t.join(timeout=30)

    assert not errors
    assert len(results) == 5
    # 1 warm-up fetch + exactly 1 refresh under single-flight.
    assert len(calls) == 2, f"expected 2 downstream fetches, got {len(calls)}"
    assert all(r["data"]["value"] == 2 for r in results)


def test_data_block_mixed_concurrent_consumers(data_clock):
    calls = []
    release = threading.Event()

    def fetch(*_a, **_k):
        calls.append(1)
        if len(calls) > 1:
            release.wait(timeout=10)
        return _payload(value=len(calls))

    service, _ = _service(fetch)
    service._fetch_cached("op_demo", {"a": 1}, None, max_age_seconds=300)
    data_clock.advance(90)

    starter = threading.Barrier(3)
    results = {}

    def caller(name, max_age):
        starter.wait(timeout=10)
        results[name] = service._fetch_cached(
            "op_demo", {"a": 1}, None, max_age_seconds=max_age
        )

    ta = threading.Thread(target=caller, args=("strict", 30))
    tb = threading.Thread(target=caller, args=("lenient", 300))
    ta.start()
    tb.start()
    starter.wait(timeout=10)
    # Lenient consumer is NOT forced to wait for the strict refresh.
    tb.join(timeout=30)
    release.set()
    ta.join(timeout=30)

    assert results["lenient"]["data"]["value"] == 1  # served from shared entry
    assert results["strict"]["data"]["value"] == 2  # triggered the refresh
    assert len(calls) == 2


def test_data_block_failed_refresh_keeps_entry_and_retries(data_clock):
    calls = []

    def fetch(*_a, **_k):
        calls.append(1)
        if len(calls) == 2:
            raise RuntimeError("downstream boom")
        return _payload(value=len(calls))

    service, _ = _service(fetch)
    service._fetch_cached("op_demo", {"a": 1}, None, max_age_seconds=300)
    data_clock.advance(90)

    with pytest.raises(RuntimeError):
        service._fetch_cached("op_demo", {"a": 1}, None, max_age_seconds=30)

    # Lenient consumer still served: failed refresh did not evict the entry.
    hit = service._fetch_cached("op_demo", {"a": 1}, None, max_age_seconds=300)
    assert hit["data"]["value"] == 1

    # No stuck inflight / no negative cache: retry fetches again.
    third = service._fetch_cached("op_demo", {"a": 1}, None, max_age_seconds=30)
    assert len(calls) == 3
    assert third["data"]["value"] == 3


def test_data_block_force_refresh_bypasses_freshness(data_clock):
    calls = []

    def fetch(*_a, **_k):
        calls.append(1)
        return _payload(value=len(calls))

    service, _ = _service(fetch)
    service._fetch_cached("op_demo", {"a": 1}, None, max_age_seconds=300)
    data_clock.advance(5)
    forced = service._fetch_cached(
        "op_demo", {"a": 1}, None, force_refresh=True, max_age_seconds=300
    )
    assert len(calls) == 2
    assert forced["data"]["value"] == 2


# --------------------------------------------------------------------------
# Native cache path
# --------------------------------------------------------------------------


def test_native_30s_stale_triggers_refresh(native_clock):
    calls = []

    def fetch(*_a, **_k):
        calls.append(1)
        return {"oee": 70 + len(calls)}

    service, _ = _native_service(fetch)
    first = service.resolve(
        screen_key="production_oee_overview",
        config={"branch": "01"},
        max_age_seconds=30,
    )
    assert first["oee"] == 71

    native_clock.advance(31)
    second = service.resolve(
        screen_key="production_oee_overview",
        config={"branch": "01"},
        max_age_seconds=30,
    )
    assert len(calls) == 2
    assert second["oee"] == 72


def test_native_300s_consumer_hits_90s_entry(native_clock):
    calls = []

    def fetch(*_a, **_k):
        calls.append(1)
        return {"oee": 77.7}

    service, _ = _native_service(fetch)
    service.resolve(
        screen_key="production_oee_overview",
        config={"branch": "01"},
        max_age_seconds=300,
    )
    native_clock.advance(90)
    hit = service.resolve(
        screen_key="production_oee_overview",
        config={"branch": "01"},
        max_age_seconds=300,
    )
    assert len(calls) == 1
    assert hit["oee"] == 77.7


def test_native_same_entry_different_consumer_decisions(native_clock):
    calls = []

    def fetch(*_a, **_k):
        calls.append(1)
        return {"oee": 70 + len(calls)}

    service, _ = _native_service(fetch)
    service.resolve(
        screen_key="production_oee_overview",
        config={"branch": "01"},
        max_age_seconds=300,
    )
    native_clock.advance(90)

    strict = service.resolve(
        screen_key="production_oee_overview",
        config={"branch": "01"},
        max_age_seconds=30,
    )
    assert strict["oee"] == 72
    assert len(calls) == 2
    assert nscs._native_cache.stats()["entries"] == 1


# --------------------------------------------------------------------------
# Presentation integration: playlist.globalRefreshSec → max_age_seconds
# --------------------------------------------------------------------------


def _playlist(global_refresh_sec):
    playlist = {
        "id": "11111111-1111-1111-1111-111111111111",
        "name": "TV",
        "description": None,
        "isActive": True,
        "publicToken": "tok",
        "masterConfig": {},
        "dataDefaults": {},
        "defaultDurationSec": 30,
        "transitionStyle": "fade",
        "viewportProfile": "1080p",
        "playbackMode": "presentation",
    }
    if global_refresh_sec is not None:
        playlist["globalRefreshSec"] = global_refresh_sec
    return playlist


def _native_slide():
    return {
        "id": "s1",
        "sortOrder": 1,
        "slideType": "native",
        "nativeScreenKey": "production_oee_overview",
        "nativeConfig": {"branch": "01"},
        "isActive": True,
        "title": "OEE",
    }


def _presentation_service(global_refresh_sec):
    from tv_app.application.services.presentation_payload_service import (
        PresentationPayloadService,
    )

    repo = MagicMock()
    repo.get_by_token.return_value = _playlist(global_refresh_sec)
    repo.list_sections.return_value = []
    repo.list_slides.return_value = [_native_slide()]
    native = MagicMock()
    native.resolve.return_value = {"oee": 77.7}
    service = PresentationPayloadService(repository=repo, native_data=native)
    return service, native


def test_present_propagates_global_refresh_as_max_age():
    service, native = _presentation_service(global_refresh_sec=30)
    service.build_by_token("tok")
    assert native.resolve.call_args.kwargs["max_age_seconds"] == 30.0


def test_present_defaults_max_age_to_300_when_unset():
    service, native = _presentation_service(global_refresh_sec=None)
    service.build_by_token("tok")
    assert native.resolve.call_args.kwargs["max_age_seconds"] == 300.0


def test_present_3600_propagates():
    service, native = _presentation_service(global_refresh_sec=3600)
    service.build_by_token("tok")
    assert native.resolve.call_args.kwargs["max_age_seconds"] == 3600.0
