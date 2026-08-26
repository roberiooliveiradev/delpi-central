from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from purchase_requests_app.application.services.purchase_request_aggregation_service import (
    PurchaseRequestAggregationService,
)
from purchase_requests_app.application.use_cases.get_purchase_request_use_case import (
    GetPurchaseRequestUseCase,
)
from purchase_requests_app.application.use_cases.list_purchase_requests_use_case import (
    ListPurchaseRequestsUseCase,
)
from purchase_requests_app.domain.services.purchase_request_domain_service import (
    CostCenterScope,
    ScopeResolution,
)


def _user(permissions: list[str], user_id: str = "u1"):
    return SimpleNamespace(
        id=user_id,
        sub=user_id,
        is_superadmin=False,
        permissions=permissions,
    )


def test_security_case_user_without_cc_gets_empty_list() -> None:
    gateway = MagicMock()
    scope_repo = MagicMock()
    scope_repo.list_active_cost_centers_for_user.return_value = []
    use_case = ListPurchaseRequestsUseCase(
        gateway=gateway,
        scope_repository=scope_repo,
    )
    result = use_case.execute(
        user=_user(["purchase-requests.access", "purchase-requests.unit.filial-01"]),
        branch="01",
    )
    assert result["items"] == []
    assert result["total"] == 0
    gateway.list_lines.assert_not_called()


def test_security_case_partial_sc_does_not_leak_hidden_item() -> None:
    aggregation = PurchaseRequestAggregationService()
    resolution = ScopeResolution(
        view_all=False,
        allowed_cost_centers=frozenset({CostCenterScope("02", "0413")}),
    )
    lines = [
        {
            "branch": "02",
            "request_number": "100",
            "request_item": "0001",
            "cost_center_code": "0413",
            "request_issue_date": "2026-08-01",
            "requester_protheus_user_id": "1",
            "requested_quantity": 1,
            "ordered_quantity": 0,
            "purchase_orders": [],
        },
        {
            "branch": "02",
            "request_number": "100",
            "request_item": "0002",
            "cost_center_code": "0520",
            "request_issue_date": "2026-08-01",
            "requester_protheus_user_id": "2",
            "requested_quantity": 9,
            "ordered_quantity": 0,
            "purchase_orders": [],
        },
    ]
    visible = aggregation.filter_authorized_lines(lines, branch="02", resolution=resolution)
    assert len(visible) == 1
    assert visible[0]["request_item"] == "0001"
    header = aggregation.aggregate_list_items(visible)[0]
    assert header["visible_items_count"] == 1
    assert header["requested_quantity"] == 1
    assert {cc["code"] for cc in header["cost_centers"]} == {"0413"}


def test_security_case_detail_invisible_returns_not_found() -> None:
    gateway = MagicMock()
    gateway.get_request_lines.return_value = {
        "lines": [
            {
                "branch": "02",
                "request_number": "100",
                "request_item": "0002",
                "cost_center_code": "0520",
                "purchase_orders": [],
            }
        ]
    }
    scope_repo = MagicMock()
    scope_repo.list_active_cost_centers_for_user.return_value = [
        {"branch": "02", "cost_center_code": "0413"}
    ]
    use_case = GetPurchaseRequestUseCase(
        gateway=gateway,
        scope_repository=scope_repo,
    )
    with pytest.raises(LookupError):
        use_case.execute(
            user=_user(["purchase-requests.access", "purchase-requests.unit.filial-02"]),
            branch="02",
            request_number="100",
        )


def test_security_case_view_all_does_not_filter_by_scope_rows() -> None:
    gateway = MagicMock()
    gateway.list_lines.return_value = {
        "items": [],
        "page": 1,
        "page_size": 50,
        "total": 0,
        "total_pages": 0,
    }
    scope_repo = MagicMock()
    scope_repo.list_active_cost_centers_for_user.return_value = []
    use_case = ListPurchaseRequestsUseCase(
        gateway=gateway,
        scope_repository=scope_repo,
    )
    use_case.execute(
        user=_user(
            [
                "purchase-requests.access",
                "purchase-requests.view-all",
                "purchase-requests.unit.filial-01",
            ]
        ),
        branch="01",
    )
    _, kwargs = gateway.list_lines.call_args
    assert "cost_centers" not in (kwargs.get("params") or {})
