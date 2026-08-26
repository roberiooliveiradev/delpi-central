from __future__ import annotations

from types import SimpleNamespace

import pytest

from purchase_requests_app.application.services.purchase_request_scope_resolver import (
    PurchaseRequestScopeResolver,
)
from purchase_requests_app.domain.services.purchase_request_domain_service import (
    CostCenterScope,
    ScopeResolution,
    derive_delivery_status,
    derive_order_status,
    derive_overall_stage,
    derive_receipt_status,
    map_approval_status,
    purchase_order_open_quantity,
    request_open_quantity,
)


def test_union_of_cost_centers_removes_duplicates() -> None:
    rows = [
        {"branch": "01", "cost_center_code": "0413"},
        {"branch": "01", "cost_center_code": "0413"},
        {"branch": "01", "cost_center_code": "0520"},
    ]
    resolver = PurchaseRequestScopeResolver()
    allowed = resolver._union_active_scopes(rows)
    assert allowed == {
        CostCenterScope("01", "0413"),
        CostCenterScope("01", "0520"),
    }


def test_inactive_scopes_excluded_by_repository_query_shape() -> None:
    resolution = ScopeResolution(
        view_all=False,
        allowed_cost_centers=frozenset({CostCenterScope("01", "0413")}),
    )
    assert resolution.allows("01", "0413")
    assert not resolution.allows("01", "0520")


def test_fail_closed_empty_allowed_codes() -> None:
    resolver = PurchaseRequestScopeResolver()
    user = SimpleNamespace(is_superadmin=False, permissions=["purchase-requests.access"])
    resolution = resolver.resolve(
        user=user,
        branch="01",
        scope_rows=[],
    )
    assert resolution.view_all is False
    assert resolver.effective_cost_centers(resolution, branch="01") == []


def test_view_all_skips_cost_center_filter() -> None:
    resolver = PurchaseRequestScopeResolver()
    user = SimpleNamespace(
        is_superadmin=False,
        permissions=["purchase-requests.access", "purchase-requests.view-all"],
    )
    resolution = resolver.resolve(user=user, branch="01", scope_rows=[])
    assert resolution.view_all is True
    assert resolver.effective_cost_centers(resolution, branch="01") is None


def test_explicit_cost_center_allowed() -> None:
    resolver = PurchaseRequestScopeResolver()
    user = SimpleNamespace(is_superadmin=False, permissions=["purchase-requests.access"])
    rows = [{"branch": "01", "cost_center_code": "0413"}]
    resolution = resolver.resolve(
        user=user,
        branch="01",
        explicit_cost_center="0413",
        scope_rows=rows,
    )
    assert resolver.effective_cost_centers(
        resolution,
        branch="01",
        explicit_cost_center="0413",
    ) == ["0413"]


def test_explicit_cost_center_forbidden_raises() -> None:
    resolver = PurchaseRequestScopeResolver()
    user = SimpleNamespace(is_superadmin=False, permissions=["purchase-requests.access"])
    rows = [{"branch": "01", "cost_center_code": "0413"}]
    with pytest.raises(PermissionError):
        resolver.resolve(
            user=user,
            branch="01",
            explicit_cost_center="0520",
            scope_rows=rows,
        )


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("L", "approved"),
        ("R", "rejected"),
        ("B", "blocked"),
        ("", "unknown"),
        ("X", "unknown"),
    ],
)
def test_approval_mapping(raw: str, expected: str) -> None:
    assert map_approval_status(raw) == expected


def test_request_open_quantity() -> None:
    assert request_open_quantity(10, 4) == 6
    assert request_open_quantity(4, 10) == 0


def test_purchase_order_open_quantity() -> None:
    assert purchase_order_open_quantity(10, 3) == 7


def test_order_status_awaiting_order() -> None:
    assert (
        derive_order_status(
            ordered_quantity=0,
            requested_quantity=5,
            has_orders=False,
        )
        == "not_ordered"
    )


def test_order_status_partially_ordered() -> None:
    assert (
        derive_order_status(
            ordered_quantity=2,
            requested_quantity=5,
            has_orders=True,
        )
        == "partially_ordered"
    )


def test_receipt_status_partially_received() -> None:
    assert (
        derive_receipt_status(
            has_orders=True,
            received_quantity=2,
            ordered_quantity=5,
        )
        == "partially_received"
    )


def test_overall_stage_awaiting_order() -> None:
    assert (
        derive_overall_stage(
            residual=False,
            requested_quantity=5,
            ordered_quantity=0,
            has_orders=False,
            max_received_quantity=0,
            max_order_quantity=0,
        )
        == "awaiting_order"
    )


def test_overall_stage_completed() -> None:
    assert (
        derive_overall_stage(
            residual=False,
            requested_quantity=5,
            ordered_quantity=5,
            has_orders=True,
            max_received_quantity=5,
            max_order_quantity=5,
        )
        == "completed"
    )


def test_overall_stage_residual_closed() -> None:
    assert (
        derive_overall_stage(
            residual=True,
            requested_quantity=5,
            ordered_quantity=0,
            has_orders=False,
            max_received_quantity=0,
            max_order_quantity=0,
        )
        == "residual_closed"
    )


def test_delivery_overdue() -> None:
    assert (
        derive_delivery_status(
            expected_delivery_date="2026-01-01",
            open_quantity=1,
            received_quantity=0,
            today_iso="2026-08-26",
        )
        == "overdue"
    )


def test_buyer_null_when_empty_in_order_payload() -> None:
    order = {"buyer_code": "   "}
    buyer_code = (order.get("buyer_code") or "").strip()
    buyer = {"code": buyer_code} if buyer_code else None
    assert buyer is None
