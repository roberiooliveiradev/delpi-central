"""Rate-limit backends — unit + real Redis integration (X1 §11).

Redis tests need an isolated instance via ``EXTERNAL_DATA_TEST_REDIS_URL``
(ephemeral container) and skip otherwise.
"""

from __future__ import annotations

import multiprocessing
import os
import threading
import time

import pytest

from app.application.contracts import LimiterUnavailableError, RateLimitedError
from app.infrastructure.rate_limits import (
    InMemoryRateLimiter,
    RedisRateLimiter,
    UnavailableRateLimiter,
    build_rate_limiter,
)

REDIS_URL = os.getenv("EXTERNAL_DATA_TEST_REDIS_URL", "").strip()
LIMITS = {"consumer": 3, "cnpj": 3, "global": 6}
PREFIX = "test:external-data-rate-limit:"


# --- unit: in-memory --------------------------------------------------------


def test_memory_limiter_caps_dimension():
    limiter = InMemoryRateLimiter(limits=LIMITS)
    for _ in range(3):
        limiter.acquire("consumer", "supplies-api")
    with pytest.raises(RateLimitedError) as exc:
        limiter.acquire("consumer", "supplies-api")
    assert exc.value.retry_after and exc.value.retry_after > 0
    # sibling dimension unaffected
    limiter.acquire("cnpj", "hash1")


def test_memory_acquire_many_atomic_no_partial_consumption():
    limiter = InMemoryRateLimiter(limits={"consumer": 1, "cnpj": 5, "global": 5})
    limiter.acquire("consumer", "a")
    with pytest.raises(RateLimitedError):
        limiter.acquire_many([("consumer", "a"), ("cnpj", "h1")])
    # cnpj was NOT consumed by the denied call — next request must pass
    limiter.acquire_many([("consumer", "b"), ("cnpj", "h1")])


def test_memory_window_recovers():
    t = [0.0]
    limiter = InMemoryRateLimiter(
        limits={"consumer": 1, "cnpj": 1, "global": 1}, clock=lambda: t[0]
    )
    limiter.acquire("global", "all")
    with pytest.raises(RateLimitedError):
        limiter.acquire("global", "all")
    t[0] += 61
    limiter.acquire("global", "all")


def test_memory_thread_safe():
    limiter = InMemoryRateLimiter(limits=LIMITS)
    ok, blocked = [], []

    def work():
        try:
            limiter.acquire("global", "all")
            ok.append(1)
        except RateLimitedError:
            blocked.append(1)

    threads = [threading.Thread(target=work) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(ok) == 6 and len(blocked) == 14


# --- unit: factory ----------------------------------------------------------


def test_factory_default_process_local(monkeypatch):
    from app.infrastructure.config.settings import Settings

    monkeypatch.setattr(Settings, "EXTERNAL_DATA_CNPJ_PROVIDER", "unavailable")
    monkeypatch.setattr(Settings, "EXTERNAL_DATA_RATE_LIMIT_STRATEGY", "process_local")
    assert isinstance(build_rate_limiter(), InMemoryRateLimiter)


def test_factory_brasilapi_process_local_blocked_without_optin(monkeypatch):
    from app.infrastructure.config.settings import Settings

    monkeypatch.setattr(Settings, "EXTERNAL_DATA_CNPJ_PROVIDER", "brasilapi")
    monkeypatch.setattr(Settings, "EXTERNAL_DATA_RATE_LIMIT_STRATEGY", "process_local")
    monkeypatch.setattr(Settings, "EXTERNAL_DATA_PROCESS_LOCAL_ALLOWED", False)
    limiter = build_rate_limiter()
    assert isinstance(limiter, UnavailableRateLimiter)
    with pytest.raises(LimiterUnavailableError):
        limiter.acquire("consumer", "a")


def test_factory_brasilapi_process_local_with_optin(monkeypatch):
    from app.infrastructure.config.settings import Settings

    monkeypatch.setattr(Settings, "EXTERNAL_DATA_CNPJ_PROVIDER", "brasilapi")
    monkeypatch.setattr(Settings, "EXTERNAL_DATA_RATE_LIMIT_STRATEGY", "process_local")
    monkeypatch.setattr(Settings, "EXTERNAL_DATA_PROCESS_LOCAL_ALLOWED", True)
    assert isinstance(build_rate_limiter(), InMemoryRateLimiter)


def test_factory_unknown_strategy_fails_closed(monkeypatch):
    from app.infrastructure.config.settings import Settings

    monkeypatch.setattr(Settings, "EXTERNAL_DATA_RATE_LIMIT_STRATEGY", "bogus")
    limiter = build_rate_limiter()
    assert isinstance(limiter, UnavailableRateLimiter)


def test_factory_distributed_without_url_fails_closed(monkeypatch):
    from app.infrastructure.config.settings import Settings

    monkeypatch.setattr(Settings, "EXTERNAL_DATA_RATE_LIMIT_STRATEGY", "distributed")
    monkeypatch.setattr(Settings, "REDIS_URL", "")
    limiter = build_rate_limiter()
    assert isinstance(limiter, UnavailableRateLimiter)


def test_unavailable_limiter_blocks_everything():
    limiter = UnavailableRateLimiter("backend down")
    with pytest.raises(LimiterUnavailableError):
        limiter.acquire("consumer", "a")
    with pytest.raises(LimiterUnavailableError):
        limiter.acquire_many([("cnpj", "h"), ("global", "all")])


def test_redis_eval_payload_shape():
    calls = []

    class FakeClient:
        def eval(self, script, numkeys, *args):
            calls.append((numkeys, args))
            return [0, 0]

    limiter = RedisRateLimiter(
        redis_url="redis://x", limits=LIMITS, key_prefix=PREFIX,
        client=FakeClient(),
    )
    limiter.acquire_many([("consumer", "s1"), ("cnpj", "h"), ("global", "all")])
    numkeys, args = calls[0]
    assert numkeys == 3
    assert args[0] == f"{PREFIX}consumer:s1"
    assert args[1] == f"{PREFIX}cnpj:h"
    assert args[2] == f"{PREFIX}global:all"
    # per-dimension limits + window ms
    assert args[3:6] == (3, 3, 6)


def test_redis_denied_maps_retry_after():
    class FakeClient:
        def eval(self, script, numkeys, *args):
            return [1, 45000]

    limiter = RedisRateLimiter(
        redis_url="redis://x", limits=LIMITS, key_prefix=PREFIX,
        client=FakeClient(),
    )
    with pytest.raises(RateLimitedError) as exc:
        limiter.acquire("consumer", "s1")
    assert exc.value.retry_after == 45


def test_redis_backend_error_fails_closed():
    class FakeClient:
        def eval(self, script, numkeys, *args):
            raise RuntimeError("connection lost")

    limiter = RedisRateLimiter(
        redis_url="redis://x", limits=LIMITS, key_prefix=PREFIX,
        client=FakeClient(),
    )
    with pytest.raises(LimiterUnavailableError):
        limiter.acquire("consumer", "s1")


# --- integration: real Redis ------------------------------------------------

pytestmark_redis = pytest.mark.skipif(
    not REDIS_URL,
    reason="EXTERNAL_DATA_TEST_REDIS_URL not set — isolated Redis required",
)


def _redis_client():
    import redis

    return redis.from_url(REDIS_URL, decode_responses=True)


@pytest.fixture()
def real_redis():
    if not REDIS_URL:
        pytest.skip("EXTERNAL_DATA_TEST_REDIS_URL not set")
    client = _redis_client()
    for key in client.scan_iter(f"{PREFIX}*"):
        client.delete(key)
    yield client
    for key in client.scan_iter(f"{PREFIX}*"):
        client.delete(key)


def _new_limiter():
    return RedisRateLimiter(
        redis_url=REDIS_URL, limits=LIMITS, key_prefix=PREFIX,
        window_seconds=60.0,
    )


@pytestmark_redis
def test_two_clients_share_consumer_quota(real_redis):
    l1, l2 = _new_limiter(), _new_limiter()
    for _ in range(3):
        l1.acquire("consumer", "supplies-api")
    with pytest.raises(RateLimitedError):
        l2.acquire("consumer", "supplies-api")


@pytestmark_redis
def test_two_clients_share_cnpj_and_global(real_redis):
    l1, l2 = _new_limiter(), _new_limiter()
    for i in range(3):
        (l1 if i % 2 == 0 else l2).acquire("cnpj", "h1")
    with pytest.raises(RateLimitedError):
        l1.acquire("cnpj", "h1")

    for _ in range(4):
        l1.acquire("global", "all")
    for _ in range(2):
        l2.acquire("global", "all")
    with pytest.raises(RateLimitedError):
        l1.acquire("global", "all")


@pytestmark_redis
def test_atomic_no_partial_consumption(real_redis):
    limiter = _new_limiter()
    for _ in range(3):
        limiter.acquire("consumer", "a")
    with pytest.raises(RateLimitedError):
        limiter.acquire_many([("consumer", "a"), ("cnpj", "h9")])
    # cnpj:h9 was NOT incremented by the denied call
    limiter.acquire_many([("consumer", "b"), ("cnpj", "h9")])


@pytestmark_redis
def test_keys_carry_ttl(real_redis):
    limiter = _new_limiter()
    limiter.acquire("consumer", "ttl-check")
    ttl = real_redis.pttl(f"{PREFIX}consumer:ttl-check")
    assert 0 < ttl <= 60000


def _process_worker(url, n, results):
    limiter = RedisRateLimiter(
        redis_url=url, limits=LIMITS, key_prefix=PREFIX
    )
    got = 0
    for _ in range(n):
        try:
            limiter.acquire("global", "all")
            got += 1
        except RateLimitedError:
            pass
    results.put(got)


@pytestmark_redis
def test_multiworker_processes_share_cap(real_redis):
    import queue

    results = multiprocessing.Queue()
    procs = [
        multiprocessing.Process(
            target=_process_worker, args=(REDIS_URL, 4, results)
        )
        for _ in range(2)
    ]
    for p in procs:
        p.start()
    total = 0
    for p in procs:
        p.join(timeout=30)
    while True:
        try:
            total += results.get_nowait()
        except queue.Empty:
            break
    assert total == LIMITS["global"]


@pytestmark_redis
def test_concurrent_threads_respect_cap(real_redis):
    limiter = _new_limiter()
    ok, blocked = [], []

    def work():
        try:
            limiter.acquire("global", "all")
            ok.append(1)
        except RateLimitedError:
            blocked.append(1)

    threads = [threading.Thread(target=work) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(ok) == 6 and len(blocked) == 14


@pytestmark_redis
def test_recovery_after_window(real_redis):
    limiter = RedisRateLimiter(
        redis_url=REDIS_URL, limits={"consumer": 1, "cnpj": 1, "global": 1},
        key_prefix=PREFIX, window_seconds=0.15,
    )
    limiter.acquire("consumer", "rec")
    with pytest.raises(RateLimitedError):
        limiter.acquire("consumer", "rec")
    time.sleep(0.2)
    limiter.acquire("consumer", "rec")


@pytestmark_redis
def test_dead_backend_fails_closed(real_redis):
    import redis

    dead_client = redis.from_url(
        "redis://127.0.0.1:16398/0",
        socket_timeout=0.3,
        socket_connect_timeout=0.3,
    )
    limiter = RedisRateLimiter(
        redis_url="redis://127.0.0.1:16398/0",
        limits=LIMITS, key_prefix=PREFIX, client=dead_client,
    )
    with pytest.raises(LimiterUnavailableError):
        limiter.acquire("consumer", "a")


@pytestmark_redis
def test_namespace_isolation(real_redis):
    other = RedisRateLimiter(
        redis_url=REDIS_URL, limits=LIMITS, key_prefix="other:ns:",
    )
    limiter = _new_limiter()
    for _ in range(3):
        limiter.acquire("consumer", "ns-check")
    with pytest.raises(RateLimitedError):
        limiter.acquire("consumer", "ns-check")
    other.acquire("consumer", "ns-check")  # unaffected
