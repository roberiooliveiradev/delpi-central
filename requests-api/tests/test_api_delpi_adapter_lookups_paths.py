"""Adapter aponta lookups canônicos /request-lookups (E17)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from requests_app.infrastructure.gateways.api_delpi_adapter import ApiDelpiAdapter


def test_adapter_uses_request_lookups_prefix() -> None:
    adapter = ApiDelpiAdapter(base_url="http://api-delpi.test")
    with patch.object(adapter, "_get", return_value={"items": []}) as get:
        adapter.search_parties(party_type="customer", query="ab", limit=5)
        adapter.search_products(query="ab")
        adapter.search_carriers(query="ab")
        adapter.list_open_sales_orders(
            branch="01", party_code="C1", party_store="01"
        )
        adapter.get_warehouse_01_balance(product_code="P1", branch="01")

    paths = [call.args[0] for call in get.call_args_list]
    assert paths == [
        "/request-lookups/parties",
        "/request-lookups/products",
        "/request-lookups/carriers",
        "/request-lookups/open-sales-orders",
        "/request-lookups/products/P1/warehouse-01-balance",
    ]
    assert all("/invoice-issuance/" not in path for path in paths)
