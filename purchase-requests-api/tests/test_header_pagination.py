from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from purchase_requests_app.application.services.purchase_request_aggregation_service import (
    PurchaseRequestAggregationService,
)
from purchase_requests_app.application.use_cases.list_purchase_requests_use_case import (
    ListPurchaseRequestsUseCase,
)
from purchase_requests_app.domain.services.purchase_request_domain_service import (
    CostCenterScope,
    ScopeResolution,
)


def _line(
    *,
    request_number: str,
    request_item: str,
    cost_center: str,
    branch: str = "02",
) -> dict:
    return {
        "branch": branch,
        "request_number": request_number,
        "request_item": request_item,
        "cost_center_code": cost_center,
        "request_issue_date": "2026-08-01",
        "requester_protheus_user_id": "1",
        "requested_quantity": 1.0,
        "ordered_quantity": 0.0,
        "approval_status": "unknown",
        "purchase_orders": [],
    }


def test_pagination_one_sc_with_many_items_returns_each_line() -> None:
    lines = [_line(request_number="100", request_item=f"{i:04d}", cost_center="0413") for i in range(1, 51)]
    gateway = MagicMock()
    gateway.list_lines.return_value = {
        "items": lines,
        "page": 1,
        "page_size": 10,
        "total": 1,
        "total_pages": 1,
    }
    scope_repo = MagicMock()
    scope_repo.list_active_cost_centers_for_user.return_value = [
        {"branch": "02", "cost_center_code": "0413"}
    ]
    use_case = ListPurchaseRequestsUseCase(gateway=gateway, scope_repository=scope_repo)
    result = use_case.execute(
        user=SimpleNamespace(
            id="u1",
            sub="u1",
            is_superadmin=False,
            permissions=["purchase-requests.access", "purchase-requests.unit.filial-02"],
        ),
        branch="02",
        page=1,
        page_size=10,
    )
    assert result["total"] == 1
    assert len(result["items"]) == 50
    assert {item["request_item"] for item in result["items"]} == {f"{i:04d}" for i in range(1, 51)}


def test_pagination_partial_sc_only_visible_items_and_single_header() -> None:
    lines = [
        _line(request_number="100", request_item="0001", cost_center="0413"),
        _line(request_number="100", request_item="0002", cost_center="0520"),
        _line(request_number="100", request_item="0003", cost_center="0413"),
    ]
    aggregation = PurchaseRequestAggregationService()
    resolution = ScopeResolution(
        view_all=False,
        allowed_cost_centers=frozenset({CostCenterScope("02", "0413")}),
    )
    visible = aggregation.filter_authorized_lines(lines, branch="02", resolution=resolution)
    list_items = aggregation.build_list_line_items(visible)
    assert len(list_items) == 2
    assert {item["request_item"] for item in list_items} == {"0001", "0003"}
    assert "0520" not in {item.get("cost_center_code") for item in list_items}


def test_pagination_total_follows_request_grain_from_gateway() -> None:
    gateway = MagicMock()
    gateway.list_lines.return_value = {
        "items": [
            _line(request_number="100", request_item="0001", cost_center="0413"),
            _line(request_number="200", request_item="0001", cost_center="0413"),
        ],
        "page": 1,
        "page_size": 10,
        "total": 2,
        "total_pages": 1,
    }
    scope_repo = MagicMock()
    scope_repo.list_active_cost_centers_for_user.return_value = [
        {"branch": "02", "cost_center_code": "0413"}
    ]
    result = ListPurchaseRequestsUseCase(gateway=gateway, scope_repository=scope_repo).execute(
        user=SimpleNamespace(
            id="u1",
            sub="u1",
            is_superadmin=False,
            permissions=["purchase-requests.access", "purchase-requests.unit.filial-02"],
        ),
        branch="02",
    )
    assert result["total"] == 2
    assert len(result["items"]) == 2


def test_pagination_does_not_split_same_request_across_pages() -> None:
    page_one_numbers = {"100", "200", "300", "400", "500", "600", "700", "800", "900", "1000"}
    lines = [
        _line(request_number=number, request_item="0001", cost_center="0413")
        for number in page_one_numbers
    ]
    gateway = MagicMock()
    gateway.list_lines.return_value = {
        "items": lines,
        "page": 1,
        "page_size": 10,
        "total": 12,
        "total_pages": 2,
    }
    scope_repo = MagicMock()
    scope_repo.list_active_cost_centers_for_user.return_value = [
        {"branch": "02", "cost_center_code": "0413"}
    ]
    result = ListPurchaseRequestsUseCase(gateway=gateway, scope_repository=scope_repo).execute(
        user=SimpleNamespace(
            id="u1",
            sub="u1",
            is_superadmin=False,
            permissions=["purchase-requests.access", "purchase-requests.unit.filial-02"],
        ),
        branch="02",
        page=1,
        page_size=10,
    )
    returned_numbers = {item["request_number"] for item in result["items"]}
    assert returned_numbers == page_one_numbers
    assert all(item["request_item"] == "0001" for item in result["items"])


def test_list_filters_by_overall_stage_after_enrichment() -> None:
    lines = [
        _line(request_number="100", request_item="0001", cost_center="0413"),
        {
            **_line(request_number="200", request_item="0001", cost_center="0413"),
            "ordered_quantity": 1.0,
            "purchase_orders": [
                {
                    "branch": "02",
                    "order_number": "PC1",
                    "order_item": "0001",
                    "ordered_quantity": 1.0,
                    "received_quantity": 0.0,
                    "open_quantity": 1.0,
                }
            ],
        },
    ]
    gateway = MagicMock()
    gateway.list_lines.return_value = {
        "items": lines,
        "page": 1,
        "page_size": 50,
        "total": 2,
        "total_pages": 1,
    }
    scope_repo = MagicMock()
    scope_repo.list_active_cost_centers_for_user.return_value = [
        {"branch": "02", "cost_center_code": "0413"}
    ]
    user = SimpleNamespace(
        id="u1",
        sub="u1",
        is_superadmin=False,
        permissions=["purchase-requests.access", "purchase-requests.unit.filial-02"],
    )
    awaiting = ListPurchaseRequestsUseCase(gateway=gateway, scope_repository=scope_repo).execute(
        user=user,
        branch="02",
        overall_stage="awaiting_order",
    )
    assert len(awaiting["items"]) == 1
    assert awaiting["items"][0]["request_number"] == "100"

    receipt = ListPurchaseRequestsUseCase(gateway=gateway, scope_repository=scope_repo).execute(
        user=user,
        branch="02",
        overall_stage="awaiting_receipt",
    )
    assert len(receipt["items"]) == 1
    assert receipt["items"][0]["request_number"] == "200"
