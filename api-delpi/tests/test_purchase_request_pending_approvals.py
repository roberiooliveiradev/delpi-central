import json
from unittest.mock import Mock, patch

import pytest

from app.infrastructure.persistence.totvs.supplies_repositories.purchase_request_pending_approvals_repository import (
    PurchaseRequestPendingApprovalsRepository,
)


class FakeRepository(PurchaseRequestPendingApprovalsRepository):
    def __init__(self, rows):
        self.rows = rows
        self.queries = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def execute_query(self, sql, params=()):
        self.queries.append((sql, params))
        return (
            self.rows
            if len(self.queries) == 1
            else [
                {
                    "branch": "01",
                    "request_number": "000001",
                    "product_code": "P1",
                    "product_description": "Produto 1",
                }
            ]
        )


def row(number="000001", **overrides):
    return {
        "branch": "01",
        "request_number": number,
        "requester_user_id": "000123",
        "approver_code": "000005",
        "approver_name": "Max",
        "approver_user_code": "000456",
        "level": "01",
        **overrides,
    }


def test_keyset_pages_whole_requests_and_keeps_all_parallel_approvers():
    repo = FakeRepository(
        [row(), row(approver_code="000006", approver_user_code="000789"), row("000002")]
    )
    payload = repo.list_pending_approvals(limit=1)
    assert len(payload["items"]) == 1
    assert len(payload["items"][0]["pending_approvers"]) == 2
    assert payload["items"][0]["products"] == [
        {"code": "P1", "description": "Produto 1"}
    ]
    assert payload["next_cursor"] == {
        "after_branch": "01",
        "after_request_number": "000001",
    }
    sql, params = repo.queries[0]
    assert params == ("01", "02", "", "", "")
    assert "H.rn <= 2" in sql
    assert "C1_EMISSAO >=" not in sql
    assert "SCR.CR_STATUS) = '02'" in sql
    assert "AK.AK_COD = SCR.CR_APROV" in sql
    assert "AK.AK_USER" in sql
    assert "H.blocked_items > 0" in sql
    assert "Rejected.C1_APROV = 'R'" in sql
    assert "SC1.C1_RESIDUO <> 'S'" in sql
    assert "SC1.C1_QUANT > SC1.C1_QUJE" in sql
    assert "ORDER BY H.branch, H.request_number" in sql


@pytest.mark.parametrize(
    "cursor",
    [
        {"after_branch": "01"},
        {"after_branch": "99", "after_request_number": "001"},
        {"after_branch": "01", "after_request_number": "1'; DROP TABLE SC1010"},
    ],
)
def test_invalid_cursor_rejected_before_sql(cursor):
    repo = FakeRepository([])
    with pytest.raises(ValueError):
        repo.list_pending_approvals(**cursor)
    assert not repo.queries


def test_empty_page_does_not_query_products_and_ends_scan():
    repo = FakeRepository([])
    assert repo.list_pending_approvals()["next_cursor"] is None
    assert len(repo.queries) == 1


def test_feed_response_matches_documented_schema_and_openapi():
    from fastapi import FastAPI
    from app.interface.http.routes.supplies.purchase_requests_router import router
    from app.interface.http.schemas.purchase_request_pending_approvals_schema import (
        PendingApprovalPage,
    )

    payload = FakeRepository([row()]).list_pending_approvals()
    assert (
        PendingApprovalPage.model_validate(payload).items[0].request_number == "000001"
    )
    app = FastAPI()
    app.include_router(router)
    spec = app.openapi()
    operation = spec["paths"]["/supplies/purchase-requests/pending-approvals"]["get"]
    assert (
        operation["operationId"] == "list_supplies_purchase_request_pending_approvals"
    )
    assert operation["responses"]["200"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("PendingApprovalResponse")


def test_internal_feed_denies_regular_users_even_with_read_permission():
    from app.interface.http.routes.supplies.purchase_requests_router import (
        list_supplies_purchase_request_pending_approvals_route,
    )

    with patch(
        "app.interface.http.supplies_bff_service_access.is_trusted_internal_caller",
        return_value=False,
    ):
        response = list_supplies_purchase_request_pending_approvals_route(
            after_branch="", after_request_number="", limit=25
        )
    assert response.status_code == 403


def test_internal_feed_envelope_and_use_case_wiring():
    from app.interface.http.routes.supplies.purchase_requests_router import (
        list_supplies_purchase_request_pending_approvals_route,
    )

    payload = {"items": [], "limit": 25, "next_cursor": None}
    with patch(
        "app.interface.http.supplies_bff_service_access.is_trusted_internal_caller",
        return_value=True,
    ), patch.object(
        PurchaseRequestPendingApprovalsRepository,
        "list_pending_approvals",
        return_value=payload,
    ) as read:
        response = list_supplies_purchase_request_pending_approvals_route(
            after_branch="", after_request_number="", limit=25
        )
    data = json.loads(response.body)
    assert data["data"] == payload
    assert (
        data["meta"]["operationId"]
        == "list_supplies_purchase_request_pending_approvals"
    )
    read.assert_called_once_with(after_branch="", after_request_number="", limit=25)
