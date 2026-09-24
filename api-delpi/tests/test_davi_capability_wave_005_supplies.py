"""DAVI Wave 005 — Supplies governed READ promotion."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.application.external_capabilities.constants import (
    MCP_TOOL_DISCOVER_DELPI_INFORMATION,
    MCP_TOOL_EXECUTE_DELPI_INFORMATION,
    MCP_TOOL_SEARCH_PRODUCTS,
)
from app.application.external_capabilities.dynamic_information.action_index import (
    reset_action_index_for_tests,
    set_actions_for_tests,
)
from app.application.external_capabilities.dynamic_information.candidate_token import (
    mint_candidate_token,
)
from app.application.external_capabilities.dynamic_information.catalog_builder import (
    TechnicalAction,
    build_technical_actions_from_baseline,
)
from app.application.external_capabilities.dynamic_information.content_loader import (
    load_dynamic_read_budgets,
    load_external_read_allowlist,
)
from app.application.external_capabilities.dynamic_information.discover_service import (
    discover_delpi_information,
)
from app.application.external_capabilities.dynamic_information.execute_service import (
    execute_delpi_information,
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
_DEFERRED = (
    "get_supplies_purchase_order_otd_panel",
    "get_supplies_purchase_requests_open_coverage",
    "get_supplies_purchase_request_lines",
    "get_supplies_safety_stock_filters",
    "get_supplies_safety_stock_item_details",
    "get_supplies_safety_stock_consumption_analysis_item_details",
    "get_supplies_third_party_materials_shipment",
    "list_supplies_purchase_request_recent_linked_orders",
    "list_supplies_purchase_request_recent_linked_receipts",
    "list_supplies_purchase_request_requesters_route_supplies_purchase_requests_requesters_get",
    "get_protheus_user_by_email_route_supplies_protheus_users_by_email_get",
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


def test_wave005_mcp_tools_remain_two():
    import asyncio

    from app.interface.mcp.server import create_mcp_server

    tools = asyncio.run(create_mcp_server().list_tools())
    assert [t.name for t in tools] == [
        MCP_TOOL_DISCOVER_DELPI_INFORMATION,
        MCP_TOOL_EXECUTE_DELPI_INFORMATION,
    ]


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("CPV suprimentos", "get_supplies_cpv"),
        ("giro de estoque", "get_supplies_inventory_turnover"),
        ("valor de estoque", "get_supplies_stock_value"),
        ("economia de negociação", "get_supplies_negotiation_savings_summary"),
        ("OTD suprimentos", "get_supplies_otd"),
        ("OTD de compras", "get_supplies_purchase_order_otd"),
        ("OTD pedidos de compra", "get_supplies_purchase_order_otd"),
        ("OTD fornecedor", "get_supplies_purchase_order_otd"),
        ("série OTD compras", "get_supplies_purchase_order_otd_series"),
        ("evolução OTD de compras", "get_supplies_purchase_order_otd_series"),
        ("estoque de segurança", "get_supplies_safety_stock_summary"),
        ("itens de estoque de segurança", "get_supplies_safety_stock_items"),
        ("análise de consumo estoque de segurança", "get_supplies_safety_stock_consumption_analysis_summary"),
        ("saldo de estoque por depósito", "get_supplies_stock_balances_summary"),
        ("resumo dos saldos de estoque por depósito", "get_supplies_stock_balances_summary"),
        ("solicitações de compra", "list_supplies_purchase_request_lines"),
        ("materiais em poder de terceiros", "get_supplies_third_party_materials_summary"),
        ("histórico de preço por fornecedor", "get_supplies_safety_stock_supplier_purchase_price_history"),
        ("fornecedores do item de estoque de segurança", "get_supplies_safety_stock_item_suppliers"),
    ],
)
def test_wave005_supplies_retrieval_positive(query, expected, monkeypatch):
    set_actions_for_tests(_actions())
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "sec",
    )
    discovered = discover_delpi_information(query=query, top_k=5, actor_id="u1")
    assert discovered["eligible_action_count"] >= 53, query
    assert discovered["candidate_count"] >= 1, query
    assert discovered["candidates"][0]["action_id"] == expected, (
        query,
        [c["action_id"] for c in discovered["candidates"]],
    )


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("resumo dos saldos de estoque por depósito", "get_supplies_stock_balances_summary"),
        ("resumo de estoque por depósito", "get_supplies_stock_balances_summary"),
        ("consolidado de estoque por depósito", "get_supplies_stock_balances_summary"),
        ("totais dos saldos por armazém", "get_supplies_stock_balances_summary"),
        ("qual o valor total de estoque por depósito", "get_supplies_stock_balances_summary"),
        ("liste os produtos em estoque por depósito", "get_supplies_stock_balances_items"),
        ("quais itens existem no depósito 01", "get_supplies_stock_balances_items"),
        ("itens de saldo de estoque", "get_supplies_stock_balances_items"),
        ("lista de produtos por armazém", "get_supplies_stock_balances_items"),
        ("mostrar itens dos saldos de estoque", "get_supplies_stock_balances_items"),
        ("estoque do produto 10080001", "get_product_stock"),
        ("saldo disponível do produto 10080001", "get_product_stock"),
        ("estoque do código 10090043", "get_product_stock"),
        ("saldo por filial do produto 10080055", "get_product_stock"),
    ],
)
def test_wave005_stock_balance_retrieval_disambiguation(query, expected, monkeypatch):
    """Summary vs items vs product-stock intents must rank without query hardcodes."""
    set_actions_for_tests(_actions())
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "sec",
    )
    discovered = discover_delpi_information(query=query, top_k=5, actor_id="u1")
    assert discovered["candidates"][0]["action_id"] == expected, (
        query,
        [c["action_id"] for c in discovered["candidates"]],
    )


@pytest.mark.parametrize(
    ("query", "expected", "forbidden"),
    [
        ("OTD comercial", "get_sales_order_otd", "get_supplies_purchase_order_otd"),
        ("OTD de compras", "get_supplies_purchase_order_otd", "get_sales_order_otd"),
        ("OTD fornecedor", "get_supplies_purchase_order_otd", "get_sales_order_otd"),
        ("resumo do ROL", "get_commercial_rol_summary", "get_supplies_cpv"),
        ("CPV suprimentos", "get_supplies_cpv", "get_commercial_rol_summary"),
        ("estoque do produto", "get_product_stock", "get_supplies_stock_balances_items"),
        ("saldo de estoque por depósito", "get_supplies_stock_balances_summary", "get_product_stock"),
        ("solicitações de compra", "list_supplies_purchase_request_lines", "get_product_purchases"),
        (
            "histórico de preço de compra do produto",
            "get_product_purchase_price_history",
            "get_supplies_safety_stock_supplier_purchase_price_history",
        ),
        (
            "histórico de preço por fornecedor",
            "get_supplies_safety_stock_supplier_purchase_price_history",
            "get_product_purchase_price_history",
        ),
        (
            "materiais em poder de terceiros",
            "get_supplies_third_party_materials_summary",
            "get_product_stock",
        ),
        ("estoque de segurança", "get_supplies_safety_stock_summary", "get_product_stock"),
    ],
)
def test_wave005_sibling_disambiguation(query, expected, forbidden, monkeypatch):
    set_actions_for_tests(_actions())
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "sec",
    )
    discovered = discover_delpi_information(query=query, top_k=5, actor_id="u1")
    ids = [c["action_id"] for c in discovered["candidates"]]
    assert ids, query
    assert ids[0] == expected, (query, ids)
    assert forbidden not in ids or ids.index(expected) < ids.index(forbidden), (query, ids)


@pytest.mark.parametrize(
    "query",
    [
        "crie uma solicitação de compra",
        "altere o estoque de segurança",
        "aprove pedido de compra",
        "cancele solicitação",
        "registre recebimento",
        "lançar título financeiro",
    ],
)
def test_wave005_negative_write_intent(query, monkeypatch):
    set_actions_for_tests(_actions())
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "sec",
    )
    discovered = discover_delpi_information(query=query, top_k=5, actor_id="u1")
    executable = [
        c for c in discovered.get("candidates") or [] if c.get("action_id") in _PROMOTED
    ]
    assert discovered["candidate_count"] == 0 or not executable, (
        query,
        [c["action_id"] for c in discovered.get("candidates") or []],
    )


def test_wave005_execute_projects_cpv(monkeypatch):
    set_actions_for_tests(_actions())
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.execute_service.candidate_token_secret",
        lambda: "sec",
    )
    action = _action("get_supplies_cpv")
    token = mint_candidate_token(
        action_id=action.action_id,
        actor_id="u1",
        secret="sec",
        ttl_seconds=300,
    )

    class _Exec:
        def execute(self, *, action_id: str, validated_arguments: dict[str, Any]):
            assert action_id == "get_supplies_cpv"
            return CatalogActionExecutionResult(
                outcome="ok",
                payload={
                    "success": True,
                    "data": {
                        "branch": "01",
                        "start_date": "2026-09-01",
                        "end_date": "2026-09-30",
                        "summary": {
                            "cpv_total": 100.0,
                            "rol": 200.0,
                            "cpv_percentage": 50.0,
                            "secret_cost_breakdown": 99.0,
                        },
                        "internal_sql": "SELECT 1",
                    },
                },
            )

    result = execute_delpi_information(
        candidate_token=token,
        arguments={"branch": "01", "start_date": "2026-09-01", "end_date": "2026-09-30"},
        actor_id="u1",
        catalog_action_executor=_Exec(),
    )
    assert result["status"] == "ok"
    assert result["projection"] == "approved_fields"
    body = result["data"]
    assert body["summary"]["cpv_total"] == 100.0
    assert "secret_cost_breakdown" not in body.get("summary", {})
    assert "internal_sql" not in body


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


def test_wave005_commercial_regression_still_discoverable(monkeypatch):
    set_actions_for_tests(_actions())
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "sec",
    )
    discovered = discover_delpi_information(query="OTD comercial", top_k=5, actor_id="u1")
    assert discovered["candidates"][0]["action_id"] == "get_sales_order_otd"
    discovered = discover_delpi_information(query="ROL comercial", top_k=5, actor_id="u1")
    assert discovered["candidates"][0]["action_id"] == "get_commercial_rol_summary"


def test_wave005_agent_intelligence_unchanged():
    intel = json.loads(
        (_API_ROOT / "app/content/davi_agent_intelligence.json").read_text(encoding="utf-8")
    )
    assert intel.get("version") == "2026.09.24.3"
    blob = json.dumps(intel)
    for oid in _PROMOTED:
        assert oid not in blob
