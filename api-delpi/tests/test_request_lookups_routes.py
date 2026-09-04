"""Contratos e smoke — /request-lookups (E17)."""

from __future__ import annotations

from app.application.security import api_delpi_permissions as perms
from app.interface.http.route_contract_registry import ROUTE_CONTRACTS

OPERATION_IDS = {
    "search_request_lookup_parties",
    "search_request_lookup_products",
    "get_request_lookup_warehouse_01_balance",
    "list_request_lookup_open_sales_orders",
    "search_request_lookup_carriers",
}


def test_request_lookups_permission_bundle() -> None:
    assert perms.MY_REQUESTS_INVOICE_CREATE in perms.REQUEST_LOOKUPS_PERMISSIONS
    assert perms.INVOICE_ISSUANCE_CREATE in perms.REQUEST_LOOKUPS_PERMISSIONS
    assert perms.MY_REQUESTS_BRANCH_VIEW_PERMS["01"] == perms.MY_REQUESTS_VIEW_FILIAL_01


def test_request_lookups_route_contracts_registered() -> None:
    missing = sorted(OPERATION_IDS - set(ROUTE_CONTRACTS))
    assert not missing, f"operation_id ausente: {missing}"
    assert ROUTE_CONTRACTS["search_request_lookup_parties"].entity == "invoice_issuance_party"
    assert ROUTE_CONTRACTS["get_request_lookup_warehouse_01_balance"].shape == "scalar"


def test_request_lookups_router_prefix() -> None:
    from app.interface.http.routes.request_lookups_router import router

    assert router.prefix == "/request-lookups"
    paths = {getattr(route, "path", "") for route in router.routes}
    assert "/request-lookups/parties" in paths
    assert "/request-lookups/products" in paths
    assert "/request-lookups/carriers" in paths
    assert "/request-lookups/open-sales-orders" in paths
    assert any("warehouse-01-balance" in p for p in paths)
