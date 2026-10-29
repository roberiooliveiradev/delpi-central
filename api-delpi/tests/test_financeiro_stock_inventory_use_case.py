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
        p7=None,
        wip=None,
    ):
        self.presence = presence or {}
        self.rows = rows or []
        self._totals = totals or {}
        self.by_type = by_type or []
        self.by_warehouse = by_warehouse or []
        self._p7 = p7 or {}
        self._wip = wip or []
        self.calls = {"items": 0}
        self.p7_kwargs = None
        self.wip_kwargs = None

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

    def p7_totals(self, **kwargs):
        self.p7_kwargs = kwargs
        return self._p7

    def work_in_process_by_type(self, **kwargs):
        self.wip_kwargs = kwargs
        return self._wip


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
    assert response["parityStatus"] == "PENDING"
    assert response["source"] == "protheus_sb9_sb1_sd3_sc2"
    assert response["referenceDate"] == "2026-09-30"


def test_source_missing_keeps_parity_not_run_and_null_p7_totals():
    repo = _FakeRepository(presence={})
    use_case = GetStockInventoryUseCase(
        repository=repo, scope_resolver=_ResolvedResolver()
    )
    response = use_case.execute(
        _request(branch="01"), user_subject="user-1"
    ).to_dict()
    assert response["status"] == "source_missing"
    assert response["parityStatus"] == "TEST_NOT_RUN"
    assert response["stockTotal"] is None
    assert response["processTotal"] is None
    assert response["grandTotal"] is None


def test_p7_totals_compose_grand_total_and_provenance():
    repo = _FakeRepository(
        presence={"01": 4812},
        totals={"item_count": 1, "total_value": Decimal("100.50")},
        p7={
            "item_count": 1,
            "stock_value": Decimal("3591191.36"),
            "process_physical_value": Decimal("293273.09"),
            "stock_quantity": Decimal("10.0"),
        },
        wip=[
            {
                "product_type": "MP",
                "allocated_value": Decimal("61967.42"),
                "open_order_count": 444,
            }
        ],
    )
    use_case = GetStockInventoryUseCase(
        repository=repo, scope_resolver=_ResolvedResolver()
    )
    response = use_case.execute(
        _request(branch="01"), user_subject="user-1"
    ).to_dict()
    assert response["stockTotal"] == "3591191.360000"
    assert response["processPhysicalTotal"] == "293273.090000"
    assert response["processAllocatedTotal"] == "61967.420000"
    assert response["processTotal"] == "355240.510000"
    assert response["grandTotal"] == "3946431.870000"
    assert response["parityStatus"] == "PENDING"
    provenance = response["provenance"]
    assert provenance["officialProducer"] == "matr460"
    assert provenance["snapshotDate"] == "2026-09-30"
    assert provenance["movementCutoff"] == "2026-09-30"
    assert provenance["opAliveCutoff"] == "2026-10-01"
    assert provenance["processWarehouse"] == "99"
    assert provenance["openOrdersAllocated"] == 444
    # Report-level totalizers ignore the warehouse item filter.
    assert repo.p7_kwargs["product_types"] is None
    assert repo.wip_kwargs["movement_cutoff"] == "20260930"
    assert repo.wip_kwargs["op_alive_cutoff"] == "20261001"


def test_p7_totals_monetary_policy_full_precision():
    """Monetary policy (doc 119 §11): totalizers are Decimal strings at
    6dp computed by the engine — the grand total is ALWAYS the exact
    sum of the parcels at full precision. Rounding to 2dp for display
    happens only in presentation; a displayed-parcels sum differing
    from the displayed total by a cent is legitimate rounding, never a
    calculation adjustment."""
    repo = _FakeRepository(
        presence={"01": 1, "02": 1},
        totals={"item_count": 1, "total_value": Decimal("1")},
        p7={
            "item_count": 1,
            "stock_value": Decimal("13767296.144"),
            "process_physical_value": Decimal("702287.869"),
            "stock_quantity": Decimal("10"),
        },
        wip=[{"allocated_value": Decimal("169128.463"),
              "open_order_count": 414}],
    )
    use_case = GetStockInventoryUseCase(
        repository=repo, scope_resolver=_ResolvedResolver()
    )
    response = use_case.execute(
        _request(), user_subject="user-1"
    ).to_dict()
    stock = Decimal(response["stockTotal"])
    process = Decimal(response["processTotal"])
    grand = Decimal(response["grandTotal"])
    assert stock == Decimal("13767296.144000")
    assert process == Decimal("871416.332000")
    assert grand == stock + process == Decimal("14638712.476000")


def test_mp_pi_pa_scope_carries_type_filter_and_parity_note():
    repo = _FakeRepository(
        presence={"01": 10},
        totals={"item_count": 0, "total_value": Decimal("0")},
        p7={
            "item_count": 0,
            "stock_value": Decimal("0"),
            "process_physical_value": Decimal("0"),
        },
    )
    use_case = GetStockInventoryUseCase(
        repository=repo, scope_resolver=_ResolvedResolver()
    )
    response = use_case.execute(
        _request(branch="01", report_scope="mp_pi_pa"), user_subject="user-1"
    ).to_dict()
    assert repo.p7_kwargs["product_types"] == ("MP", "PI", "PA")
    assert repo.wip_kwargs["product_types"] == ("MP", "PI", "PA")
    assert len(response["parityNotes"]) == 2
    assert "poder de terceiros" in response["parityNotes"][1]
