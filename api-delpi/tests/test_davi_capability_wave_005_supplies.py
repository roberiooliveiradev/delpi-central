"""DAVI Wave 005 — Supplies governed READ promotion."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.application.external_capabilities.constants import (
    MCP_TOOL_SEARCH_PRODUCTS,
)
from app.application.external_capabilities.dynamic_information.action_index import (
    reset_action_index_for_tests,
    set_actions_for_tests,
)
from app.application.external_capabilities.dynamic_information.catalog_builder import (
    TechnicalAction,
    build_technical_actions_from_baseline,
)
from app.application.external_capabilities.dynamic_information.content_loader import (
    load_dynamic_read_budgets,
    load_external_read_allowlist,
)
from app.application.external_capabilities.dynamic_information.projection import (
    apply_approved_field_projection,
    classify_source_pagination,
)
from app.application.external_capabilities.dynamic_information.read_only_intent_guard import (
    clear_read_only_intent_guard_cache,
)
from app.domain.ports.davi_catalog_action_executor_port import CatalogActionExecutionResult

_API_ROOT = Path(__file__).resolve().parents[1]

_PROMOTED = (
    "get_supplies_cpv",
    "get_supplies_inventory_turnover",
    "get_supplies_negotiation_savings_summary",
    "get_supplies_otd",
    "get_supplies_purchase_order_otd",
    "get_supplies_purchase_order_otd_series",
    "get_supplies_stock_value",
    "get_supplies_safety_stock_summary",
    "get_supplies_safety_stock_items",
    "get_supplies_safety_stock_item_suppliers",
    "get_supplies_safety_stock_supplier_purchase_price_history",
    "get_supplies_safety_stock_consumption_analysis_summary",
    "get_supplies_safety_stock_consumption_analysis_items",
    "get_supplies_stock_balances_summary",
    "get_supplies_stock_balances_items",
    "get_supplies_third_party_materials_summary",
    "get_supplies_third_party_materials_shipments",
    "list_supplies_purchase_request_lines",
)
# get_supplies_safety_stock_item_details and
# get_supplies_safety_stock_consumption_analysis_item_details were deferred at
# wave 005 and later promoted by
# DAVI-INVENTORY-MATERIAL-FLOW-IMPLEMENTATION-001 (allowlist v18).
_DEFERRED = (
    "get_supplies_purchase_order_otd_panel",
    "get_supplies_purchase_requests_open_coverage",
    "get_supplies_purchase_request_lines",
    "get_supplies_safety_stock_filters",
    "get_supplies_third_party_materials_shipment",
    "list_supplies_purchase_request_recent_linked_orders",
    "list_supplies_purchase_request_recent_linked_receipts",
    "list_supplies_purchase_request_requesters",
    "get_supplies_protheus_user_by_email",
)
_REJECTED = ("export_supplies_third_party_materials_returns",)
_PRIOR_THIRTY_FIVE = (
    "search_products",
    "get_product_stock",
    "get_product_suppliers",
    "get_product_customers",
    "get_product_purchases",
    "get_product_structure",
    "get_product_production_status",
    "get_product_factory_status",
    "get_product_structure_exclusivity",
    "get_product_shipping_status",
    "get_product_pricing",
    "get_product_purchase_price_history",
    "get_product_last_purchase",
    "get_product_guide",
    "get_product_parents",
    "list_product_drawings",
    "get_product_drawing",
    "get_commercial_rol_summary",
    "get_commercial_rol_series",
    "get_commercial_rol_by_branch",
    "get_commercial_rol_by_customer",
    "get_commercial_rol_by_product",
    "get_new_business_rol_pct",
    "get_new_business_rol_target_pct",
    "get_new_clients_average",
    "get_new_clients_rol_pct",
    "get_sales_conversion_rate",
    "get_sales_conversion_rate_series",
    "get_sales_order_otd",
    "get_sales_order_otd_summary",
    "get_sales_order_otd_by_branch",
    "get_sales_order_otd_by_customer",
    "get_sales_order_otd_series",
    "get_sales_order_otd_series_by_customer",
    "get_weg_rol_target_pct",
)


@pytest.fixture(autouse=True)
def _reset_index():
    reset_action_index_for_tests()
    load_external_read_allowlist.cache_clear()
    load_dynamic_read_budgets.cache_clear()
    clear_read_only_intent_guard_cache()
    yield
    reset_action_index_for_tests()
    load_external_read_allowlist.cache_clear()
    load_dynamic_read_budgets.cache_clear()
    clear_read_only_intent_guard_cache()


def _actions() -> list[TechnicalAction]:
    baseline = json.loads(
        (_API_ROOT / "app/content/openapi_baseline.json").read_text(encoding="utf-8")
    )
    return build_technical_actions_from_baseline(
        baseline, allowlist=load_external_read_allowlist()
    )


def _action(oid: str) -> TechnicalAction:
    return next(a for a in _actions() if a.operation_id == oid)


def _allowlist_entry(oid: str) -> dict[str, Any]:
    allow = load_external_read_allowlist()
    for entry in allow.get("operations") or []:
        if entry.get("operationId") == oid:
            return entry
    raise AssertionError(f"missing allowlist entry {oid}")


def test_wave005_allowlist_version_and_eligible_count():
    allow = load_external_read_allowlist()
    # Wave 005 historical: promoted set remains eligible after later waves
    eligible = {a.operation_id for a in _actions() if a.executable}
    assert len(eligible) >= 53
    assert set(_PRIOR_THIRTY_FIVE) <= eligible
    assert set(_PROMOTED) <= eligible
    for oid in (*_DEFERRED, *_REJECTED):
        assert oid not in eligible


@pytest.mark.parametrize("oid", _PROMOTED)
def test_wave005_promoted_contract_matrix(oid: str):
    action = _action(oid)
    entry = _allowlist_entry(oid)
    assert action.method.upper() == "GET"
    assert action.executable is True
    fields_in = list(entry.get("approvedInputFields") or [])
    fields_out = list(entry.get("approvedResponseFields") or [])
    assert fields_in
    assert fields_out
    assert all("*" not in f for f in fields_out)
    assert all("/" not in f for f in fields_in)
    param_names = {p["name"] for p in (action.parameters or ()) if isinstance(p, dict)}
    for name in fields_in:
        assert name in param_names or name in action.path, (oid, name)
    assert "url" not in fields_in
    assert "operationId" not in fields_in
    assert "sql" not in fields_in
    assert entry.get("semanticAliases")


@pytest.mark.parametrize("oid", (*_DEFERRED, *_REJECTED))
def test_wave005_deferred_and_rejected_not_executable(oid: str):
    action = _action(oid)
    assert action.executable is False


def test_wave005_mcp_tools_wave001_four():
    import asyncio

    from app.interface.mcp.server import create_mcp_server

    tools = asyncio.run(create_mcp_server().list_tools())
    assert [t.name for t in tools] == [
        "get_context",
        "knowledge",
        "read",
        "analyze",
    ]


def test_wave005_suppliers_drop_tax_document():
    raw = {
        "items": [
            {
                "product_code": "P1",
                "supplier_code": "F1",
                "supplier_store": "01",
                "trade_name": "Fornecedor",
                "document": "12.345.678/0001-99",
                "has_last_purchase": True,
                "last_unit_price": 10.0,
                "last_quantity": 2.0,
            }
        ],
        "total": 1,
    }
    fields = tuple(
        _allowlist_entry("get_supplies_safety_stock_item_suppliers")["approvedResponseFields"]
    )
    projected = apply_approved_field_projection(raw, approved_fields=fields)
    assert projected["items"][0]["supplier_code"] == "F1"
    assert "document" not in projected["items"][0]


def test_wave005_nested_purchase_orders_projection():
    raw = {
        "items": [
            {
                "branch": "01",
                "request_number": "000001",
                "request_item": "0001",
                "product_code": "P1",
                "product_description": "Item",
                "unit": "UN",
                "requested_quantity": 10,
                "ordered_quantity": 5,
                "request_open_quantity": 5,
                "requester_code": "U1",
                "requester_name": "Ana",
                "approval_status": "approved",
                "purchase_orders": [
                    {
                        "order_number": "PC1",
                        "ordered_quantity": 5,
                        "received_quantity": 1,
                        "buyer_secret": "x",
                    }
                ],
            }
        ],
        "page": 1,
        "page_size": 50,
        "total": 1,
        "total_pages": 1,
    }
    fields = tuple(
        _allowlist_entry("list_supplies_purchase_request_lines")["approvedResponseFields"]
    )
    projected = apply_approved_field_projection(raw, approved_fields=fields)
    assert projected["items"][0]["purchase_orders"][0]["order_number"] == "PC1"
    assert "buyer_secret" not in projected["items"][0]["purchase_orders"][0]


def test_wave005_stock_balances_pagination_partial():
    payload = {
        "items": [{"product_code": "1"}],
        "page": 1,
        "page_size": 50,
        "total": 120,
        "total_pages": 3,
    }
    assert classify_source_pagination(payload) == "partial"


def test_stock_balances_summary_preserves_branch_warehouse_grain():
    """EXECUTION_DRIFT fix: warehouse alone is NOT row identity across branches."""
    raw = {
        "summary": {
            "branch": "consolidated",
            "warehouse": "all",
            "product_count": 10,
            "total_quantity": 100.0,
            "total_stock_value": 1000.0,
            "warehouse_count": 2,
            "valuation": "qatu_times_cm1_same_local",
        },
        "by_warehouse": [
            {
                "branch": "01",
                "warehouse": "01",
                "warehouse_label": "Produção",
                "product_count": 4,
                "total_quantity": 40.0,
                "total_stock_value": 400.0,
                "total_stock_value_vatu1": 400.0,
                "internal_note": "drop-me",
            },
            {
                "branch": "02",
                "warehouse": "01",
                "warehouse_label": "Produção",
                "product_count": 6,
                "total_quantity": 60.0,
                "total_stock_value": 600.0,
                "total_stock_value_vatu1": 600.0,
            },
        ],
    }
    fields = tuple(
        _allowlist_entry("get_supplies_stock_balances_summary")["approvedResponseFields"]
    )
    assert "by_warehouse[].branch" in fields
    projected = apply_approved_field_projection(raw, approved_fields=fields)
    rows = projected["by_warehouse"]
    grains = {(row["branch"], row["warehouse"]) for row in rows}
    assert grains == {("01", "01"), ("02", "01")}
    assert projected["summary"]["branch"] == "consolidated"
    for row in rows:
        assert "branch" in row
        assert "warehouse" in row
        assert "warehouse_label" in row
        assert "product_count" in row
        assert "total_quantity" in row
        assert "total_stock_value" in row
        assert "total_stock_value_vatu1" not in row
        assert "internal_note" not in row


def test_stock_balances_summary_single_branch_still_exposes_branch():
    raw = {
        "summary": {
            "branch": "01",
            "warehouse": "all",
            "product_count": 2,
            "total_quantity": 5.0,
            "total_stock_value": 50.0,
            "warehouse_count": 1,
            "valuation": "qatu_times_cm1_same_local",
        },
        "by_warehouse": [
            {
                "branch": "01",
                "warehouse": "50",
                "warehouse_label": "WIP / processo",
                "product_count": 2,
                "total_quantity": 5.0,
                "total_stock_value": 50.0,
            }
        ],
    }
    fields = tuple(
        _allowlist_entry("get_supplies_stock_balances_summary")["approvedResponseFields"]
    )
    projected = apply_approved_field_projection(raw, approved_fields=fields)
    assert projected["by_warehouse"][0]["branch"] == "01"
    assert projected["by_warehouse"][0]["warehouse"] == "50"


def test_stock_balances_items_already_preserves_branch():
    fields = tuple(
        _allowlist_entry("get_supplies_stock_balances_items")["approvedResponseFields"]
    )
    assert "items[].branch" in fields
    assert "items[].warehouse" in fields
    raw = {
        "items": [
            {
                "product_code": "P1",
                "description": "Item",
                "unit_of_measure": "UN",
                "branch": "01",
                "warehouse": "01",
                "warehouse_label": "Produção",
                "quantity": 1.0,
                "stock_value": 10.0,
                "unit_cost": 10.0,
            }
        ],
        "page": 1,
        "page_size": 50,
        "total": 1,
        "total_pages": 1,
    }
    projected = apply_approved_field_projection(raw, approved_fields=fields)
    assert projected["items"][0]["branch"] == "01"
    assert projected["items"][0]["warehouse"] == "01"
    assert "unit_cost" not in projected["items"][0]


def test_wave005_drawing_pdf_still_not_executable():
    assert _action("get_product_drawing_pdf").executable is False
def test_wave005_agent_intelligence_unchanged():
    intel = json.loads(
        (_API_ROOT / "app/content/davi_agent_intelligence.json").read_text(encoding="utf-8")
    )
    assert intel.get("version") >= "2026.10.06.1"
    blob = json.dumps(intel)
    for oid in _PROMOTED:
        assert oid not in blob
