"""Use-case behavior: scope gate, normalization, quality flags, summary."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import pytest

from app.application.dto.financeiro_settlements.settlements_request import (
    SettlementsQueryRequest,
)
from app.application.security.settlement_scope import (
    SettlementScope,
    SettlementScopeUnavailableError,
    UnresolvedSettlementScopeResolver,
)
from app.application.use_cases.financeiro_settlements.get_settlements_use_case import (
    GetSettlementsUseCase,
)
from app.application.use_cases.financeiro_settlements.get_summary_use_case import (
    GetSettlementsSummaryUseCase,
)


@dataclass
class _ResolvedResolver:
    def resolve(self, *, user_subject):
        return SettlementScope(resolved=True, reason="test")


class _FakeRepository:
    def __init__(self, rows=None, counters=None, groups=None):
        self.rows = rows or []
        self.counters = counters or {}
        self.groups = groups or []
        self.list_calls = []

    def list_settlements(self, **kwargs):
        self.list_calls.append(kwargs)
        return self.rows

    def count_settlements(self, **kwargs):
        return len(self.rows)

    def quality_counters(self, **kwargs):
        return self.counters

    def summary_groups(self, **kwargs):
        return self.groups

    def nature_descriptions(self, *, nature_codes):
        return {code: f"Nature {code}" for code in nature_codes}

    def movement_descriptions(self, *, movement_types):
        return {code: f"Movement {code}" for code in movement_types}


def _request(**overrides):
    return SettlementsQueryRequest.from_query(
        start_date="2026-01-01",
        end_date="2026-01-31",
        **overrides,
    )


def _resolved_row(**overrides):
    row = {
        "settlement_id": "ABC123",
        "settlement_date": "20260110",
        "settlement_amount": Decimal("1234.50"),
        "currency_code": "BRL",
        "nature_code": "100",
        "nature_description": "FORNECEDORES",
        "document_number": "12345",
        "prefix": "001",
        "installment": "01",
        "document_type": "NF",
        "party_code": "000777",
        "party_store": "01",
        "party_name": "ACME LTDA",
        "issue_date": "20260102",
        "due_date": "20260201",
        "history": "PAGAMENTO NF 12345",
        "movement_type": "BA",
        "payment_direction": "P",
        "source_branch": "",
        "missing_document": 0,
        "missing_nature": 0,
    }
    row.update(overrides)
    return row


def test_unresolved_scope_blocks_real_rows() -> None:
    use_case = GetSettlementsUseCase(
        repository=_FakeRepository(rows=[_resolved_row()]),
        scope_resolver=UnresolvedSettlementScopeResolver(),
    )
    with pytest.raises(SettlementScopeUnavailableError):
        use_case.execute(
            _request(), side="payable", user_subject="user-1"
        )


def test_list_normalizes_item_and_flags_branch_unresolved() -> None:
    repo = _FakeRepository(
        rows=[_resolved_row()],
        counters={
            "total_events": 1,
            "missing_document": 0,
            "missing_nature": 0,
            "unresolved_branch": 1,
        },
    )
    use_case = GetSettlementsUseCase(
        repository=repo, scope_resolver=_ResolvedResolver()
    )
    response = use_case.execute(
        _request(), side="payable", user_subject="user-1"
    )
    body = response.to_dict()
    assert body["status"] == "partial"
    assert body["officialTotals"] is False
    item = body["items"][0]
    assert item["settlementId"] == "ABC123"
    assert item["settlementDate"] == "2026-01-10"
    assert item["settlementAmount"] == "1234.50"  # decimal string
    assert item["branchCode"] is None  # empty *_FILIAL → null, never "01"
    assert item["branchResolution"] == "unresolved"
    assert item["linkStatus"] == "resolved"
    assert item["movementType"] == "BA"
    assert item["movementDescription"] == "Movement BA"
    assert repo.list_calls[0]["side"] == "payable"
    assert repo.list_calls[0]["start_date"] == "20260101"


def test_link_status_missing_document_and_nature() -> None:
    repo = _FakeRepository(
        rows=[_resolved_row(missing_document=1)],
        counters={
            "total_events": 1,
            "missing_document": 1,
            "missing_nature": 0,
            "unresolved_branch": 0,
        },
    )
    use_case = GetSettlementsUseCase(
        repository=repo, scope_resolver=_ResolvedResolver()
    )
    body = use_case.execute(
        _request(), side="receivable", user_subject="user-1"
    ).to_dict()
    assert body["items"][0]["linkStatus"] == "missing_document"
    assert body["status"] == "partial"
    assert body["side"] == "receivable"


def test_invalid_side_rejected() -> None:
    use_case = GetSettlementsUseCase(
        repository=_FakeRepository(), scope_resolver=_ResolvedResolver()
    )
    with pytest.raises(ValueError):
        use_case.execute(_request(), side="north", user_subject="u")


def test_summary_groups_preserve_currencies_and_no_official_total() -> None:
    repo = _FakeRepository(
        groups=[
            {
                "side": "payable",
                "currency_code": "BRL",
                "nature_code": "100",
                "movement_type": "BA",
                "event_count": 3,
                "total_amount": Decimal("999.995"),
            },
            {
                "side": "payable",
                "currency_code": "USD",
                "nature_code": "100",
                "movement_type": "BA",
                "event_count": 1,
                "total_amount": Decimal("10"),
            },
        ]
    )
    use_case = GetSettlementsSummaryUseCase(
        repository=repo, scope_resolver=_ResolvedResolver()
    )
    body = use_case.execute(_request(), user_subject="user-1").to_dict()
    assert body["officialTotals"] is False
    assert len(body["groups"]) == 2
    brl = next(g for g in body["groups"] if g["currencyCode"] == "BRL")
    usd = next(g for g in body["groups"] if g["currencyCode"] == "USD")
    assert brl["totalAmount"] == "1000.00"  # quantized decimal string
    assert usd["totalAmount"] == "10.00"  # never merged with BRL
    assert brl["natureDescription"] == "Nature 100"
    assert brl["movementDescription"] == "Movement BA"


def test_summary_also_fail_closed_without_scope() -> None:
    use_case = GetSettlementsSummaryUseCase(
        repository=_FakeRepository(groups=[{"side": "payable"}]),
        scope_resolver=UnresolvedSettlementScopeResolver(),
    )
    with pytest.raises(SettlementScopeUnavailableError):
        use_case.execute(_request(), user_subject="u")
