"""Use-case behavior for the R05 stock-movements summary.

Covers: fail-closed scope gate, snapshot presence, the derived opening
balance (BR-R05-006: SA − net movement), the process-transfers memo
column staying outside the balance equation, no-false-zero semantics,
sibling-branch isolation and the mp_pi_pa scope filter.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import pytest

from app.application.dto.financeiro_stock_movements.stock_movements_request import (
    StockMovementsQueryRequest,
)
from app.application.security.stock_inventory_scope import (
    StockInventoryScope,
    StockInventoryScopeUnavailableError,
    UnresolvedStockInventoryScopeResolver,
)
from app.application.use_cases.financeiro_stock_movements.get_stock_movements_use_case import (
    GetStockMovementsUseCase,
)


@dataclass
class _ResolvedResolver:
    def resolve(self, *, user_subject):
        return StockInventoryScope(resolved=True, reason="test")


class _FakeRepository:
    def __init__(self, presence=None, sa=None, sd1=None, sd2=None,
                 sd3=None):
        self.presence = presence or {}
        self._sa = sa or []
        self._sd1 = sd1 or []
        self._sd2 = sd2 or []
        self._sd3 = sd3 or []
        self.calls = {"sd1": 0, "sd2": 0, "sd3": 0, "sa": 0}
        self.kwargs = {}

    def snapshot_branch_counts(self, **kwargs):
        return self.presence

    def closing_balance_by_type(self, **kwargs):
        self.calls["sa"] += 1
        self.kwargs["sa"] = kwargs
        return self._sa

    def sd1_by_type(self, **kwargs):
        self.calls["sd1"] += 1
        self.kwargs["sd1"] = kwargs
        return self._sd1

    def sd2_by_type(self, **kwargs):
        self.calls["sd2"] += 1
        self.kwargs["sd2"] = kwargs
        return self._sd2

    def sd3_by_type(self, **kwargs):
        self.calls["sd3"] += 1
        self.kwargs["sd3"] = kwargs
        return self._sd3


def _request(**overrides):
    params = {"period": "2026-09"}
    params.update(overrides)
    return StockMovementsQueryRequest.from_query(**params)


def _use_case(repo, resolver=None):
    return GetStockMovementsUseCase(
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
    assert response["branchesMissing"] == ["01"]
    assert response["dataAsOf"] is None
    assert response["totals"]["openingBalance"] is None
    assert response["totals"]["closingBalance"] is None
    assert response["totals"]["netMovement"] is None
    # Movement reads still run — they prove absence honestly, but the
    # SA read is skipped without any snapshot.
    assert repo.calls["sa"] == 0


def test_incomplete_when_sibling_branch_missing():
    repo = _FakeRepository(
        presence={"01": 10},
        sa=[{"product_type": "MP", "total_stock_value": "100.00"}],
    )
    response = _use_case(repo).execute(
        _request(branch="all"), user_subject="user-1"
    ).to_dict()
    assert response["status"] == "incomplete"
    assert response["branchesAvailable"] == ["01"]
    assert response["branchesMissing"] == ["02"]


def test_opening_balance_is_derived_from_sa_minus_net_movement():
    """BR-R05-006: SI = SA − (Compras+MovInt+Requis+Transf+Prod−Vendas+
    DevV−DevC+EntPT−SaiPT). Process transfers stay OUT of the equation."""
    repo = _FakeRepository(
        presence={"01": 5},
        sa=[{"product_type": "MP", "total_stock_value": "1000.00"}],
        sd1=[{
            "product_type": "MP",
            "purchases": "300.00",
            "sales_returns": "20.00",
            "third_party_in": "10.00",
        }],
        sd2=[{
            "product_type": "MP",
            "sales": "150.00",
            "purchase_returns": "30.00",
            "third_party_out": "5.00",
        }],
        sd3=[{
            "product_type": "MP",
            "internal_movements": "40.00",
            "production_requisitions": "60.00",
            "transfers": "15.00",
            "production": "25.00",
            "process_transfers": "999.00",
        }],
    )
    response = _use_case(repo).execute(
        _request(branch="01"), user_subject="user-1"
    ).to_dict()
    assert response["status"] == "available"
    row = next(r for r in response["rows"] if r["productType"] == "MP")
    # net = 300+40+60+15+25−150+20−30+10−5 = 285
    assert row["netMovement"] == "285.000000"
    # opening = 1000 − 285 = 715 — memo column never enters.
    assert row["openingBalance"] == "715.000000"
    assert row["closingBalance"] == "1000.000000"
    assert row["processTransfersMemo"] == "999.000000"
    totals = response["totals"]
    assert totals["netMovement"] == "285.000000"
    assert totals["openingBalance"] == "715.000000"


def test_sb9_type_absent_is_real_zero_not_unknown():
    """Snapshot present but the type has no SB9 balance → closing 0.00,
    not unknown (BR-R05-002 real zero vs unknown measure)."""
    repo = _FakeRepository(
        presence={"01": 5},
        sa=[],
        sd1=[{"product_type": "MP", "purchases": "50.00"}],
    )
    response = _use_case(repo).execute(
        _request(branch="01"), user_subject="user-1"
    ).to_dict()
    row = response["rows"][0]
    assert row["closingBalance"] == "0.000000"
    assert row["openingBalance"] == "-50.000000"


def test_movement_window_uses_full_competence_month():
    repo = _FakeRepository(presence={"01": 1})
    _use_case(repo).execute(_request(branch="01"), user_subject="user-1")
    assert repo.kwargs["sd1"]["period_start"] == "20260901"
    assert repo.kwargs["sd1"]["period_end"] == "20260930"
    assert repo.kwargs["sa"]["snapshot_date"] == "20260930"


def test_mp_pi_pa_scope_propagates_product_types():
    repo = _FakeRepository(presence={"01": 1})
    _use_case(repo).execute(
        _request(branch="01", report_scope="mp_pi_pa"),
        user_subject="user-1",
    )
    for key in ("sd1", "sd2", "sd3", "sa"):
        assert repo.kwargs[key]["product_types"] == ("MP", "PI", "PA")


def test_all_products_scope_passes_no_type_filter():
    repo = _FakeRepository(presence={"01": 1})
    _use_case(repo).execute(
        _request(branch="01"), user_subject="user-1"
    )
    assert repo.kwargs["sd1"]["product_types"] is None


def test_single_branch_query_never_reads_sibling():
    repo = _FakeRepository(presence={"02": 3})
    response = _use_case(repo).execute(
        _request(branch="02"), user_subject="user-1"
    ).to_dict()
    assert response["branchesAvailable"] == ["02"]
    assert repo.kwargs["sd1"]["branches"] == ("02",)


def test_empty_population_is_no_matching_items():
    repo = _FakeRepository(presence={"01": 4})
    response = _use_case(repo).execute(
        _request(branch="01"), user_subject="user-1"
    ).to_dict()
    assert response["status"] == "no_matching_items"
    assert response["rows"] == []


def test_parity_stays_pending_and_never_official():
    repo = _FakeRepository(presence={"01": 1})
    response = _use_case(repo).execute(
        _request(branch="01"), user_subject="user-1"
    ).to_dict()
    assert response["officialMatr320"] is False
    assert response["parityStatus"] == "PENDING"
    assert response["source"] == "protheus_sd1_sd2_sd3_sf4_sb9_sb1"
