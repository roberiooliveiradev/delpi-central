from __future__ import annotations

import threading
import time

from app.composition.query_cache_composer import (
    build_query_cache,
    reset_query_cache_for_tests,
)
from app.infrastructure.cache.singleflight import Singleflight
from app.infrastructure.cache.ttl_cache import TtlCache


def setup_function() -> None:
    reset_query_cache_for_tests()


def test_singleflight_runs_factory_once_under_concurrency() -> None:
    gate = Singleflight[int]()
    calls = {"n": 0}
    lock = threading.Lock()

    def factory() -> int:
        with lock:
            calls["n"] += 1
        time.sleep(0.05)
        return 42

    results: list[int] = []

    def worker() -> None:
        results.append(gate.do("k", factory))

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert calls["n"] == 1
    assert results == [42] * 8


def test_ttl_cache_get_or_set_singleflight() -> None:
    cache: TtlCache[str] = TtlCache(ttl_seconds=60)
    calls = {"n": 0}

    def factory() -> str:
        calls["n"] += 1
        time.sleep(0.03)
        return "ok"

    results: list[str] = []

    def worker() -> None:
        results.append(cache.get_or_set("row", factory))

    threads = [threading.Thread(target=worker) for _ in range(6)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert calls["n"] == 1
    assert results == ["ok"] * 6
    assert cache.get("row") == "ok"


def test_query_cache_get_or_set_prevents_stampede() -> None:
    cache = build_query_cache()
    calls = {"n": 0}

    def factory() -> dict:
        calls["n"] += 1
        time.sleep(0.04)
        return {"rows": [1, 2, 3]}

    results: list[dict] = []

    def worker() -> None:
        results.append(cache.get_or_set("lmp-dashboard|stampede", factory))

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert calls["n"] == 1
    assert all(item == {"rows": [1, 2, 3]} for item in results)
