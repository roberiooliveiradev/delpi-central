"""Cache granular de status vivo — fato por (branch, OP, operação)."""

from __future__ import annotations

import threading
import time

from production_control_app.application.services.machine_load_live_status_cache import (
    clear_live_status_cache,
    get_live_status_many,
    invalidate_live_status_operation,
    put_live_status_many,
)


def setup_function() -> None:
    clear_live_status_cache()


def teardown_function() -> None:
    clear_live_status_cache()


def test_get_many_empty_cache_returns_all_misses() -> None:
    hits, misses = get_live_status_many("01", [("A", "01"), ("B", "01"), ("C", "01")])
    assert hits == {}
    assert misses == {("A", "01"), ("B", "01"), ("C", "01")}


def test_put_and_get_many_returns_hits() -> None:
    put_live_status_many(
        "01",
        {
            ("A", "01"): {"production_status": "started"},
            ("B", "01"): {"production_status": "in_progress"},
        },
    )
    hits, misses = get_live_status_many(
        "01", [("A", "01"), ("B", "01"), ("C", "01")]
    )
    assert set(hits) == {("A", "01"), ("B", "01")}
    assert misses == {("C", "01")}
    assert hits[("B", "01")]["production_status"] == "in_progress"


def test_entries_expire_individually() -> None:
    put_live_status_many("01", {("A", "01"): {}}, ttl_seconds=0.05)
    put_live_status_many("01", {("B", "01"): {}}, ttl_seconds=30)
    time.sleep(0.08)
    hits, misses = get_live_status_many("01", [("A", "01"), ("B", "01")])
    assert set(hits) == {("B", "01")}
    assert misses == {("A", "01")}


def test_invalidate_operation_removes_only_that_key() -> None:
    put_live_status_many(
        "01", {("A", "01"): {}, ("B", "01"): {}, ("C", "01"): {}}
    )
    invalidate_live_status_operation("01", "B", "01")
    hits, misses = get_live_status_many("01", [("A", "01"), ("B", "01"), ("C", "01")])
    assert set(hits) == {("A", "01"), ("C", "01")}
    assert misses == {("B", "01")}


def test_clear_branch_preserves_other_branches() -> None:
    put_live_status_many("01", {("A", "01"): {}})
    put_live_status_many("02", {("B", "01"): {}})
    clear_live_status_cache("01")
    assert get_live_status_many("01", [("A", "01")])[1] == {("A", "01")}
    assert ("B", "01") in get_live_status_many("02", [("B", "01")])[0]


def test_same_operation_is_shared_independent_of_requester() -> None:
    """A identidade do fato é OP+operação — nunca o CT que pediu."""
    put_live_status_many("01", {("SHARED", "010"): {"production_status": "started"}})
    hits, _ = get_live_status_many("01", [("SHARED", "010")])
    assert hits[("SHARED", "010")]["production_status"] == "started"


def test_concurrent_access_does_not_corrupt() -> None:
    errors: list[Exception] = []

    def worker(seed: int) -> None:
        try:
            for i in range(200):
                put_live_status_many("01", {(f"OP{seed}-{i}", "01"): {"x": i}})
                get_live_status_many("01", [(f"OP{seed}-{i}", "01")])
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(n,)) for n in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []
