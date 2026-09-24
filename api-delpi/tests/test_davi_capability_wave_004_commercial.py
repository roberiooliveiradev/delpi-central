"""DAVI Wave 004 — Commercial Analytics governed READ promotion."""

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
_DEFERRED = ("get_sales_order_otd_panel",)
_OUT_OF_WAVE = (
    "get_commercial_proposal_history_events",
    "list_commercial_proposals",
    "get_commercial_proposal",
    "summarize_commercial_proposals_by_collaborator",
    "get_sales_order_otd_line_detail",
)
_PRIOR_SEVENTEEN = (
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


def test_wave004_allowlist_version_and_eligible_count():
    allow = load_external_read_allowlist()
    assert allow.get("version") == 10
    eligible = {a.operation_id for a in _actions() if a.executable}
    assert len(eligible) == 35
    assert set(_PRIOR_SEVENTEEN) <= eligible
    assert set(_PROMOTED) <= eligible
    for oid in (*_DEFERRED, *_OUT_OF_WAVE):
        assert oid not in eligible


@pytest.mark.parametrize("oid", _PROMOTED)
def test_wave004_promoted_contract_matrix(oid: str):
    action = _action(oid)
    entry = _allowlist_entry(oid)
    assert action.method.upper() == "GET"
    assert action.executable is True
    fields_in = list(entry.get("approvedInputFields") or [])
    fields_out = list(entry.get("approvedResponseFields") or [])
    assert fields_in
    assert fields_out
    assert all("*" not in f for f in fields_out)
    assert all("/" not in f for f in fields_in)  # no path/url args
    param_names = {p["name"] for p in (action.parameters or ()) if isinstance(p, dict)}
    for name in fields_in:
        assert name in param_names or name in action.path, (oid, name)
    assert "url" not in fields_in
    assert "operationId" not in fields_in
    assert "sql" not in fields_in


@pytest.mark.parametrize("oid", (*_DEFERRED, *_OUT_OF_WAVE))
def test_wave004_deferred_and_out_of_wave_not_executable(oid: str):
    action = _action(oid)
    assert action.executable is False


def test_wave004_mcp_tools_remain_three():
    import asyncio

    from app.interface.mcp.server import create_mcp_server

    tools = asyncio.run(create_mcp_server().list_tools())
    assert [t.name for t in tools] == [
        MCP_TOOL_SEARCH_PRODUCTS,
        MCP_TOOL_DISCOVER_DELPI_INFORMATION,
        MCP_TOOL_EXECUTE_DELPI_INFORMATION,
    ]


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("ROL comercial", "get_commercial_rol_summary"),
        ("resumo do ROL", "get_commercial_rol_summary"),
        ("evolução mensal do ROL", "get_commercial_rol_series"),
        ("série de ROL", "get_commercial_rol_series"),
        ("ROL por cliente", "get_commercial_rol_by_customer"),
        ("ROL por produto", "get_commercial_rol_by_product"),
        ("ROL por filial", "get_commercial_rol_by_branch"),
        ("resumo OTD", "get_sales_order_otd_summary"),
        ("OTD comercial", "get_sales_order_otd"),
        ("evolução do OTD", "get_sales_order_otd_series"),
        ("OTD por semana", "get_sales_order_otd_series"),
        ("OTD por cliente", "get_sales_order_otd_by_customer"),
        ("OTD por filial", "get_sales_order_otd_by_branch"),
        ("taxa de conversão", "get_sales_conversion_rate"),
        ("evolução da conversão", "get_sales_conversion_rate_series"),
        ("média de novos clientes", "get_new_clients_average"),
        ("ROL de clientes novos", "get_new_clients_rol_pct"),
        ("participação de novos negócios", "get_new_business_rol_pct"),
        ("meta de novos negócios", "get_new_business_rol_target_pct"),
        ("meta ROL WEG", "get_weg_rol_target_pct"),
    ],
)
def test_wave004_commercial_retrieval_positive(query, expected, monkeypatch):
    set_actions_for_tests(_actions())
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "sec",
    )
    discovered = discover_delpi_information(query=query, top_k=5, actor_id="u1")
    assert discovered["eligible_action_count"] == 35, query
    assert discovered["candidate_count"] >= 1, query
    assert discovered["candidates"][0]["action_id"] == expected, (
        query,
        [c["action_id"] for c in discovered["candidates"]],
    )


@pytest.mark.parametrize(
    ("query", "expected", "forbidden"),
    [
        ("ROL comercial", "get_commercial_rol_summary", "get_sales_order_otd_summary"),
        ("resumo OTD", "get_sales_order_otd_summary", "get_commercial_rol_summary"),
        ("evolução do ROL", "get_commercial_rol_series", "get_sales_order_otd_series"),
        ("evolução do OTD", "get_sales_order_otd_series", "get_commercial_rol_series"),
        ("ROL por cliente", "get_commercial_rol_by_customer", "get_sales_order_otd_by_customer"),
        ("OTD por cliente", "get_sales_order_otd_by_customer", "get_commercial_rol_by_customer"),
        ("OTD por filial", "get_sales_order_otd_by_branch", "get_commercial_rol_by_branch"),
        ("média de novos clientes", "get_new_clients_average", "get_new_business_rol_pct"),
        ("participação de novos negócios", "get_new_business_rol_pct", "get_new_clients_rol_pct"),
        ("ROL de clientes novos", "get_new_clients_rol_pct", "get_new_business_rol_pct"),
        ("resumo do ROL", "get_commercial_rol_summary", "get_sales_order_otd_panel"),
    ],
)
def test_wave004_sibling_disambiguation(query, expected, forbidden, monkeypatch):
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
        "lançar título financeiro",
        "alterar proposta comercial",
        "rodar SQL comercial",
        "criar pedido de venda",
        "excluir proposta",
        "can you update commercial proposal",
    ],
)
def test_wave004_negative_write_and_unrelated(query, monkeypatch):
    set_actions_for_tests(_actions())
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "sec",
    )
    discovered = discover_delpi_information(query=query, top_k=5, actor_id="u1")
    executable = [
        c for c in discovered.get("candidates") or [] if c.get("action_id") in _PROMOTED
    ]
    # write-intent guard → zero candidates; unrelated finance write verbs also empty
    assert discovered["candidate_count"] == 0 or not executable, (
        query,
        [c["action_id"] for c in discovered.get("candidates") or []],
    )

def test_wave004_execute_projects_rol_summary(monkeypatch):
    set_actions_for_tests(_actions())
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.execute_service.candidate_token_secret",
        lambda: "sec",
    )
    action = _action("get_commercial_rol_summary")
    token = mint_candidate_token(
        action_id=action.action_id,
        actor_id="u1",
        secret="sec",
        ttl_seconds=300,
    )

    class _Exec:
        def execute(self, *, action_id: str, validated_arguments: dict[str, Any]):
            assert action_id == "get_commercial_rol_summary"
            return CatalogActionExecutionResult(
                outcome="ok",
                payload={
                    "success": True,
                    "data": {
                        "branch": "01",
                        "start_date": "2026-09-01",
                        "end_date": "2026-09-30",
                        "rol": 1000.0,
                        "gross_revenue": 1200.0,
                        "returns": 100.0,
                        "discounts": 100.0,
                        "secret_margin": 99.0,
                        "goal_value": 2000.0,
                        "rol_target_pct": 50.0,
                        "has_goal": True,
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
    assert body.get("rol") == 1000.0
    assert "secret_margin" not in body
    assert body.get("gross_revenue") == 1200.0


def test_wave004_customer_ranking_drops_identifiers():
    raw = {
        "branch": "all",
        "start_date": "2026-09-01",
        "end_date": "2026-09-30",
        "items": [
            {
                "customer_code": "0001",
                "customer_store": "01",
                "customer_name": "ACME",
                "cnpj": "12.345.678/0001-99",
                "city": "Joinville",
                "state": "SC",
                "customer_center": "1320",
                "rol": 10.0,
                "gross_revenue": 12.0,
                "share_pct": 50.0,
                "rank": 1,
            }
        ],
        "others": None,
        "summary": {"total_rol": 10.0, "customers_count": 1, "items_count": 1},
    }
    fields = tuple(_allowlist_entry("get_commercial_rol_by_customer")["approvedResponseFields"])
    projected = apply_approved_field_projection(raw, approved_fields=fields)
    assert projected["items"][0]["customer_code"] == "0001"
    assert "cnpj" not in projected["items"][0]
    assert "city" not in projected["items"][0]
    assert "state" not in projected["items"][0]


def test_wave004_nested_pagination_partial():
    payload = {
        "items": [{"customer_code": "1"}],
        "pagination": {"page": 1, "page_size": 50, "total": 120, "has_more": True},
    }
    assert classify_source_pagination(payload) == "partial"


def test_wave004_drawing_pdf_still_not_executable():
    assert _action("get_product_drawing_pdf").executable is False


def test_wave004_agent_intelligence_unchanged():
    intel = json.loads(
        (_API_ROOT / "app/content/davi_agent_intelligence.json").read_text(encoding="utf-8")
    )
    assert intel.get("version") == "2026.09.24.2"
    blob = json.dumps(intel)
    for oid in _PROMOTED:
        assert oid not in blob
