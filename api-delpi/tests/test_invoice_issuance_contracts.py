"""Contratos e permissões — invoice-issuance."""

from __future__ import annotations

from app.application.security import api_delpi_permissions as perms
from app.interface.http.route_contract_registry import ROUTE_CONTRACTS

OPERATION_IDS = {
    "create_invoice_issuance_request",
    "list_invoice_issuance_requests",
    "get_invoice_issuance_request",
    "update_invoice_issuance_request",
    "resubmit_invoice_issuance_request",
    "start_invoice_issuance_request",
    "return_invoice_issuance_request",
    "issue_invoice_issuance_request",
    "cancel_invoice_issuance_request",
}

REMOVED_LOOKUP_OPERATION_IDS = {
    "search_invoice_issuance_parties",
    "search_invoice_issuance_products",
    "get_invoice_issuance_warehouse_01_balance",
    "list_invoice_issuance_open_sales_orders",
    "search_invoice_issuance_carriers",
}


def test_permission_constants() -> None:
    assert perms.INVOICE_ISSUANCE_CREATE == "invoice-issuance.create"
    assert perms.INVOICE_ISSUANCE_VIEW == "invoice-issuance.view"
    assert perms.INVOICE_ISSUANCE_PROCESS == "invoice-issuance.process"
    assert perms.INVOICE_ISSUANCE_MANAGE == "invoice-issuance.manage"
    assert perms.INVOICE_ISSUANCE_VIEW_FILIAL_01 == "invoice-issuance.view.filial-01"
    assert perms.INVOICE_ISSUANCE_VIEW_FILIAL_02 == "invoice-issuance.view.filial-02"
    assert perms.INVOICE_ISSUANCE_CREATE in perms.INVOICE_ISSUANCE_READ_PERMISSIONS
    assert perms.INVOICE_ISSUANCE_PROCESS in perms.INVOICE_ISSUANCE_PROCESS_PERMISSIONS
    assert perms.INVOICE_ISSUANCE_BRANCH_VIEW_PERMS["01"] == perms.INVOICE_ISSUANCE_VIEW_FILIAL_01


def test_route_contracts_registered() -> None:
    missing = sorted(OPERATION_IDS - set(ROUTE_CONTRACTS))
    assert not missing, f"operation_id ausente: {missing}"
    assert ROUTE_CONTRACTS["list_invoice_issuance_requests"].shape == "paged_list"
    assert ROUTE_CONTRACTS["create_invoice_issuance_request"].entity == "invoice_issuance_request"
    for oid in REMOVED_LOOKUP_OPERATION_IDS:
        assert oid not in ROUTE_CONTRACTS, f"lookup legado ainda no registry: {oid}"


def test_router_exposes_invoice_issuance_operation_ids() -> None:
    from app.interface.http.routes.invoice_issuance.invoice_issuance_router import router

    ids = {route.operation_id for route in router.routes if getattr(route, "operation_id", None)}
    assert OPERATION_IDS <= ids
    assert not (REMOVED_LOOKUP_OPERATION_IDS & ids)


def test_router_has_no_legacy_lookup_paths() -> None:
    from app.interface.http.routes.invoice_issuance.invoice_issuance_router import router

    paths = {getattr(route, "path", "") for route in router.routes}
    assert "/invoice-issuance/parties" not in paths
    assert "/invoice-issuance/products" not in paths
    assert "/invoice-issuance/carriers" not in paths
    assert "/invoice-issuance/open-sales-orders" not in paths
    assert not any("warehouse-01-balance" in p for p in paths)


def test_list_requests_returns_success_envelope() -> None:
    """Regressão: listagem 500 por NameError em api_delpi_success (ago/2026)."""
    from unittest.mock import patch

    from app.interface.http.route_response_helpers import api_delpi_success as canonical
    from app.interface.http.routes.invoice_issuance import invoice_issuance_router as mod
    from tests.support.route_contract_smoke import assert_envelope_meta, body_json

    assert mod.api_delpi_success is canonical

    payload = {"items": [], "total": 0, "page": 1, "page_size": 20, "total_pages": 0}
    with (
        patch.object(mod, "branch_access_error", return_value=None),
        patch.object(mod, "build_list_use_case") as build,
        patch.object(mod, "_actor"),
    ):
        build.return_value.execute.return_value = payload
        response = mod.list_requests(
            branch="01",
            status="open",
            invoice_type=None,
            q=None,
            page=1,
            page_size=20,
        )
    body = body_json(response)
    assert_envelope_meta(body, operation_id="list_invoice_issuance_requests")
    assert body["data"]["items"] == []
