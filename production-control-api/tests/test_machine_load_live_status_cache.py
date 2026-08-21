"""Cache de status HZA vivo — troca de CT não deve reconsultar a api-delpi."""

from __future__ import annotations

import time

from production_control_app.application.services.machine_load_live_status_cache import (
    clear_live_status_cache,
    get_live_status_cache,
    put_live_status_cache,
)


def setup_function() -> None:
    clear_live_status_cache()


def teardown_function() -> None:
    clear_live_status_cache()


def test_live_status_cache_roundtrip() -> None:
    status = {("000001", "01"): {"production_status": "started", "is_in_production": False}}
    put_live_status_cache("01", status, ttl_seconds=30)
    hit = get_live_status_cache("01")
    assert hit is not None
    assert hit[("000001", "01")]["production_status"] == "started"
    assert get_live_status_cache("02") is None


def test_live_status_cache_expires() -> None:
    put_live_status_cache("01", {("A", "01"): {"is_in_production": True}}, ttl_seconds=0.05)
    assert get_live_status_cache("01") is not None
    time.sleep(0.08)
    assert get_live_status_cache("01") is None


def test_clear_live_status_cache_branch() -> None:
    put_live_status_cache("01", {("A", "01"): {}})
    put_live_status_cache("02", {("B", "01"): {}})
    clear_live_status_cache("01")
    assert get_live_status_cache("01") is None
    assert get_live_status_cache("02") is not None
