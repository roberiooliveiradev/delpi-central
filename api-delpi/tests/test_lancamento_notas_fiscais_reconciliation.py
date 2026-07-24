"""Conciliação LNF — matching, lote, idempotência e concorrência (fakes)."""

from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timezone
from typing import Any, Sequence
from uuid import uuid4

import pytest

from app.application.use_cases.lancamento_notas_fiscais.invoice_posting_use_cases import (
    Actor,
    RefreshInvoicePostingReconciliationUseCase,
    RunInvoicePostingReconciliationUseCase,
    resolve_reconciliation_limit,
)
from app.domain.services.lancamento_notas_fiscais.exceptions import (
    InvoicePostingErpQueryError,
    InvoicePostingForbiddenError,
    InvoicePostingReconciliationBusyError,
    InvoicePostingValidationError,
)
from app.domain.services.lancamento_notas_fiscais.fiscal_normalization import (
    DEFAULT_RECONCILIATION_LIMIT,
    MAX_RECONCILIATION_LIMIT,
    normalize_document,
)
from app.domain.services.lancamento_notas_fiscais.reconciliation_matching import (
    classify_candidates,
    fiscal_match_key_from_mapping,
    parse_erp_entry_date,
)


def _manager(**kwargs: Any) -> Actor:
    base = dict(
        user_id="u-manage",
        user_name="Gestor",
        has_manage=True,
    )
    base.update(kwargs)
    return Actor(**base)


def _seed_request(
    *,
    status: str = "pending",
    branch_code: str = "02",
    document: str = "12078",
    series: str = "",
    supplier_code: str = "000054",
    supplier_store: str = "03",
    received_at: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    doc = normalize_document(document)
    row = {
        "id": str(uuid4()),
        "branch_code": branch_code,
        "document_number": doc.document_number,
        "document_match_key": doc.document_match_key,
        "series": series,
        "supplier_code": supplier_code,
        "supplier_store": supplier_store,
        "supplier_name": "Fornecedor Teste",
        "supplier_short_name": None,
        "issue_date": "2026-07-20",
        "amount": 1100.0,
        "received_at": received_at or "2026-07-20T10:00:00+00:00",
        "observation": None,
        "status": status,
        "block_reason": "other" if status == "blocked" else None,
        "block_description": "pendência" if status == "blocked" else None,
        "created_by_user_id": "u-create",
        "created_by_name": "Criador",
        "assignee_user_id": "u-process" if status == "in_progress" else None,
        "assignee_name": "Processador" if status == "in_progress" else None,
        "cancelled_at": None,
        "cancelled_by_user_id": None,
        "cancelled_by_name": None,
        "cancel_justification": None,
        "completion_source": None,
        "sf1_recno": None,
        "erp_entry_date": None,
        "reconciled_at": None,
        "created_at": "2026-07-20T09:00:00+00:00",
        "updated_at": "2026-07-20T09:00:00+00:00",
    }
    row.update(extra)
    return row


class FakeSf1:
    def __init__(
        self,
        rows: list[dict[str, Any]] | None = None,
        *,
        fail: bool = False,
    ) -> None:
        self.rows = rows or []
        self.fail = fail
        self.call_count = 0
        self.last_keys: list[dict[str, Any]] | None = None

    def find_active_by_fiscal_keys(
        self, keys: Sequence[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        self.call_count += 1
        self.last_keys = list(keys)
        if self.fail:
            raise RuntimeError("TOTVS unavailable")
        wanted = {
            (
                str(k["branch_code"]).strip(),
                str(k["supplier_code"]).strip(),
                str(k["supplier_store"]).strip(),
                str(k["document_match_key"]).strip(),
                str(k.get("series") or "").strip().upper(),
            )
            for k in keys
        }
        out: list[dict[str, Any]] = []
        for row in self.rows:
            token = (
                row["branch_code"],
                row["supplier_code"],
                row["supplier_store"],
                row["document_match_key"],
                row["series"],
            )
            if token in wanted and not row.get("deleted"):
                out.append(dict(row))
        return out


class FakeRequests:
    def __init__(
        self,
        rows: list[dict[str, Any]] | None = None,
        *,
        lock_busy: bool = False,
        fail_persist: bool = False,
        cooldown_active: bool = False,
    ) -> None:
        self.rows: dict[str, dict[str, Any]] = {
            r["id"]: deepcopy(r) for r in (rows or [])
        }
        self.history: dict[str, list[dict[str, Any]]] = {
            rid: [] for rid in self.rows
        }
        self.lock_busy = lock_busy
        self._lock_held = False
        self.fail_persist = fail_persist
        self.cooldown_active = cooldown_active
        self.lock_acquire_count = 0
        self.lock_release_count = 0
        self.refresh_started_count = 0
        self.last_started_at: datetime | None = None

    def list_reconciliation_candidates(self, *, limit: int) -> list[dict[str, Any]]:
        eligible = {"pending", "in_progress", "blocked"}
        items = [r for r in self.rows.values() if r["status"] in eligible]
        items.sort(key=lambda r: (r.get("received_at") or "", r.get("created_at") or ""))
        return deepcopy(items[:limit])

    def mark_reconciled_posted_batch(self, items: Sequence[dict[str, Any]]) -> int:
        if self.fail_persist:
            raise RuntimeError("persist failed")
        # simula atomicidade: aplica tudo ou nada
        staging_rows = deepcopy(self.rows)
        staging_history = deepcopy(self.history)
        posted = 0
        try:
            for item in items:
                rid = item["request_id"]
                current = staging_rows.get(rid)
                if current is None or current["status"] not in {
                    "pending",
                    "in_progress",
                    "blocked",
                }:
                    continue
                current = {
                    **current,
                    "status": "posted",
                    "block_reason": None,
                    "block_description": None,
                    "completion_source": "auto",
                    "sf1_recno": item.get("sf1_recno"),
                    "erp_entry_date": (
                        item["erp_entry_date"].isoformat()
                        if hasattr(item.get("erp_entry_date"), "isoformat")
                        else item.get("erp_entry_date")
                    ),
                    "reconciled_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
                staging_rows[rid] = current
                staging_history.setdefault(rid, []).append(
                    {
                        "id": str(uuid4()),
                        "request_id": rid,
                        "event_type": "reconciled",
                        "actor_origin": "system",
                        "actor_user_id": None,
                        "actor_name": None,
                        "from_status": item.get("from_status"),
                        "to_status": "posted",
                        "changes": {"completion_source": "auto"},
                        "justification": None,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
                posted += 1
            self.rows = staging_rows
            self.history = staging_history
            return posted
        except Exception:
            raise

    def try_acquire_reconciliation_lock(self) -> bool:
        self.lock_acquire_count += 1
        if self.lock_busy or self._lock_held:
            return False
        self._lock_held = True
        return True

    def release_reconciliation_lock(self) -> None:
        self.lock_release_count += 1
        self._lock_held = False

    def is_reconciliation_refresh_cooldown_active(
        self, cooldown_seconds: int
    ) -> bool:
        if self.cooldown_active:
            return True
        if self.last_started_at is None:
            return False
        elapsed = (
            datetime.now(timezone.utc) - self.last_started_at
        ).total_seconds()
        return elapsed < cooldown_seconds

    def mark_reconciliation_refresh_started(self) -> None:
        self.refresh_started_count += 1
        self.last_started_at = datetime.now(timezone.utc)
        self.cooldown_active = True

    # stubs unused by reconciliation
    def find_active_by_fiscal_key(self, **kwargs: Any) -> None:
        return None

    def get_request(self, request_id: str) -> dict[str, Any] | None:
        row = self.rows.get(request_id)
        return deepcopy(row) if row else None

    def list_history(self, request_id: str) -> list[dict[str, Any]]:
        return deepcopy(self.history.get(request_id, []))


def test_normalize_document_nine_positions() -> None:
    doc = normalize_document("12078")
    assert doc.document_match_key == "000012078"
    assert doc.document_number == "000012078"


def test_series_empty_differs_from_zero() -> None:
    a = fiscal_match_key_from_mapping(
        {
            "branch_code": "02",
            "supplier_code": "000054",
            "supplier_store": "03",
            "document_match_key": "000012078",
            "series": "",
        }
    )
    b = fiscal_match_key_from_mapping(
        {
            "branch_code": "02",
            "supplier_code": "000054",
            "supplier_store": "03",
            "document_match_key": "000012078",
            "series": "0",
        }
    )
    assert a != b


def test_classify_ignores_deleted_via_absence() -> None:
    candidate = _seed_request()
    decisions = classify_candidates(
        [candidate],
        [],
    )
    assert decisions[0].outcome == "not_found"


def test_classify_ambiguous_not_matched() -> None:
    candidate = _seed_request()
    key = {
        "branch_code": candidate["branch_code"],
        "supplier_code": candidate["supplier_code"],
        "supplier_store": candidate["supplier_store"],
        "document_match_key": candidate["document_match_key"],
        "series": candidate["series"],
        "sf1_recno": 1,
        "erp_entry_date_raw": "20260724",
    }
    decisions = classify_candidates(
        [candidate],
        [{**key, "sf1_recno": 1}, {**key, "sf1_recno": 2}],
    )
    assert decisions[0].outcome == "ambiguous"


def test_exact_match_posts_and_history() -> None:
    pending = _seed_request(status="pending")
    in_progress = _seed_request(
        status="in_progress",
        document="999",
        received_at="2026-07-21T10:00:00+00:00",
    )
    blocked = _seed_request(
        status="blocked",
        document="888",
        received_at="2026-07-22T10:00:00+00:00",
    )
    posted = _seed_request(
        status="posted",
        document="777",
        received_at="2026-07-19T10:00:00+00:00",
        completion_source="manual",
        sf1_recno=99,
    )
    cancelled = _seed_request(
        status="cancelled",
        document="666",
        cancel_justification="ok",
        cancelled_at="2026-07-19T11:00:00+00:00",
        cancelled_by_user_id="u",
        cancelled_by_name="U",
    )

    sf1 = FakeSf1(
        [
            {
                "branch_code": pending["branch_code"],
                "supplier_code": pending["supplier_code"],
                "supplier_store": pending["supplier_store"],
                "document_match_key": pending["document_match_key"],
                "series": "",
                "sf1_recno": 12345,
                "erp_entry_date_raw": "20260724",
            },
            {
                "branch_code": in_progress["branch_code"],
                "supplier_code": in_progress["supplier_code"],
                "supplier_store": in_progress["supplier_store"],
                "document_match_key": in_progress["document_match_key"],
                "series": "",
                "sf1_recno": 12346,
                "erp_entry_date_raw": "20260724",
            },
            {
                "branch_code": blocked["branch_code"],
                "supplier_code": blocked["supplier_code"],
                "supplier_store": blocked["supplier_store"],
                "document_match_key": blocked["document_match_key"],
                "series": "",
                "sf1_recno": 12347,
                "erp_entry_date_raw": "20260724",
            },
            # série 0 não casa com série vazia do pending
            {
                "branch_code": pending["branch_code"],
                "supplier_code": pending["supplier_code"],
                "supplier_store": pending["supplier_store"],
                "document_match_key": pending["document_match_key"],
                "series": "0",
                "sf1_recno": 99999,
                "erp_entry_date_raw": "20260724",
            },
        ]
    )
    repo = FakeRequests([pending, in_progress, blocked, posted, cancelled])
    uc = RunInvoicePostingReconciliationUseCase(repo, sf1)

    summary = uc.execute(actor=_manager())
    assert summary == {
        "examined": 3,
        "matched": 3,
        "posted": 3,
        "not_found": 0,
        "ambiguous": 0,
        "failed": 0,
    }
    assert sf1.call_count == 1
    assert repo.rows[pending["id"]]["status"] == "posted"
    assert repo.rows[pending["id"]]["completion_source"] == "auto"
    assert repo.rows[pending["id"]]["sf1_recno"] == 12345
    assert repo.rows[pending["id"]]["erp_entry_date"] == "2026-07-24"
    assert repo.rows[pending["id"]]["block_reason"] is None
    assert repo.rows[pending["id"]]["created_by_user_id"] == "u-create"
    assert repo.rows[in_progress["id"]]["assignee_user_id"] == "u-process"
    hist = repo.list_history(pending["id"])
    assert len(hist) == 1
    assert hist[0]["event_type"] == "reconciled"
    assert hist[0]["actor_origin"] == "system"
    assert repo.rows[posted["id"]]["status"] == "posted"
    assert repo.rows[posted["id"]]["sf1_recno"] == 99
    assert repo.rows[cancelled["id"]]["status"] == "cancelled"
    assert repo.lock_release_count == 1


def test_idempotent_second_run() -> None:
    pending = _seed_request()
    sf1_row = {
        "branch_code": pending["branch_code"],
        "supplier_code": pending["supplier_code"],
        "supplier_store": pending["supplier_store"],
        "document_match_key": pending["document_match_key"],
        "series": "",
        "sf1_recno": 10,
        "erp_entry_date_raw": "20260724",
    }
    repo = FakeRequests([pending])
    sf1 = FakeSf1([sf1_row])
    uc = RunInvoicePostingReconciliationUseCase(repo, sf1)
    first = uc.execute(actor=_manager())
    second = uc.execute(actor=_manager())
    assert first["posted"] == 1
    assert second["examined"] == 0
    assert second["posted"] == 0
    assert len(repo.list_history(pending["id"])) == 1


def test_ambiguous_not_posted() -> None:
    pending = _seed_request()
    key = {
        "branch_code": pending["branch_code"],
        "supplier_code": pending["supplier_code"],
        "supplier_store": pending["supplier_store"],
        "document_match_key": pending["document_match_key"],
        "series": "",
        "erp_entry_date_raw": "20260724",
    }
    repo = FakeRequests([pending])
    sf1 = FakeSf1([{**key, "sf1_recno": 1}, {**key, "sf1_recno": 2}])
    summary = RunInvoicePostingReconciliationUseCase(repo, sf1).execute(
        actor=_manager()
    )
    assert summary["ambiguous"] == 1
    assert summary["posted"] == 0
    assert repo.rows[pending["id"]]["status"] == "pending"


def test_not_found() -> None:
    pending = _seed_request()
    repo = FakeRequests([pending])
    summary = RunInvoicePostingReconciliationUseCase(repo, FakeSf1([])).execute(
        actor=_manager()
    )
    assert summary["not_found"] == 1
    assert summary["posted"] == 0


def test_totvs_failure_no_partial_updates() -> None:
    pending = _seed_request()
    repo = FakeRequests([pending])
    sf1 = FakeSf1(fail=True)
    with pytest.raises(InvoicePostingErpQueryError):
        RunInvoicePostingReconciliationUseCase(repo, sf1).execute(actor=_manager())
    assert repo.rows[pending["id"]]["status"] == "pending"
    assert repo.lock_release_count == 1


def test_persist_failure_rolls_back_atomic_fake() -> None:
    pending = _seed_request()
    repo = FakeRequests([pending], fail_persist=True)
    sf1 = FakeSf1(
        [
            {
                "branch_code": pending["branch_code"],
                "supplier_code": pending["supplier_code"],
                "supplier_store": pending["supplier_store"],
                "document_match_key": pending["document_match_key"],
                "series": "",
                "sf1_recno": 1,
                "erp_entry_date_raw": "20260724",
            }
        ]
    )
    with pytest.raises(Exception):
        RunInvoicePostingReconciliationUseCase(repo, sf1).execute(actor=_manager())
    assert repo.rows[pending["id"]]["status"] == "pending"
    assert repo.lock_release_count == 1


def test_concurrent_lock_conflict() -> None:
    repo = FakeRequests([_seed_request()], lock_busy=True)
    with pytest.raises(InvoicePostingReconciliationBusyError):
        RunInvoicePostingReconciliationUseCase(repo, FakeSf1([])).execute(
            actor=_manager()
        )
    assert repo.lock_release_count == 0


def test_limit_invalid() -> None:
    with pytest.raises(InvoicePostingValidationError):
        resolve_reconciliation_limit(0)
    with pytest.raises(InvoicePostingValidationError):
        resolve_reconciliation_limit(MAX_RECONCILIATION_LIMIT + 1)
    assert resolve_reconciliation_limit(None) == DEFAULT_RECONCILIATION_LIMIT


def test_without_manage_forbidden() -> None:
    repo = FakeRequests([_seed_request()])
    with pytest.raises(InvoicePostingForbiddenError):
        RunInvoicePostingReconciliationUseCase(repo, FakeSf1([])).execute(
            actor=Actor(user_id="x", user_name="X", has_view=True)
        )


def test_parse_erp_entry_date() -> None:
    assert parse_erp_entry_date("20260724") == date(2026, 7, 24)
    assert parse_erp_entry_date("") is None


def test_deleted_sf1_ignored_by_repository_filter() -> None:
    pending = _seed_request()
    sf1 = FakeSf1(
        [
            {
                "branch_code": pending["branch_code"],
                "supplier_code": pending["supplier_code"],
                "supplier_store": pending["supplier_store"],
                "document_match_key": pending["document_match_key"],
                "series": "",
                "sf1_recno": 1,
                "erp_entry_date_raw": "20260724",
                "deleted": True,
            }
        ]
    )
    repo = FakeRequests([pending])
    summary = RunInvoicePostingReconciliationUseCase(repo, sf1).execute(
        actor=_manager()
    )
    assert summary["not_found"] == 1
    assert repo.rows[pending["id"]]["status"] == "pending"


def _access_actor(**kwargs: Any) -> Actor:
    base = dict(user_id="u-access", user_name="Operador", has_access=True)
    base.update(kwargs)
    return Actor(**base)


def test_refresh_reuses_batch_and_returns_minimal_payload() -> None:
    pending = _seed_request()
    sf1 = FakeSf1(
        [
            {
                "branch_code": pending["branch_code"],
                "supplier_code": pending["supplier_code"],
                "supplier_store": pending["supplier_store"],
                "document_match_key": pending["document_match_key"],
                "series": "",
                "sf1_recno": 42,
                "erp_entry_date_raw": "20260724",
            }
        ]
    )
    repo = FakeRequests([pending])
    run_uc = RunInvoicePostingReconciliationUseCase(repo, sf1)
    refresh = RefreshInvoicePostingReconciliationUseCase(repo, run_uc)

    result = refresh.execute(actor=_access_actor())
    assert result == {"status": "completed", "updated": 1}
    assert set(result.keys()) == {"status", "updated"}
    assert repo.rows[pending["id"]]["status"] == "posted"
    assert sf1.call_count == 1
    assert repo.refresh_started_count == 1


def test_refresh_skipped_on_cooldown() -> None:
    repo = FakeRequests([_seed_request()], cooldown_active=True)
    run_uc = RunInvoicePostingReconciliationUseCase(repo, FakeSf1([]))
    result = RefreshInvoicePostingReconciliationUseCase(repo, run_uc).execute(
        actor=_access_actor()
    )
    assert result == {"status": "skipped", "updated": 0}
    assert repo.lock_acquire_count == 0


def test_refresh_skipped_on_concurrent_lock() -> None:
    repo = FakeRequests([_seed_request()], lock_busy=True)
    run_uc = RunInvoicePostingReconciliationUseCase(repo, FakeSf1([]))
    result = RefreshInvoicePostingReconciliationUseCase(repo, run_uc).execute(
        actor=_access_actor()
    )
    assert result == {"status": "skipped", "updated": 0}


def test_refresh_failed_totvs_no_partial() -> None:
    pending = _seed_request()
    repo = FakeRequests([pending])
    run_uc = RunInvoicePostingReconciliationUseCase(repo, FakeSf1(fail=True))
    result = RefreshInvoicePostingReconciliationUseCase(repo, run_uc).execute(
        actor=_access_actor()
    )
    assert result == {"status": "failed", "updated": 0}
    assert repo.rows[pending["id"]]["status"] == "pending"
    assert repo.lock_release_count == 1


def test_refresh_idempotent_second_call_skipped_by_cooldown() -> None:
    pending = _seed_request()
    sf1_row = {
        "branch_code": pending["branch_code"],
        "supplier_code": pending["supplier_code"],
        "supplier_store": pending["supplier_store"],
        "document_match_key": pending["document_match_key"],
        "series": "",
        "sf1_recno": 7,
        "erp_entry_date_raw": "20260724",
    }
    repo = FakeRequests([pending])
    run_uc = RunInvoicePostingReconciliationUseCase(repo, FakeSf1([sf1_row]))
    refresh = RefreshInvoicePostingReconciliationUseCase(repo, run_uc)
    first = refresh.execute(actor=_access_actor())
    second = refresh.execute(actor=_access_actor())
    assert first["status"] == "completed"
    assert second == {"status": "skipped", "updated": 0}
    assert len(repo.list_history(pending["id"])) == 1


def test_refresh_without_access_forbidden() -> None:
    repo = FakeRequests([_seed_request()])
    run_uc = RunInvoicePostingReconciliationUseCase(repo, FakeSf1([]))
    with pytest.raises(InvoicePostingForbiddenError):
        RefreshInvoicePostingReconciliationUseCase(repo, run_uc).execute(
            actor=Actor(user_id="x", user_name="X")
        )


def test_refresh_reuses_execute_batch() -> None:
    pending = _seed_request()
    repo = FakeRequests([pending])
    sf1 = FakeSf1([])
    run_uc = RunInvoicePostingReconciliationUseCase(repo, sf1)
    calls: list[int] = []
    original = run_uc.execute_batch

    def wrapped(*, limit: int | None = None):
        calls.append(1)
        return original(limit=limit)

    run_uc.execute_batch = wrapped  # type: ignore[method-assign]
    RefreshInvoicePostingReconciliationUseCase(repo, run_uc).execute(
        actor=_access_actor()
    )
    assert calls == [1]
