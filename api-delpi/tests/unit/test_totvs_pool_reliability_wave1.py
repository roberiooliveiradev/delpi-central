"""Wave 1 — confiabilidade do pool TOTVS e singleflight.

Cenários: criação lenta fora do lock, falha de abertura, concorrência acima
da capacidade, fila saturada, falha de cursor/query, descarte/recuperação,
rollback na devolução e ausência de vazamento.
"""
from __future__ import annotations

import threading
import time
from unittest.mock import MagicMock

import pytest

from app.infrastructure.providers.totvs import connection_pool as mod
from app.infrastructure.cache.singleflight import Singleflight


def _fake_conn() -> MagicMock:
    conn = MagicMock()
    conn.cursor.return_value = MagicMock()
    return conn


@pytest.fixture
def pool(monkeypatch):
    monkeypatch.setattr(mod, "TOTVS_POOL_ENABLED", True)
    monkeypatch.setattr(mod, "TOTVS_POOL_MAX_SIZE", 2)
    monkeypatch.setattr(mod, "TOTVS_POOL_ACQUIRE_TIMEOUT", 5.0)
    monkeypatch.setattr(mod, "TOTVS_POOL_MAX_WAITERS", 2)
    monkeypatch.setattr(mod, "create_totvs_connection", _fake_conn)
    with mod._pool_lock:
        mod._pool = None
    p = mod.get_totvs_connection_pool()
    yield p
    with mod._pool_lock:
        mod._pool = None


def test_slow_create_does_not_block_other_acquires(monkeypatch, pool):
    gate = threading.Event()

    def slow_create():
        gate.wait(2.0)
        return _fake_conn()

    monkeypatch.setattr(mod, "create_totvs_connection", slow_create)
    results, errors = [], []

    t = threading.Thread(target=lambda: results.append(pool.acquire()), daemon=True)
    t.start()
    time.sleep(0.05)
    # segundo acquire reserva e cria em paralelo — não fica preso no lock
    t2 = threading.Thread(
        target=lambda: results.append(pool.acquire()), daemon=True
    )
    t2.start()
    time.sleep(0.2)
    # acquires de waiters (não criação) também não ficam presos pelo create lento
    def _waiter():
        try:
            pool.acquire(timeout_seconds=0.2)
        except TimeoutError:
            errors.append("timeout")

    t3 = threading.Thread(target=_waiter, daemon=True)
    t3.start()
    t3.join(timeout=2)
    gate.set()
    t.join(timeout=3); t2.join(timeout=3)
    assert len(results) == 2
    assert pool.stats()["created"] == 2


def test_create_failure_decrements_created_and_recovers(monkeypatch, pool):
    calls = []
    def flaky():
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError("db indisponível")
        return _fake_conn()
    monkeypatch.setattr(mod, "create_totvs_connection", flaky)

    with pytest.raises(RuntimeError):
        pool.acquire()
    assert pool.stats()["created"] == 0
    conn = pool.acquire()
    assert conn is not None
    assert pool.stats()["created"] == 1


def test_never_exceeds_max_size_under_concurrency(pool):
    acquired, lock = [], threading.Lock()

    def worker():
        try:
            c = pool.acquire(timeout_seconds=5.0)
            with lock:
                acquired.append(c)
            time.sleep(0.02)
        except TimeoutError:
            with lock:
                acquired.append("timeout")

    threads = [threading.Thread(target=worker, daemon=True) for _ in range(12)]
    for t in threads:
        t.start()
    time.sleep(0.4)
    stats = pool.stats()
    assert stats["created"] <= 2
    assert stats["rejected_total"] >= 1  # fila saturada rejeita na hora
    for t in threads:
        t.join(timeout=6)
    # devolve tudo que conseguiu
    for c in acquired:
        if c != "timeout":
            pool.release(c)
    assert pool.stats()["in_use"] == 0


def test_release_rolls_back_and_returns_healthy(pool):
    conn = pool.acquire()
    pool.release(conn)
    conn.rollback.assert_called_once()
    assert pool.stats()["available"] == 1
    assert pool.acquire(timeout_seconds=0.5) is conn


def test_release_discards_when_healthcheck_fails(pool):
    bad = _fake_conn()
    bad.cursor.side_effect = RuntimeError("conn morta")
    pool.release(bad)
    stats = pool.stats()
    assert stats["discards_total"] == 1
    assert stats["created"] == 0  # vaga liberada — nova acquire recria


def test_waiter_times_out_and_does_not_leak(pool):
    a = pool.acquire(); b = pool.acquire()
    with pytest.raises(TimeoutError):
        pool.acquire(timeout_seconds=0.05)
    assert pool.stats()["waiting"] == 0
    pool.release(a); pool.release(b)


# --- BaseRepository: sem vazamento em falha de cursor/close ---

def test_base_repository_releases_on_cursor_failure(monkeypatch):
    from app.infrastructure.persistence.totvs import base_repository as br

    conn = _fake_conn()
    conn.cursor.side_effect = RuntimeError("cursor quebrou")
    released = []
    monkeypatch.setattr(br, "get_connection", lambda: conn)
    monkeypatch.setattr(
        br, "release_connection", lambda c, discard=False: released.append((c, discard))
    )
    repo = br.BaseRepository()
    with pytest.raises(Exception):
        with repo:
            pass
    assert released == [(conn, True)]  # descartado, não devolvido sadio


def test_base_repository_closes_connection_even_if_cursor_close_fails(monkeypatch):
    from app.infrastructure.persistence.totvs import base_repository as br

    conn = _fake_conn()
    cursor = MagicMock()
    cursor.close.side_effect = RuntimeError("close falhou")
    conn.cursor.return_value = cursor
    released = []
    monkeypatch.setattr(br, "get_connection", lambda: conn)
    monkeypatch.setattr(
        br, "release_connection", lambda c, discard=False: released.append(c)
    )
    repo = br.BaseRepository()
    with repo:
        pass
    assert released == [conn]


# --- Singleflight: espera limitada ---

def test_singleflight_follower_times_out_when_leader_stuck():
    sf = Singleflight(wait_timeout_seconds=0.05)
    leader_started = threading.Event()

    def slow():
        leader_started.set()
        time.sleep(5)
        return "x"

    errors = []
    t = threading.Thread(
        target=lambda: sf.do("k", slow), daemon=True
    )
    t.start()
    leader_started.wait(2)
    with pytest.raises(TimeoutError):
        sf.do("k", slow)


def test_singleflight_follower_gets_leader_result():
    sf = Singleflight(wait_timeout_seconds=2.0)
    calls = []

    def compute():
        calls.append(1)
        time.sleep(0.05)
        return 42

    results = []
    threads = [
        threading.Thread(target=lambda: results.append(sf.do("k", compute)))
        for _ in range(4)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5)
    assert results == [42, 42, 42, 42]
    assert len(calls) == 1


def test_singleflight_follower_gets_leader_error():
    sf = Singleflight(wait_timeout_seconds=2.0)

    def boom():
        time.sleep(0.02)
        raise ValueError("falhou")

    out = []
    t1 = threading.Thread(
        target=lambda: out.append(("lead", _safe(sf, "k", boom))), daemon=True
    )
    t1.start()
    time.sleep(0.01)
    out.append(("follow", _safe(sf, "k", boom)))
    t1.join(timeout=5)
    assert all(isinstance(r, ValueError) for _, r in out)


def _safe(sf, key, fn):
    try:
        return sf.do(key, fn)
    except Exception as exc:  # noqa: BLE001
        return exc
