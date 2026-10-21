"""Use-case behavior: scope gate, snapshot presence, status semantics."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import pytest

from app.application.dto.financeiro_stock_inventory.stock_inventory_request import (
    StockInventoryQueryRequest,
)
from app.application.security.stock_inventory_scope import (
    SharedDatasetStockInventoryScopeResolver,
    StockInventoryScope,
    StockInventoryScopeUnavailableError,
    UnresolvedStockInventoryScopeResolver,
)
from app.application.use_cases.financeiro_stock_inventory.get_stock_inventory_use_case import (
    GetStockInventoryUseCase,
)


@dataclass
class _ResolvedResolver:
    def resolve(self, *, user_subject):
        return StockInventoryScope(resolved=True, reason="test")


class _FakeRepository:
    def __init__(
        self,
        presence=None,
        rows=None,
        totals=None,
        by_type=None,
        by_warehouse=None,
    ):
        self.presence = presence or {}
        self.rows = rows or []
        self._totals = totals or {}
        self.by_type = by_type or []
        self.by_warehouse = by_warehouse or []
        self.calls = {"items": 0}

    def snapshot_branch_counts(self, **kwargs):
        return self.presence

    def totals(self, **kwargs):
        return self._totals

    def list_items(self, **kwargs):
        self.calls["items"] += 1
        return self.rows

    def summary_by_type(self, **kwargs):
        return self.by_type

    def summary_by_warehouse(self, **kwargs):
        return self.by_warehouse


def _request(**overrides):
    params = {"period": "2026-09"}
    params.update(overrides)
    return StockInventoryQueryRequest.from_query(**params)


def test_scope_unresolved_is_fail_closed():
    use_case = GetStockInventoryUseCase(
        repository=_FakeRepository(),
        scope_resolver=UnresolvedStockInventoryScopeResolver(),
    )
    with pytest.raises(StockInventoryScopeUnavailableError):
        use_case.execute(_request(), user_subject="user-1")


def test_flag_disabled_resolver_stays_closed():
    resolver = SharedDatasetStockInventoryScopeResolver(enabled=False)
    assert resolver.resolve(user_subject="user-1").resolved is False


def test_flag_on_requires_delegated_user():
    resolver = SharedDatasetStockInventoryScopeResolver(enabled=True)
    assert resolver.resolve(user_subject=None).resolved is False
    assert resolver.resolve(user_subject="").resolved is False
    assert resolver.resolve(user_subject="user-1").resolved is True


def test_source_missing_returns_no_total_and_no_queries():
    repo = _FakeRepository(presence={})
    use_case = GetStockInventoryUseCase(
        repository=repo, scope_resolver=_ResolvedResolver()
    )
    response = use_case.execute(
        _request(branch="01"), user_subject="user-1"
    ).to_dict()
    assert response["status"] == "source_missing"
    assert response["historicalTotal"] is None
    assert response["items"] == []
    assert response["branchesMissing"] == ["01"]
    assert response["dataAsOf"] is None
    assert repo.calls["items"] == 0


def test_incomplete_when_one_branch_missing_on_all():
    repo = _FakeRepository(
        presence={"02": 3117},
        rows=[
            {
                "branch_code": "02",
                "warehouse": "01",
                "product_code": "P1",
                "description": "Produto 1",
                "product_type": "MP",
                "product_group": "1000",
                "unit": "KG",
                "historical_quantity": Decimal("10.0000"),
                "historical_stock_value": Decimal("100.50"),
            }
        ],
        totals={
            "item_count": 1,
            "total_quantity": Decimal("10.0000"),
            "total_value": Decimal("100.50"),
        },
        by_type=[
            {
                "product_type": "MP",
                "item_count": 1,
                "total_quantity": Decimal("10.0000"),
                "total_stock_value": Decimal("100.50"),
            }
        ],
        by_warehouse=[
            {
                "branch_code": "02",
                "warehouse": "01",
                "item_count": 1,
                "total_quantity": Decimal("10.0000"),
                "total_stock_value": Decimal("100.50"),
            }
        ],
    )
    use_case = GetStockInventoryUseCase(
        repository=repo, scope_resolver=_ResolvedResolver()
    )
    response = use_case.execute(
        _request(branch="all"), user_subject="user-1"
    ).to_dict()
    assert response["status"] == "incomplete"
    assert response["branchesAvailable"] == ["02"]
    assert response["branchesMissing"] == ["01"]
    assert response["historicalTotal"] == "100.50"
    assert response["items"][0]["productCode"] == "P1"
    assert response["summariesByType"][0]["productType"] == "MP"


def test_available_snapshot():
    repo = _FakeRepository(
        presence={"01": 4812},
        totals={
            "item_count": 0,
            "total_quantity": Decimal("0"),
            "total_value": Decimal("0"),
        },
    )
    use_case = GetStockInventoryUseCase(
        repository=repo, scope_resolver=_ResolvedResolver()
    )
    # Snapshot exists, filter matched nothing -> legitimate empty result.
    response = use_case.execute(
        _request(branch="01", warehouse="99"), user_subject="user-1"
    ).to_dict()
    assert response["status"] == "no_matching_items"
    assert response["historicalTotal"] == "0"
    assert response["dataAsOf"] == "2026-09-30"


def test_response_contract_flags():
    repo = _FakeRepository(
        presence={"01": 10},
        totals={"item_count": 0, "total_value": Decimal("0")},
    )
    use_case = GetStockInventoryUseCase(
        repository=repo, scope_resolver=_ResolvedResolver()
    )
    response = use_case.execute(
        _request(branch="01"), user_subject="user-1"
    ).to_dict()
    assert response["officialP7"] is False
    assert response["parityStatus"] == "TEST_NOT_RUN"
    assert response["source"] == "protheus_sb9_sb1"
    assert response["referenceDate"] == "2026-09-30"
