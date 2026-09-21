from types import SimpleNamespace
from unittest.mock import MagicMock

from purchase_requests_app.application.security.supplies_portal_context import (
    bind_http_request,
    reset_http_request,
)
from purchase_requests_app.application.services.purchase_request_aggregation_service import (
    ATTENTION_BUCKETS,
    OVERALL_STAGE_SORT_ORDER,
    PurchaseRequestAggregationService,
)
from purchase_requests_app.application.use_cases.list_purchase_requests_use_case import (
    ListPurchaseRequestsUseCase,
)


def _user(*codes: str):
    return SimpleNamespace(
        id="u1",
        sub="u1",
        is_superadmin=False,
        permissions=set(codes),
    )


def _request(*, caller: str, token: str):
    return SimpleNamespace(
        headers={
            "X-Delpi-Caller-App": caller,
            "X-Delpi-Service-Token": token,
        }
    )


def _scope():
    scope_repo = MagicMock()
    scope_repo.list_active_cost_centers_for_user.return_value = [
        {"branch": "02", "cost_center_code": "0413"}
    ]
    return scope_repo


def _line(
    *,
    request_number: str,
    request_item: str = "0001",
    ordered_quantity: float = 0.0,
    requested_quantity: float = 1.0,
    residual: bool = False,
    orders: list | None = None,
) -> dict:
    return {
        "branch": "02",
        "request_number": request_number,
        "request_item": request_item,
        "cost_center_code": "0413",
        "request_issue_date": "2026-08-01",
        "requested_quantity": requested_quantity,
        "ordered_quantity": ordered_quantity,
        "residual": residual,
        "purchase_orders": orders or [],
    }


def _order(*, received: float, ordered: float = 1.0) -> dict:
    return {
        "branch": "02",
        "order_number": "PC1",
        "order_item": "0001",
        "ordered_quantity": ordered,
        "received_quantity": received,
        "open_quantity": max(ordered - received, 0),
    }


def _use_case(items: list[dict], *, total: int | None = None) -> tuple[ListPurchaseRequestsUseCase, MagicMock]:
    gateway = MagicMock()
    gateway.list_lines.return_value = {
        "items": items,
        "page": 1,
        "page_size": 200,
        "total": len({item["request_number"] for item in items}) if total is None else total,
        "total_pages": 1,
    }
    return (
        ListPurchaseRequestsUseCase(gateway=gateway, scope_repository=_scope()),
        gateway,
    )


def test_attention_buckets_cover_canonical_stages_once() -> None:
    covered = [stage for members in ATTENTION_BUCKETS.values() for stage in members]
    assert tuple(covered) == OVERALL_STAGE_SORT_ORDER


def test_summary_empty() -> None:
    use_case, _gateway = _use_case([])
    summary = use_case.summarize(user=_user("purchase-requests.access", "purchase-requests.unit.filial-02"), branch="02")
    assert summary["total_requests"] == 0
    assert summary["total_items"] == 0
    assert all(count == 0 for count in summary["stage_counts"].values())
    assert summary["buckets"] == {"ordering": 0, "receiving": 0, "completed": 0}


def test_summary_counts_headers_items_and_each_derivable_stage() -> None:
    lines = [
        _line(request_number="1"),
        _line(request_number="2", ordered_quantity=0.4),
        _line(request_number="3", ordered_quantity=1, orders=[_order(received=0)]),
        _line(request_number="4", ordered_quantity=1, orders=[_order(received=0.4)]),
        _line(request_number="5", ordered_quantity=1, orders=[_order(received=1)]),
        _line(request_number="6", residual=True),
        _line(request_number="5", request_item="0002", ordered_quantity=1, orders=[_order(received=1)]),
    ]
    use_case, _gateway = _use_case(lines)
    summary = use_case.summarize(
        user=_user("purchase-requests.access", "purchase-requests.unit.filial-02"),
        branch="02",
    )
    assert summary["total_requests"] == 6
    assert summary["total_items"] == 7
    counts = summary["stage_counts"]
    assert counts["awaiting_order"] == 1
    assert counts["partially_ordered"] == 1
    assert counts["ordered"] == 0
    assert counts["awaiting_receipt"] == 1
    assert counts["partially_received"] == 1
    assert counts["completed"] == 1
    assert counts["residual_closed"] == 1
    assert summary["buckets"]["ordering"] == 2
    assert summary["buckets"]["receiving"] == 2
    assert summary["buckets"]["completed"] == 2


def test_summary_ignores_selected_stage_and_applies_base_filters() -> None:
    lines = [
        _line(request_number="1"),
        _line(request_number="2", ordered_quantity=1, orders=[_order(received=1)]),
    ]
    use_case, gateway = _use_case(lines)
    summary = use_case.summarize(
        user=_user("purchase-requests.access", "purchase-requests.unit.filial-02"),
        branch="02",
        product_code="MP1",
        overall_stage="completed",
    )
    assert summary["total_requests"] == 2
    assert summary["buckets"]["ordering"] == 1
    assert summary["buckets"]["completed"] == 1
    params = gateway.list_lines.call_args.kwargs["params"]
    assert params["product_code"] == "MP1"
    assert "overall_stage" not in params


def test_summary_unknown_branch_rejected() -> None:
    use_case, gateway = _use_case([])
    try:
        use_case.summarize(
            user=_user("purchase-requests.access", "purchase-requests.unit.filial-02"),
            branch="99",
        )
        raise AssertionError("expected permission error")
    except PermissionError:
        pass
    gateway.list_lines.assert_not_called()


def test_summary_direct_supplies_access_is_not_portal(monkeypatch) -> None:
    monkeypatch.delenv("API_DELPI_INTERNAL_SERVICE_TOKEN", raising=False)
    use_case, gateway = _use_case([])
    try:
        use_case.summarize(user=_user("supplies.access"), branches=["01"])
        raise AssertionError("expected permission error")
    except PermissionError:
        pass
    gateway.list_lines.assert_not_called()


def test_summary_trusted_portal_context(monkeypatch) -> None:
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "svc-secret")
    use_case, gateway = _use_case([])
    token = bind_http_request(_request(caller="supplies-api", token="svc-secret"))
    try:
        summary = use_case.summarize(user=_user("supplies.access"), branches=["01", "02"])
    finally:
        reset_http_request(token)
    assert summary["total_requests"] == 0
    params = gateway.list_lines.call_args.kwargs["params"]
    assert "cost_centers" not in params
    assert "cc_scope" not in params


def test_conservative_stage_rollup_direct() -> None:
    service = PurchaseRequestAggregationService()
    mixed = [
        _line(request_number="9", request_item="0001"),
        _line(
            request_number="9",
            request_item="0002",
            ordered_quantity=1,
            orders=[_order(received=1)],
        ),
    ]
    summary = service.summarize_lines(mixed)
    assert summary["total_requests"] == 1
    assert summary["total_items"] == 2
    assert summary["stage_counts"]["awaiting_order"] == 1
    assert summary["buckets"]["ordering"] == 1
    assert summary["buckets"]["completed"] == 0
