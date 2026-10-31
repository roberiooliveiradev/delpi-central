"""Tests for the R12/R15 closing-state markers read (doc 129)."""

from __future__ import annotations

import pytest

from app.application.dto.financeiro_closing_state.closing_state_request import (
    ClosingStateRequest,
)
from app.application.security.stock_inventory_scope import (
    StockInventoryScope,
    StockInventoryScopeUnavailableError,
)
from app.application.use_cases.financeiro_closing_state.get_closing_state_use_case import (
    GetClosingStateUseCase,
)


class _FakeRepo:
    def __init__(self, *, counts=None, last_dates=None, ulmes=None,
                 writes=None):
        self._counts = counts or {}
        self._last_dates = last_dates or {}
        self._ulmes = ulmes or {}
        self._writes = writes or {}

    def snapshot_branch_counts(self, *, snapshot_date, branches):
        self.snapshot_date = snapshot_date
        return self._counts

    def last_snapshot_dates(self, *, branches):
        return self._last_dates

    def mv_ulmes_values(self, *, branches):
        return self._ulmes

    def ttat_write_window(self, *, log_table, field_name,
                          window_start, window_end):
        return self._writes.get((log_table, field_name), {})


class _Resolver:
    def __init__(self, resolved=True):
        self._resolved = resolved

    def resolve(self, *, user_subject):
        return StockInventoryScope(
            resolved=self._resolved, reason="test"
        )


def _uc(repo, resolved=True):
    return GetClosingStateUseCase(
        repository=repo, scope_resolver=_Resolver(resolved)
    )


def test_request_validates_period_and_branch():
    req = ClosingStateRequest.from_query(period="2026-09", branch="02")
    assert req.snapshot_date() == "20260930"
    assert req.requested_branches() == ("02",)
    with pytest.raises(ValueError):
        ClosingStateRequest.from_query(period="2026-13", branch="01")
    with pytest.raises(ValueError):
        ClosingStateRequest.from_query(period="2026-09", branch="03")


def test_use_case_returns_raw_markers_per_branch():
    repo = _FakeRepo(
        counts={"01": 4812},
        last_dates={"01": "20260930", "02": "20260831"},
        ulmes={"01": "20260930", "02": "20260930"},
        writes={
            ("SB1010_TTAT_LOG", "B1_CUSTD"): {
                "write_count": 14733,
                "first_at": "2026-09-30 14:36:00",
                "last_at": "2026-10-01 03:54:00",
            },
        },
    )
    req = ClosingStateRequest.from_query(period="2026-09", branch="all")
    data = _uc(repo).execute(req, user_subject="u1")
    b1 = data["branches"]["01"]
    b2 = data["branches"]["02"]
    assert b1["snapshot"]["available"] is True
    assert b1["snapshot"]["rowCount"] == 4812
    assert b2["snapshot"]["available"] is False
    assert b2["snapshot"]["rowCount"] is None
    assert b2["snapshot"]["lastAvailableDate"] == "2026-08-31"
    assert b1["cutoffMarker"]["value"] == "20260930"
    ev = b1["evidence"]["replacementCostWrites"]
    assert ev["writeCount"] == 14733
    assert ev["firstAt"] == "2026-09-30 14:36:00"
    assert data["provenance"]["writerPending"] is True


def test_use_case_fail_closed_without_scope():
    repo = _FakeRepo()
    req = ClosingStateRequest.from_query(period="2026-09", branch="all")
    with pytest.raises(StockInventoryScopeUnavailableError):
        _uc(repo, resolved=False).execute(req, user_subject="u1")
