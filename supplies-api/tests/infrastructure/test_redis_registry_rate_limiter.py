"""S3.2 — registry rate-limit backends: unit + real Redis integration tests.

Unit tests run everywhere. Redis integration tests require an isolated
Redis instance via ``SUPPLIES_TEST_REDIS_URL`` (ephemeral container in CI/
dev), and are skipped otherwise.
"""

from __future__ import annotations

import multiprocessing
import os
import threading
import time

import pytest

from app.application.services.supplier_enrichment.contracts import (
    RegistryLimiterUnavailableError,
    RegistryRateLimitedError,
)
from app.infrastructure.gateways.registry_rate_limits import (
    InMemoryRegistryRateLimiter,
    RedisRegistryRateLimiter,
    UnavailableRegistryRateLimiter,
    build_registry_rate_limiter,
)

REDIS_URL = os.getenv("SUPPLIES_TEST_REDIS_URL", "").strip()
LIMITS = {"actor": 3, "cnpj": 3, "global": 6}
PREFIX = "test:registry-rate-limit:"


# --- unit: factory / strategy -------------------------------------------------


def test_factory_defaults_to_process_local(monkeypatch):
    from app.infrastructure.config.settings import Settings

    monkeypatch.setattr(Settings, "COMPANY_REGISTRY_RATE_LIMIT_STRATEGY", "process_local")
    assert isinstance(build_registry_rate_limiter(), InMemoryRegistryRateLimiter)


def test_factory_distributed_without_url_fails_closed(monkeypatch):
    from app.infrastructure.config.settings import Settings

    monkeypatch.setattr(Settings, "COMPANY_REGISTRY_RATE_LIMIT_STRATEGY", "distributed")
    monkeypatch.setattr(Settings, "REDIS_URL", "")
    limiter = build_registry_rate_limiter()
    assert isinstance(limiter, UnavailableRegistryRateLimiter)
    with pytest.raises(RegistryLimiterUnavailableError):
        limiter.acquire("actor", "u1")


def test_factory_unknown_strategy_fails_closed(monkeypatch):
    from app.infrastructure.config.settings import Settings

    monkeypatch.setattr(Settings, "COMPANY_REGISTRY_RATE_LIMIT_STRATEGY", "bogus")
    limiter = build_registry_rate_limiter()
    assert isinstance(limiter, UnavailableRegistryRateLimiter)
    with pytest.raises(RegistryLimiterUnavailableError):
        limiter.acquire("actor", "u1")


def test_factory_brasilapi_process_local_blocked_without_optin(monkeypatch):
    from app.infrastructure.config.settings import Settings

    monkeypatch.setattr(Settings, "COMPANY_REGISTRY_PROVIDER", "brasilapi")
    monkeypatch.setattr(Settings, "COMPANY_REGISTRY_RATE_LIMIT_STRATEGY", "process_local")
    monkeypatch.setattr(Settings, "COMPANY_REGISTRY_PROCESS_LOCAL_ALLOWED", False)
    limiter = build_registry_rate_limiter()
    assert isinstance(limiter, UnavailableRegistryRateLimiter)
    with pytest.raises(RegistryLimiterUnavailableError):
        limiter.acquire("cnpj", "h")


def test_factory_external_data_process_local_blocked_without_optin(monkeypatch):
    # X3 — same multiworker protection for the shared-service mode: the
    # actor limit must not silently degrade to per-worker memory in prod.
    from app.infrastructure.config.settings import Settings

    monkeypatch.setattr(Settings, "COMPANY_REGISTRY_PROVIDER", "external-data-api")
    monkeypatch.setattr(Settings, "COMPANY_REGISTRY_RATE_LIMIT_STRATEGY", "process_local")
    monkeypatch.setattr(Settings, "COMPANY_REGISTRY_PROCESS_LOCAL_ALLOWED", False)
    limiter = build_registry_rate_limiter()
    assert isinstance(limiter, UnavailableRegistryRateLimiter)
    with pytest.raises(RegistryLimiterUnavailableError):
        limiter.acquire("actor", "u1")


def test_factory_brasilapi_process_local_with_explicit_optin(monkeypatch):
    from app.infrastructure.config.settings import Settings

    monkeypatch.setattr(Settings, "COMPANY_REGISTRY_PROVIDER", "brasilapi")
    monkeypatch.setattr(Settings, "COMPANY_REGISTRY_RATE_LIMIT_STRATEGY", "process_local")
    monkeypatch.setattr(Settings, "COMPANY_REGISTRY_PROCESS_LOCAL_ALLOWED", True)
    assert isinstance(build_registry_rate_limiter(), InMemoryRegistryRateLimiter)


def test_factory_unavailable_provider_process_local_stays_local(monkeypatch):
    from app.infrastructure.config.settings import Settings

    monkeypatch.setattr(Settings, "COMPANY_REGISTRY_PROVIDER", "unavailable")
    monkeypatch.setattr(Settings, "COMPANY_REGISTRY_RATE_LIMIT_STRATEGY", "process_local")
    assert isinstance(build_registry_rate_limiter(), InMemoryRegistryRateLimiter)


def test_unavailable_limiter_blocks_everything():
    limiter = UnavailableRegistryRateLimiter("backend down")
    with pytest.raises(RegistryLimiterUnavailableError):
        limiter.acquire("actor", "u1")
    with pytest.raises(RegistryLimiterUnavailableError):
        limiter.acquire_many([("cnpj", "h"), ("global", "all")])
    with pytest.raises(RegistryLimiterUnavailableError):
        limiter.check("actor:u1")


# --- unit: multi-dimension atomicity (in-memory) --------------------------------


def test_acquire_many_denied_dim_leaves_no_partial_consumption():
    limiter = InMemoryRegistryRateLimiter(limits={"actor": 1, "cnpj": 5, "global": 5})
    limiter.acquire("actor", "u1")  # actor now at cap
    with pytest.raises(RegistryRateLimitedError):
        limiter.acquire_many([("actor", "u1"), ("cnpj", "h1")])
    # cnpj was NOT consumed by the denied batch — a different actor can still
    # acquire it.
    limiter.acquire_many([("actor", "u2"), ("cnpj", "h1")])


# --- unit: Redis impl with fake client -------------------------------------------


class _FakeRedisClient:
    """Minimal redis-py surface used by the limiter (eval-based)."""

    def __init__(self):
        self._counts: dict[str, int] = {}
        self._ttls: dict[str, int] = {}
        self.fail_next = False
        self.eval_calls: list[tuple] = []

    def eval(self, script, numkeys, *keys_and_args):
        self.eval_calls.append((numkeys, keys_and_args))
        if self.fail_next:
            self.fail_next = False
            raise ConnectionError("redis down")
        keys = list(keys_and_args[:numkeys])
        limits = list(keys_and_args[numkeys:-1])
        window_ms = int(keys_and_args[-1])
        for i, k in enumerate(keys):
            if self._counts.get(k, 0) >= int(limits[i]):
                return [1, self._ttls.get(k, -1)]
        for k in keys:
            self._counts[k] = self._counts.get(k, 0) + 1
            if self._counts[k] == 1:
                self._ttls[k] = window_ms
        return [0, 0]


def test_redis_limiter_uses_atomic_eval_with_prefixed_keys():
    client = _FakeRedisClient()
    limiter = RedisRegistryRateLimiter(
        redis_url="", limits=LIMITS, key_prefix=PREFIX, client=client
    )
    limiter.acquire_many([("cnpj", "h1"), ("global", "all")])
    (numkeys, args), = client.eval_calls
    assert numkeys == 2
    assert f"{PREFIX}cnpj:h1" in args and f"{PREFIX}global:all" in args


def test_redis_limiter_denies_at_cap_with_retry_after():
    client = _FakeRedisClient()
    limiter = RedisRegistryRateLimiter(
        redis_url="", limits={"cnpj": 1, "global": 9}, key_prefix=PREFIX, client=client
    )
    limiter.acquire("cnpj", "h1")
    with pytest.raises(RegistryRateLimitedError) as err:
        limiter.acquire("cnpj", "h1")
    assert err.value.retry_after >= 1


def test_redis_limiter_backend_error_fails_closed():
    client = _FakeRedisClient()
    client.fail_next = True
    limiter = RedisRegistryRateLimiter(
        redis_url="", limits=LIMITS, key_prefix=PREFIX, client=client
    )
    with pytest.raises(RegistryLimiterUnavailableError):
        limiter.acquire("actor", "u1")


def test_redis_limiter_init_without_url_unavailable():
    with pytest.raises(RegistryLimiterUnavailableError):
        RedisRegistryRateLimiter(redis_url="")


# --- integration: real Redis ---------------------------------------------------


@pytest.mark.skipif(not REDIS_URL, reason="SUPPLIES_TEST_REDIS_URL not set")
class TestRedisIntegration:
    @pytest.fixture()
    def clients(self):
        import redis

        c1 = redis.from_url(REDIS_URL, decode_responses=True)
        c2 = redis.from_url(REDIS_URL, decode_responses=True)
        for client in (c1, c2):
            for key in client.scan_iter(f"{PREFIX}*"):
                client.delete(key)
        yield c1, c2
        for client in (c1, c2):
            for key in client.scan_iter(f"{PREFIX}*"):
                client.delete(key)

    def _limiters(self, c1, c2):
        return (
            RedisRegistryRateLimiter(
                redis_url="", limits=LIMITS, key_prefix=PREFIX, client=c1
            ),
            RedisRegistryRateLimiter(
                redis_url="", limits=LIMITS, key_prefix=PREFIX, client=c2
            ),
        )

    def test_two_clients_share_cnpj_counter(self, clients):
        c1, c2 = clients
        l1, l2 = self._limiters(c1, c2)
        l1.acquire("cnpj", "shared-cnpj")
        l1.acquire("cnpj", "shared-cnpj")
        l2.acquire("cnpj", "shared-cnpj")
        with pytest.raises(RegistryRateLimitedError):
            l1.acquire("cnpj", "shared-cnpj")
        assert int(c1.get(f"{PREFIX}cnpj:shared-cnpj")) == 3

    def test_actor_and_global_share_across_clients(self, clients):
        c1, c2 = clients
        l1, l2 = self._limiters(c1, c2)
        for i in range(3):
            (l1 if i % 2 == 0 else l2).acquire("actor", "u-shared")
        with pytest.raises(RegistryRateLimitedError):
            l1.acquire("actor", "u-shared")
        for i in range(6):
            (l1 if i % 2 else l2).acquire_many([("cnpj", f"c{i}"), ("global", "all")])
        with pytest.raises(RegistryRateLimitedError):
            l2.acquire_many([("cnpj", "c-x"), ("global", "all")])

    def test_multiworker_concurrent_processes_share_cap(self, clients):
        """Two OS-level workers (separate processes) share the same cap."""

        def worker(url, n, out):
            import redis as r

            c = r.from_url(url, decode_responses=True)
            lim = RedisRegistryRateLimiter(
                redis_url="", limits=LIMITS, key_prefix=PREFIX, client=c
            )
            ok = blocked = 0
            for _ in range(n):
                try:
                    lim.acquire("cnpj", "mp-cnpj")
                    ok += 1
                except RegistryRateLimitedError:
                    blocked += 1
            out.put((ok, blocked))

        q1, q2 = multiprocessing.Queue(), multiprocessing.Queue()
        p1 = multiprocessing.Process(target=worker, args=(REDIS_URL, 4, q1))
        p2 = multiprocessing.Process(target=worker, args=(REDIS_URL, 4, q2))
        p1.start(); p2.start()
        p1.join(); p2.join()
        results = [q1.get(timeout=10), q2.get(timeout=10)]
        total_ok = sum(r[0] for r in results)
        total_blocked = sum(r[1] for r in results)
        assert total_ok == LIMITS["cnpj"]
        assert total_blocked == 8 - LIMITS["cnpj"]

    def test_thread_concurrency_single_key(self, clients):
        c1, _ = clients
        limiter = RedisRegistryRateLimiter(
            redis_url="", limits=LIMITS, key_prefix=PREFIX, client=c1
        )
        allowed = []
        blocked = []
        lock = threading.Lock()

        def work():
            try:
                limiter.acquire("cnpj", "thread-cnpj")
                with lock:
                    allowed.append(1)
            except RegistryRateLimitedError:
                with lock:
                    blocked.append(1)

        threads = [threading.Thread(target=work) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(allowed) == LIMITS["cnpj"]
        assert len(blocked) == 20 - LIMITS["cnpj"]

    def test_ttl_set_on_window_key(self, clients):
        c1, _ = clients
        limiter = RedisRegistryRateLimiter(
            redis_url="", limits=LIMITS, key_prefix=PREFIX, client=c1
        )
        limiter.acquire("cnpj", "ttl-cnpj")
        pttl = c1.pttl(f"{PREFIX}cnpj:ttl-cnpj")
        assert 0 < pttl <= 60_000

    def test_window_expires_and_counter_recovers(self, clients):
        c1, _ = clients
        limiter = RedisRegistryRateLimiter(
            redis_url="", limits=LIMITS, key_prefix=PREFIX,
            window_seconds=1.2, client=c1,
        )
        for _ in range(LIMITS["cnpj"]):
            limiter.acquire("cnpj", "exp-cnpj")
        with pytest.raises(RegistryRateLimitedError):
            limiter.acquire("cnpj", "exp-cnpj")
        time.sleep(1.5)
        limiter.acquire("cnpj", "exp-cnpj")  # recovered

    def test_redis_down_mid_operation_fails_closed(self, clients):
        import redis

        dead = redis.from_url(
            "redis://127.0.0.1:6398/0",
            decode_responses=True,
            socket_connect_timeout=0.3,
            socket_timeout=0.3,
        )
        limiter = RedisRegistryRateLimiter(
            redis_url="", limits=LIMITS, key_prefix=PREFIX, client=dead
        )
        with pytest.raises(RegistryLimiterUnavailableError):
            limiter.acquire("cnpj", "down-cnpj")

    def test_namespace_isolated_no_foreign_keys(self, clients):
        c1, _ = clients
        c1.set("other-service:key", "1")
        limiter = RedisRegistryRateLimiter(
            redis_url="", limits=LIMITS, key_prefix=PREFIX, client=c1
        )
        limiter.acquire("cnpj", "ns-cnpj")
        assert c1.get("other-service:key") == "1"
        keys = list(c1.scan_iter("*registry-rate-limit*"))
        assert all(k.startswith(PREFIX) for k in keys)
