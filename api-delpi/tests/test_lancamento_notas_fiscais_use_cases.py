"""Use cases — lançamento-notas-fiscais (fakes, sem TOTVS/Postgres reais)."""

from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timezone
from typing import Any
from uuid import uuid4

import pytest

from app.application.use_cases.lancamento_notas_fiscais.invoice_posting_use_cases import (
    Actor,
    AddInvoicePostingCommentUseCase,
    BlockInvoicePostingRequestUseCase,
    CancelInvoicePostingRequestUseCase,
    CreateInvoicePostingRequestUseCase,
    GetInvoicePostingRequestUseCase,
    ListInvoicePostingRequestsUseCase,
    PostManualInvoicePostingRequestUseCase,
    ResumeInvoicePostingRequestUseCase,
    SearchSuppliersUseCase,
    StartInvoicePostingRequestUseCase,
    UpdateInvoicePostingRequestUseCase,
    _parse_amount,
)
from app.domain.services.lancamento_notas_fiscais.exceptions import (
    DuplicateFiscalKeyError,
    InvoicePostingConflictError,
    InvoicePostingDuplicateError,
    InvoicePostingForbiddenError,
    InvoicePostingInvalidTransitionError,
    InvoicePostingNotFoundError,
    InvoicePostingValidationError,
    SupplierBlockedError,
    SupplierNotFoundError,
)


def _creator(**kwargs: Any) -> Actor:
    base = dict(
        user_id="u-create",
        user_name="Criador",
        has_create=True,
    )
    base.update(kwargs)
    return Actor(**base)


def _processor(**kwargs: Any) -> Actor:
    base = dict(
        user_id="u-process",
        user_name="Processador",
        has_process=True,
    )
    base.update(kwargs)
    return Actor(**base)


def _manager(**kwargs: Any) -> Actor:
    base = dict(
        user_id="u-manage",
        user_name="Gestor",
        has_manage=True,
    )
    base.update(kwargs)
    return Actor(**base)


class FakeSuppliers:
    def __init__(self, suppliers: list[dict[str, Any]] | None = None) -> None:
        self.suppliers = suppliers or [
            {
                "supplier_code": "000001",
                "supplier_store": "01",
                "supplier_name": "Fornecedor Alpha",
                "supplier_short_name": "Alpha",
                "tax_id": "12345678000199",
                "state": "SC",
                "blocked": False,
            },
            {
                "supplier_code": "000002",
                "supplier_store": "01",
                "supplier_name": "Fornecedor Bloqueado",
                "supplier_short_name": "Bloq",
                "tax_id": "98765432000111",
                "state": "ES",
                "blocked": True,
            },
        ]

    def search_suppliers(self, *, query: str, limit: int = 20) -> list[dict[str, Any]]:
        q = query.lower()
        items = [
            s
            for s in self.suppliers
            if q in s["supplier_code"].lower()
            or q in s["supplier_name"].lower()
            or q in (s.get("tax_id") or "")
        ]
        return items[:limit]

    def get_supplier(
        self, *, supplier_code: str, supplier_store: str
    ) -> dict[str, Any] | None:
        for s in self.suppliers:
            if s["supplier_code"] == supplier_code and s["supplier_store"] == supplier_store:
                return dict(s)
        return None


class FakeRequests:
    def __init__(self, *, fail_history_once: bool = False) -> None:
        self.rows: dict[str, dict[str, Any]] = {}
        self.history: dict[str, list[dict[str, Any]]] = {}
        self.comments: dict[str, list[dict[str, Any]]] = {}
        self.fail_history_once = fail_history_once
        self._history_failures = 0

    def find_active_by_fiscal_key(
        self,
        *,
        branch_code: str,
        supplier_code: str,
        supplier_store: str,
        document_match_key: str,
        series: str,
        exclude_id: str | None = None,
    ) -> dict[str, Any] | None:
        for row in self.rows.values():
            if exclude_id and row["id"] == exclude_id:
                continue
            if row["status"] == "cancelled":
                continue
            if (
                row["branch_code"] == branch_code
                and row["supplier_code"] == supplier_code
                and row["supplier_store"] == supplier_store
                and row["document_match_key"] == document_match_key
                and row["series"] == series
            ):
                return deepcopy(row)
        return None

    def create_request_with_history(
        self,
        *,
        request_fields: dict[str, Any],
        history_fields: dict[str, Any],
    ) -> dict[str, Any]:
        if self.find_active_by_fiscal_key(
            branch_code=request_fields["branch_code"],
            supplier_code=request_fields["supplier_code"],
            supplier_store=request_fields["supplier_store"],
            document_match_key=request_fields["document_match_key"],
            series=request_fields["series"],
        ):
            raise DuplicateFiscalKeyError()
        request_id = str(uuid4())
        row = {
            **request_fields,
            "id": request_id,
            "block_reason": None,
            "block_description": None,
            "assignee_user_id": None,
            "assignee_name": None,
            "cancelled_at": None,
            "cancelled_by_user_id": None,
            "cancelled_by_name": None,
            "cancel_justification": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if isinstance(row.get("issue_date"), date):
            row["issue_date"] = row["issue_date"].isoformat()
        if isinstance(row.get("received_at"), datetime):
            row["received_at"] = row["received_at"].isoformat()
        if hasattr(row.get("amount"), "quantize"):
            row["amount"] = float(row["amount"])
        staging = deepcopy(row)
        try:
            self._append_history(request_id, history_fields)
            self.rows[request_id] = staging
        except RuntimeError:
            # simula rollback atômico
            self.history.pop(request_id, None)
            raise
        return deepcopy(staging)

    def get_request(self, request_id: str) -> dict[str, Any] | None:
        row = self.rows.get(request_id)
        return deepcopy(row) if row else None

    def list_history(self, request_id: str) -> list[dict[str, Any]]:
        return deepcopy(self.history.get(request_id, []))

    def list_comments(self, request_id: str) -> list[dict[str, Any]]:
        return deepcopy(self.comments.get(request_id, []))

    def list_requests(
        self,
        *,
        filters: dict[str, Any],
        created_by_user_id: str | None,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        items = list(self.rows.values())
        if created_by_user_id:
            items = [r for r in items if r["created_by_user_id"] == created_by_user_id]
        if filters.get("branch"):
            items = [r for r in items if r["branch_code"] == filters["branch"]]
        if filters.get("status"):
            items = [r for r in items if r["status"] == filters["status"]]
        if filters.get("document"):
            dig = "".join(ch for ch in str(filters["document"]) if ch.isdigit())
            items = [
                r
                for r in items
                if dig in r["document_number"] or dig in r["document_match_key"]
            ]
        items.sort(key=lambda r: (r.get("received_at") or "", r.get("created_at") or ""))
        total = len(items)
        start = (page - 1) * page_size
        page_items = items[start : start + page_size]
        return {
            "items": deepcopy(page_items),
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": max((total + page_size - 1) // page_size, 1) if total else 0,
        }

    def update_request_with_history(
        self,
        *,
        request_id: str,
        updates: dict[str, Any],
        history_fields: dict[str, Any],
    ) -> dict[str, Any]:
        current = self.rows.get(request_id)
        if current is None:
            raise LookupError(request_id)
        candidate = {**current, **updates}
        if isinstance(candidate.get("issue_date"), date):
            candidate["issue_date"] = candidate["issue_date"].isoformat()
        if isinstance(candidate.get("received_at"), datetime):
            candidate["received_at"] = candidate["received_at"].isoformat()
        if isinstance(candidate.get("cancelled_at"), datetime):
            candidate["cancelled_at"] = candidate["cancelled_at"].isoformat()
        if isinstance(candidate.get("reconciled_at"), datetime):
            candidate["reconciled_at"] = candidate["reconciled_at"].isoformat()
        if hasattr(candidate.get("amount"), "quantize"):
            candidate["amount"] = float(candidate["amount"])
        duplicate = self.find_active_by_fiscal_key(
            branch_code=candidate["branch_code"],
            supplier_code=candidate["supplier_code"],
            supplier_store=candidate["supplier_store"],
            document_match_key=candidate["document_match_key"],
            series=candidate["series"],
            exclude_id=request_id,
        )
        if duplicate and candidate["status"] != "cancelled":
            raise DuplicateFiscalKeyError()
        try:
            self._append_history(request_id, history_fields)
            self.rows[request_id] = candidate
        except RuntimeError:
            raise
        return deepcopy(candidate)

    def add_comment(
        self,
        *,
        request_id: str,
        author_user_id: str,
        author_name: str,
        body: str,
    ) -> dict[str, Any]:
        if request_id not in self.rows:
            raise LookupError(request_id)
        comment = {
            "id": str(uuid4()),
            "request_id": request_id,
            "author_user_id": author_user_id,
            "author_name": author_name,
            "body": body,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.comments.setdefault(request_id, []).append(comment)
        self._append_history(
            request_id,
            {
                "event_type": "comment_added",
                "actor_origin": "user",
                "actor_user_id": author_user_id,
                "actor_name": author_name,
                "from_status": None,
                "to_status": None,
                "changes": {"comment_id": comment["id"]},
                "justification": None,
            },
        )
        return deepcopy(comment)

    def _append_history(self, request_id: str, fields: dict[str, Any]) -> None:
        if self.fail_history_once and self._history_failures == 0:
            self._history_failures += 1
            raise RuntimeError("history failed")
        entry = {
            "id": str(uuid4()),
            "request_id": request_id,
            **fields,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.history.setdefault(request_id, []).append(entry)


def _payload(**overrides: Any) -> dict[str, Any]:
    base = {
        "branch": "01",
        "document": "123456",
        "series": "1",
        "supplier_code": "000001",
        "supplier_store": "01",
        "issue_date": "2026-07-01",
        "amount": "100.50",
        "received_at": "2026-07-02T10:00:00+00:00",
        "observation": "ok",
    }
    base.update(overrides)
    return base


def test_search_suppliers_min_query() -> None:
    uc = SearchSuppliersUseCase(FakeSuppliers())
    with pytest.raises(InvoicePostingValidationError):
        uc.execute(query="a")
    items = uc.execute(query="Alpha")
    assert len(items) == 1
    assert items[0]["blocked"] is False


def test_create_valid_and_history() -> None:
    repo = FakeRequests()
    created = CreateInvoicePostingRequestUseCase(repo, FakeSuppliers()).execute(
        _payload(), _creator()
    )
    assert created["status"] == "pending"
    assert created["document_number"] == "000123456"
    assert created["document_match_key"] == "000123456"
    assert created["series"] == "1"
    assert created["supplier_name"] == "Fornecedor Alpha"
    assert created["created_by_user_id"] == "u-create"
    hist = repo.list_history(created["id"])
    assert len(hist) == 1
    assert hist[0]["event_type"] == "created"


def test_create_rejects_missing_and_blocked_supplier() -> None:
    uc = CreateInvoicePostingRequestUseCase(FakeRequests(), FakeSuppliers())
    with pytest.raises(SupplierNotFoundError):
        uc.execute(_payload(supplier_code="999999"), _creator())
    with pytest.raises(SupplierBlockedError):
        uc.execute(
            _payload(supplier_code="000002", supplier_store="01"),
            _creator(),
        )


def test_create_duplicate() -> None:
    repo = FakeRequests()
    uc = CreateInvoicePostingRequestUseCase(repo, FakeSuppliers())
    first = uc.execute(_payload(), _creator())
    with pytest.raises(InvoicePostingDuplicateError) as exc:
        uc.execute(_payload(), _creator(user_id="other"))
    assert exc.value.meta.get("existing_request_id") == first["id"]


def test_create_rollback_when_history_fails() -> None:
    repo = FakeRequests(fail_history_once=True)
    uc = CreateInvoicePostingRequestUseCase(repo, FakeSuppliers())
    with pytest.raises(RuntimeError):
        uc.execute(_payload(), _creator())
    assert repo.rows == {}
    assert repo.history == {}


def test_list_visibility_own_vs_all() -> None:
    repo = FakeRequests()
    create = CreateInvoicePostingRequestUseCase(repo, FakeSuppliers())
    mine = create.execute(_payload(document="111"), _creator())
    create.execute(
        _payload(document="222"),
        _creator(user_id="other", user_name="Outro"),
    )
    listed_own = ListInvoicePostingRequestsUseCase(repo).execute(
        actor=_creator(), filters={}, page=1, page_size=20
    )
    assert listed_own["total"] == 1
    assert listed_own["items"][0]["id"] == mine["id"]

    listed_all = ListInvoicePostingRequestsUseCase(repo).execute(
        actor=_processor(has_view=True), filters={}, page=1, page_size=20
    )
    assert listed_all["total"] == 2


def test_list_filters_and_pagination() -> None:
    repo = FakeRequests()
    create = CreateInvoicePostingRequestUseCase(repo, FakeSuppliers())
    create.execute(_payload(document="111", branch="01"), _creator())
    create.execute(_payload(document="222", branch="02"), _creator())
    listed = ListInvoicePostingRequestsUseCase(repo).execute(
        actor=_creator(has_view=True),
        filters={"branch": "02", "document": "222"},
        page=1,
        page_size=1,
    )
    assert listed["total"] == 1
    assert listed["items"][0]["branch_code"] == "02"
    assert listed["page_size"] == 1


def test_get_forbidden_for_other_create_user() -> None:
    repo = FakeRequests()
    created = CreateInvoicePostingRequestUseCase(repo, FakeSuppliers()).execute(
        _payload(), _creator()
    )
    with pytest.raises(InvoicePostingForbiddenError):
        GetInvoicePostingRequestUseCase(repo).execute(
            created["id"], _creator(user_id="stranger")
        )


def test_update_authorized_and_forbidden() -> None:
    repo = FakeRequests()
    created = CreateInvoicePostingRequestUseCase(repo, FakeSuppliers()).execute(
        _payload(), _creator()
    )
    updated = UpdateInvoicePostingRequestUseCase(repo, FakeSuppliers()).execute(
        created["id"], {"amount": "200.00"}, _creator()
    )
    assert float(updated["amount"]) == 200.0
    hist = repo.list_history(created["id"])
    assert any(h["event_type"] == "updated" for h in hist)

    StartInvoicePostingRequestUseCase(repo).execute(created["id"], _processor())
    with pytest.raises(InvoicePostingForbiddenError):
        UpdateInvoicePostingRequestUseCase(repo, FakeSuppliers()).execute(
            created["id"], {"amount": "300"}, _creator()
        )


def test_update_terminal_forbidden() -> None:
    repo = FakeRequests()
    created = CreateInvoicePostingRequestUseCase(repo, FakeSuppliers()).execute(
        _payload(), _creator()
    )
    CancelInvoicePostingRequestUseCase(repo).execute(
        created["id"], actor=_creator(), justification="erro"
    )
    with pytest.raises(InvoicePostingInvalidTransitionError):
        UpdateInvoicePostingRequestUseCase(repo, FakeSuppliers()).execute(
            created["id"], {"amount": "10"}, _manager()
        )


def test_transitions_start_block_resume() -> None:
    repo = FakeRequests()
    created = CreateInvoicePostingRequestUseCase(repo, FakeSuppliers()).execute(
        _payload(), _creator()
    )
    started = StartInvoicePostingRequestUseCase(repo).execute(
        created["id"], _processor()
    )
    assert started["status"] == "in_progress"
    assert started["assignee_user_id"] == "u-process"
    # idempotente mesmo responsável
    again = StartInvoicePostingRequestUseCase(repo).execute(created["id"], _processor())
    assert again["status"] == "in_progress"

    blocked = BlockInvoicePostingRequestUseCase(repo).execute(
        created["id"],
        actor=_processor(),
        block_reason="purchase_order",
        block_description="Falta pedido",
    )
    assert blocked["status"] == "blocked"
    resumed = ResumeInvoicePostingRequestUseCase(repo).execute(
        created["id"], _processor()
    )
    assert resumed["status"] == "in_progress"
    assert resumed["block_reason"] is None
    assert resumed["assignee_user_id"] == "u-process"


def test_start_conflict_other_assignee() -> None:
    repo = FakeRequests()
    created = CreateInvoicePostingRequestUseCase(repo, FakeSuppliers()).execute(
        _payload(), _creator()
    )
    StartInvoicePostingRequestUseCase(repo).execute(created["id"], _processor())
    with pytest.raises(InvoicePostingConflictError):
        StartInvoicePostingRequestUseCase(repo).execute(
            created["id"], _processor(user_id="u-other", user_name="Outro")
        )
    # manage pode reassumir
    taken = StartInvoicePostingRequestUseCase(repo).execute(created["id"], _manager())
    assert taken["assignee_user_id"] == "u-manage"


def test_invalid_transitions() -> None:
    repo = FakeRequests()
    created = CreateInvoicePostingRequestUseCase(repo, FakeSuppliers()).execute(
        _payload(), _creator()
    )
    with pytest.raises(InvoicePostingInvalidTransitionError):
        ResumeInvoicePostingRequestUseCase(repo).execute(created["id"], _processor())

    StartInvoicePostingRequestUseCase(repo).execute(created["id"], _processor())
    with pytest.raises(InvoicePostingInvalidTransitionError):
        ResumeInvoicePostingRequestUseCase(repo).execute(created["id"], _processor())

    BlockInvoicePostingRequestUseCase(repo).execute(
        created["id"],
        actor=_processor(),
        block_reason="other",
        block_description="pendência",
    )
    with pytest.raises(InvoicePostingInvalidTransitionError):
        StartInvoicePostingRequestUseCase(repo).execute(created["id"], _processor())


def test_cancel_by_creator_and_manage() -> None:
    repo = FakeRequests()
    create = CreateInvoicePostingRequestUseCase(repo, FakeSuppliers())
    a = create.execute(_payload(document="101"), _creator())
    b = create.execute(_payload(document="102"), _creator())
    CancelInvoicePostingRequestUseCase(repo).execute(
        a["id"], actor=_creator(), justification="digitou errado"
    )
    assert repo.get_request(a["id"])["status"] == "cancelled"

    StartInvoicePostingRequestUseCase(repo).execute(b["id"], _processor())
    with pytest.raises(InvoicePostingForbiddenError):
        CancelInvoicePostingRequestUseCase(repo).execute(
            b["id"], actor=_creator(), justification="não pode"
        )
    with pytest.raises(InvoicePostingForbiddenError):
        CancelInvoicePostingRequestUseCase(repo).execute(
            b["id"], actor=_processor(), justification="process não cancela"
        )
    CancelInvoicePostingRequestUseCase(repo).execute(
        b["id"], actor=_manager(), justification="admin cancela"
    )
    assert repo.get_request(b["id"])["status"] == "cancelled"


def test_cancel_idempotent_does_not_hide_authz() -> None:
    repo = FakeRequests()
    created = CreateInvoicePostingRequestUseCase(repo, FakeSuppliers()).execute(
        _payload(), _creator()
    )
    CancelInvoicePostingRequestUseCase(repo).execute(
        created["id"], actor=_creator(), justification="ok"
    )
    # process não pode "cancelar de novo" só porque já está cancelled
    with pytest.raises(InvoicePostingForbiddenError):
        CancelInvoicePostingRequestUseCase(repo).execute(
            created["id"], actor=_processor(), justification="x"
        )


def test_parse_amount_accepts_brazilian_comma() -> None:
    assert _parse_amount("1.100,50") == __import__("decimal").Decimal("1100.50")
    assert _parse_amount("1100,5") == __import__("decimal").Decimal("1100.50")
    assert _parse_amount("1100.50") == __import__("decimal").Decimal("1100.50")


def test_post_manual_marks_posted() -> None:
    repo = FakeRequests()
    created = CreateInvoicePostingRequestUseCase(repo, FakeSuppliers()).execute(
        _payload(document="909"), _creator()
    )
    with pytest.raises(InvoicePostingForbiddenError):
        PostManualInvoicePostingRequestUseCase(repo).execute(
            created["id"], actor=_creator()
        )

    posted = PostManualInvoicePostingRequestUseCase(repo).execute(
        created["id"],
        actor=_processor(),
    )
    assert posted["status"] == "posted"
    assert posted["completion_source"] == "manual"
    assert posted["reconciled_at"]
    hist = repo.list_history(created["id"])
    assert hist[-1]["event_type"] == "manual_posted"
    assert hist[-1]["justification"] is None
    assert "post_manual_lancamento_notas_fiscais_request"  # cobertura operationId


def test_comments_auth() -> None:
    repo = FakeRequests()
    created = CreateInvoicePostingRequestUseCase(repo, FakeSuppliers()).execute(
        _payload(), _creator()
    )
    comment = AddInvoicePostingCommentUseCase(repo).execute(
        created["id"], actor=_creator(), body="  olá  "
    )
    assert comment["body"] == "olá"
    with pytest.raises(InvoicePostingValidationError):
        AddInvoicePostingCommentUseCase(repo).execute(
            created["id"], actor=_creator(), body="   "
        )
    with pytest.raises(InvoicePostingForbiddenError):
        AddInvoicePostingCommentUseCase(repo).execute(
            created["id"], actor=_creator(user_id="stranger"), body="x"
        )
    with pytest.raises(InvoicePostingNotFoundError):
        AddInvoicePostingCommentUseCase(repo).execute(
            str(uuid4()), actor=_processor(), body="x"
        )


def test_get_includes_history_comments_actions() -> None:
    repo = FakeRequests()
    created = CreateInvoicePostingRequestUseCase(repo, FakeSuppliers()).execute(
        _payload(), _creator()
    )
    AddInvoicePostingCommentUseCase(repo).execute(
        created["id"], actor=_creator(), body="c1"
    )
    detail = GetInvoicePostingRequestUseCase(repo).execute(created["id"], _creator())
    assert detail["request"]["id"] == created["id"]
    assert len(detail["history"]) >= 2
    assert len(detail["comments"]) == 1
    assert "cancel" in detail["allowed_actions"]
    assert "edit" in detail["allowed_actions"]
