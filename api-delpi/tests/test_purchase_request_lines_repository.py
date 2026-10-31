"""SUPPLIES-G2-FULL-YEAR-EXPORT-PERFORMANCE-001 — _fetch_key_batches.

Covers the bounded fan-out added to `_attach_orders_and_receipts`:
batch queries must fetch every batch (completeness), preserve batch
order (determinism) and fall back to a plain serial call when only one
batch exists — without touching a real TOTVS connection.
"""
from __future__ import annotations

import time

from app.infrastructure.persistence.totvs.supplies_repositories.purchase_request_lines_repository import (
    PurchaseRequestLinesRepository,
)


def _no_connect(repo):
    repo._connect = lambda: None  # type: ignore[attr-defined]
    repo._close = lambda **kw: None  # type: ignore[attr-defined]
    return repo


def _patch_repo_lifecycle(monkeypatch, execute):
    monkeypatch.setattr(
        PurchaseRequestLinesRepository, "_connect", lambda self: None
    )
    monkeypatch.setattr(
        PurchaseRequestLinesRepository, "_close", lambda self, **kw: None
    )
    monkeypatch.setattr(
        PurchaseRequestLinesRepository, "execute_query", execute
    )


def test_fetch_key_batches_fetches_every_batch_in_order(monkeypatch):
    def fake_execute(self, sql, params=()):
        return [{"key": p} for p in params]

    _patch_repo_lifecycle(monkeypatch, fake_execute)
    repo = _no_connect(PurchaseRequestLinesRepository())

    keys = [("01", str(i), "0001") for i in range(7)]
    rows = repo._fetch_key_batches(
        keys, 3, lambda batch: ("S", [k[1] for k in batch])
    )
    # 7 keys / batch_size=3 → batches [0,1,2],[3,4,5],[6]
    assert [r["key"] for r in rows] == [str(i) for i in range(7)]


def test_fetch_key_batches_serial_path_for_single_batch(monkeypatch):
    calls = []

    def fake_execute(self, sql, params=()):
        calls.append(params)
        return [{"n": len(params)}]

    _patch_repo_lifecycle(monkeypatch, fake_execute)
    repo = _no_connect(PurchaseRequestLinesRepository())

    rows = repo._fetch_key_batches(
        [("01", "1", "1"), ("01", "2", "1")], 50, lambda b: ("S", [1])
    )
    assert calls == [(1,)]
    assert rows == [{"n": 1}]


def test_fetch_key_batches_parallelizes_independent_batches(monkeypatch):
    """4 batches × 80ms each must complete well under the serial cost."""
    def fake_execute(self, sql, params=()):
        time.sleep(0.08)
        return [{"ok": True}]

    _patch_repo_lifecycle(monkeypatch, fake_execute)
    repo = _no_connect(PurchaseRequestLinesRepository())

    keys = [("01", str(i), "1") for i in range(4)]
    t0 = time.time()
    rows = repo._fetch_key_batches(keys, 1, lambda b: ("S", [1]))
    duration = time.time() - t0

    assert len(rows) == 4
    # serial would be >= 0.32s; bounded fan-out must finish faster
    assert duration < 0.32
