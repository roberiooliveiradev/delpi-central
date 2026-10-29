"""Use-case behavior for the standalone R08 work-in-process report.

Covers: fail-closed scope gate, snapshot presence, the MATR989
composition (physical loc-99 + allocated OP balance), no-false-zero,
sibling-branch isolation and honest detail pagination.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import pytest

from app.application.dto.financeiro_stock_inventory.stock_inventory_request import (
    StockInventoryQueryRequest,
)
from app.application.security.stock_inventory_scope import (
    StockInventoryScope,
    StockInventoryScopeUnavailableError,
    UnresolvedStockInventoryScopeResolver,
)
from app.application.use_cases.financeiro_work_in_process.get_work_in_process_use_case import (
    GetWorkInProcessUseCase,
)


@dataclass
class _ResolvedResolver:
    def resolve(self, *, user_subject):
        return StockInventoryScope(resolved=True, reason="test")


class _FakeRepository:
    def __init__(self, presence=None, physical=None, wip=None,
                 detail=None, detail_count=0):
        self.presence = presence or {}
        self._physical = physical or []
        self._wip = wip or []
        self._detail = detail or []
        self._detail_count = detail_count
        self.kwargs = {}

    def snapshot_branch_counts(self, **kwargs):
        return self.presence

    def summary_by_type(self, **kwargs):
        self.kwargs["physical"] = kwargs
        return self._physical

    def work_in_process_by_type(self, **kwargs):
        self.kwargs["wip"] = kwargs
        return self._wip

    def work_in_process_detail(self, **kwargs):
        self.kwargs["detail"] = kwargs
        return self._detail

    def work_in_process_detail_count(self, **kwargs):
        return self._detail_count


def _request(**overrides):
    params = {"period": "2026-09"}
    params.update(overrides)
    return StockInventoryQueryRequest.from_query(**params)


def _use_case(repo, resolver=None):
    return GetWorkInProcessUseCase(
        repository=repo, scope_resolver=resolver or _ResolvedResolver()
    )


def test_scope_unresolved_is_fail_closed():
    use_case = _use_case(
        _FakeRepository(), resolver=UnresolvedStockInventoryScopeResolver()
    )
    with pytest.raises(StockInventoryScopeUnavailableError):
        use_case.execute(_request(), user_subject="user-1")


def test_source_missing_never_fabricates_zero():
    repo = _FakeRepository(presence={})
    response = _use_case(repo).execute(
        _request(branch="01"), user_subject="user-1"
    ).to_dict()
    assert response["status"] == "source_missing"
    assert response["physicalTotal"] is None
    assert response["allocatedTotal"] is None
    assert response["grandTotal"] is None
    assert response["dataAsOf"] is None
    assert response["items"] == []
    # No repository reads beyond the presence probe.
    assert "wip" not in repo.kwargs
    assert "detail" not in repo.kwargs


def test_physical_read_is_scoped_to_process_warehouse():
    repo = _FakeRepository(
        presence={"01": 5},
        physical=[{"product_type": "MP", "total_stock_value": "700.00"}],
        wip=[{
            "product_type": "MP",
            "allocated_value": "300.00",
            "open_order_count": 2,
        }],
        detail_count=2,
    )
    _use_case(repo).execute(_request(branch="01"), user_subject="user-1")
    assert repo.kwargs["physical"]["warehouse"] == "99"
    assert repo.kwargs["wip"]["movement_cutoff"] == "20260930"
    assert repo.kwargs["wip"]["op_alive_cutoff"] == "20261001"


def test_grand_total_is_physical_plus_allocated():
    repo = _FakeRepository(
        presence={"01": 5},
        physical=[
            {"product_type": "MP", "total_stock_value": "700.00"},
            {"product_type": "PA", "total_stock_value": "2287.869"},
        ],
        wip=[
            {
                "product_type": "MP",
                "allocated_value": "169128.463",
                "open_order_count": 3,
            },
        ],
        detail_count=3,
    )
    response = _use_case(repo).execute(
        _request(branch="01"), user_subject="user-1"
    ).to_dict()
    assert response["status"] == "available"
    assert response["physicalTotal"] == "2987.869000"
    assert response["allocatedTotal"] == "169128.463000"
    assert response["grandTotal"] == "172116.332000"
    mp = next(
        s for s in response["summariesByType"] if s["productType"] == "MP"
    )
    assert mp["physicalValue"] == "700.000000"
    assert mp["allocatedValue"] == "169128.463000"
    assert mp["totalValue"] == "169828.463000"
    assert mp["openOrderCount"] == 3


def test_incomplete_when_sibling_branch_missing():
    repo = _FakeRepository(presence={"01": 3})
    response = _use_case(repo).execute(
        _request(branch="all"), user_subject="user-1"
    ).to_dict()
    assert response["status"] == "incomplete"
    assert response["branchesAvailable"] == ["01"]
    assert response["branchesMissing"] == ["02"]


def test_detail_items_normalize_op_and_amounts():
    repo = _FakeRepository(
        presence={"01": 5},
        physical=[{"product_type": "MP", "total_stock_value": "0"}],
        detail=[
            {
                "branch_code": "01",
                "product_code": " MP001 ",
                "description": "Matéria-prima",
                "product_type": "MP",
                "production_order": "00012300101",
                "allocated_quantity": Decimal("12.5"),
                "allocated_value": Decimal("987.654321"),
            }
        ],
        detail_count=1,
    )
    response = _use_case(repo).execute(
        _request(branch="01", page_size=10), user_subject="user-1"
    ).to_dict()
    item = response["items"][0]
    assert item["productCode"] == "MP001"
    assert item["productionOrder"] == "00012300101"
    assert item["allocatedQuantity"] == "12.500000"
    assert item["allocatedValue"] == "987.654321"
    assert response["pagination"]["total_items"] == 1


def test_parity_stays_pending_and_never_official():
    repo = _FakeRepository(presence={"01": 1})
    response = _use_case(repo).execute(
        _request(branch="01"), user_subject="user-1"
    ).to_dict()
    assert response["officialMatr989"] is False
    assert response["parityStatus"] == "PENDING"
    assert response["source"] == "protheus_sb9_sd3_sc2_sb1"


def test_mp_pi_pa_scope_propagates_product_types():
    repo = _FakeRepository(presence={"01": 1})
    _use_case(repo).execute(
        _request(branch="01", report_scope="mp_pi_pa"),
        user_subject="user-1",
    )
    assert repo.kwargs["physical"]["product_types"] == ("MP", "PI", "PA")
    assert repo.kwargs["wip"]["product_types"] == ("MP", "PI", "PA")
