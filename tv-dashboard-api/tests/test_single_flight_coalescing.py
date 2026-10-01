import threading
import time
from unittest.mock import MagicMock

import pytest

from tv_app.application.services.comunicado_data_enrichment_service import (
    ComunicadoDataEnrichmentService,
    reset_comunicado_data_block_cache,
)
from tv_app.application.services.native_screen_cache_service import (
    reset_native_data_cache,
)
from tv_app.application.services.native_screen_data_service import NativeScreenDataService
from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService


@pytest.fixture(autouse=True)
def _clean_cache():
    reset_comunicado_data_block_cache()
    reset_native_data_cache()
    yield
    reset_comunicado_data_block_cache()
    reset_native_data_cache()


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


def _run_concurrent(callable_, n, *, hold_release=None):
    """N threads start simultaneously on `callable_`; results/errors collected."""
    starter = threading.Barrier(n + 1)
    results, errors = [], []

    def caller():
        starter.wait(timeout=10)
        try:
            results.append(callable_())
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=caller) for _ in range(n)]
    for t in threads:
        t.start()
    starter.wait(timeout=10)
    if hold_release is not None:
        time.sleep(0.4)
        hold_release.set()
    for t in threads:
        t.join(timeout=30)
    assert all(not t.is_alive() for t in threads)
    return results, errors


def test_a_concurrent_identical_miss_fetches_once():
    calls = []
    release = threading.Event()

    def fetch(*_a, **_k):
        calls.append(1)
        release.wait(timeout=10)
        return _payload()

    service, _ = _service(fetch)
    results, errors = _run_concurrent(
        lambda: service._fetch_cached("op_demo", {"a": 1}, None), 5, hold_release=release
    )

    assert not errors
    assert len(results) == 5
    assert len(calls) == 1, f"expected 1 downstream fetch, got {len(calls)}"
    assert all(r["data"] == results[0]["data"] for r in results)


def test_b_cached_payload_fetches_zero_times():
    calls = []

    def fetch(*_a, **_k):
        calls.append(1)
        return _payload()

    service, _ = _service(fetch)
    first = service._fetch_cached("op_demo", {"a": 1}, None)
    second = service._fetch_cached("op_demo", {"a": 1}, None)

    assert len(calls) == 1
    assert second["_tvCacheHit"] is True
    assert second["data"] == first["data"]


def test_c_different_params_do_not_coalesce():
    calls = []
    release = threading.Event()

    def fetch(*_a, **k):
        calls.append(dict(k.get("params") or {}))
        release.wait(timeout=10)
        return _payload()

    service, _ = _service(fetch)
    barrier = threading.Barrier(3)
    results, errors = [], []

    def caller(params):
        barrier.wait(timeout=10)
        try:
            results.append(service._fetch_cached("op_demo", params, None))
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [
        threading.Thread(target=caller, args=({"a": 1},)),
        threading.Thread(target=caller, args=({"a": 2},)),
    ]
    for t in threads:
        t.start()
    barrier.wait(timeout=10)
    time.sleep(0.4)
    release.set()
    for t in threads:
        t.join(timeout=30)

    assert not errors
    assert len(results) == 2
    assert len(calls) == 2, f"different params must not coalesce, got {len(calls)}"


def test_d_different_auth_scope_does_not_coalesce():
    calls = []
    release = threading.Event()

    def fetch(*_a, **_k):
        calls.append(1)
        release.wait(timeout=10)
        return _payload()

    service, _ = _service(fetch)
    barrier = threading.Barrier(3)
    results, errors = [], []

    def caller(auth):
        barrier.wait(timeout=10)
        try:
            results.append(service._fetch_cached("op_demo", {"a": 1}, auth))
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [
        threading.Thread(target=caller, args=("Bearer token-user-a",)),
        threading.Thread(target=caller, args=("Bearer token-user-b",)),
    ]
    for t in threads:
        t.start()
    barrier.wait(timeout=10)
    time.sleep(0.4)
    release.set()
    for t in threads:
        t.join(timeout=30)

    assert not errors
    assert len(results) == 2
    assert len(calls) == 2, f"different auth scope must not coalesce, got {len(calls)}"


def test_e_failure_propagates_to_waiters_and_allows_retry():
    attempts = []
    release = threading.Event()

    def fetch(*_a, **_k):
        attempts.append(1)
        if len(attempts) == 1:
            release.wait(timeout=10)
            raise RuntimeError("downstream boom")
        return _payload()

    service, _ = _service(fetch)
    results, errors = _run_concurrent(
        lambda: service._fetch_cached("op_demo", {"a": 1}, None), 5, hold_release=release
    )

    assert not results
    assert len(errors) == 5
    assert all(isinstance(e, RuntimeError) for e in errors)
    assert len(attempts) == 1, f"leader fetch must run once, got {len(attempts)}"

    # Falha não vira cache negativo: nova chamada dispara novo fetch.
    second = service._fetch_cached("op_demo", {"a": 1}, None)
    assert len(attempts) == 2
    assert second["data"]["value"] == 1


def test_f_sequential_requests_use_ttl_cache():
    calls = []

    def fetch(*_a, **_k):
        calls.append(1)
        return _payload(value=len(calls))

    service, _ = _service(fetch)
    for _ in range(3):
        service._fetch_cached("op_demo", {"a": 1}, None)
    assert len(calls) == 1

    # Segunda identidade (outros params) segue independente em sequência.
    service._fetch_cached("op_demo", {"a": 9}, None)
    assert len(calls) == 2


def test_g_concurrent_presentations_share_downstream_fetch():
    calls = []
    release = threading.Event()

    def fetch(*_a, **_k):
        calls.append(1)
        release.wait(timeout=10)
        return {
            "meta": {
                "operationId": "get_overall_equipment_effectiveness_pct",
                "shape": "scalar",
            },
            "data": {"summary": {"value": 78.4}},
            "route": {
                "label": "OEE",
                "valueFields": ["value", "oeePct"],
                "tvConstraints": {},
            },
        }

    service, _ = _service(fetch)
    blocks = [
        {
            "id": "kpi-1",
            "type": "data_kpi",
            "frame": {"x": 5, "y": 5, "w": 30, "h": 20},
            "dataBinding": {
                "operationId": "get_overall_equipment_effectiveness_pct",
                "params": {"periodDays": 7},
                "displayMode": "kpi",
            },
        }
    ]

    results, errors = _run_concurrent(
        lambda: service.enrich_blocks(
            [dict(b) for b in blocks], cfg={}, authorization=None
        ),
        5,
        hold_release=release,
    )

    assert not errors
    assert len(results) == 5
    assert all(r[0]["resolved"]["kpi"]["value"] == 78.4 for r in results)
    assert len(calls) == 1, (
        f"5 concurrent presentations must share one fetch, got {len(calls)}"
    )


def test_h_native_screen_concurrent_resolve_fetches_once():
    calls = []
    release = threading.Event()

    def fetch(*_a, **_k):
        calls.append(1)
        release.wait(timeout=10)
        return {"oee": 77.7}

    gateway = MagicMock()
    gateway.fetch_oee_overview.side_effect = fetch
    service = NativeScreenDataService(gateway=gateway)

    results, errors = _run_concurrent(
        lambda: service.resolve(
            screen_key="production_oee_overview", config={"branch": "01"}
        ),
        5,
        hold_release=release,
    )

    assert not errors
    assert len(results) == 5
    assert all(r["oee"] == 77.7 for r in results)
    assert len(calls) == 1, f"native screen concurrent miss must fetch once, got {len(calls)}"


def test_i_native_screen_error_result_not_cached_and_retryable():
    calls = []

    def fetch(*_a, **_k):
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError("downstream boom")
        return {"oee": 77.7}

    gateway = MagicMock()
    gateway.fetch_oee_overview.side_effect = fetch
    service = NativeScreenDataService(gateway=gateway)

    first = service.resolve(screen_key="production_oee_overview", config={"branch": "01"})
    assert first.get("error") is True

    second = service.resolve(screen_key="production_oee_overview", config={"branch": "01"})
    assert second["oee"] == 77.7
    assert len(calls) == 2
