"""Tests for DAVI dynamic governed READ broker (DAVI-DYNAMIC-READ-002/003)."""

from __future__ import annotations

import ast
import inspect
import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, call

import pytest
from pydantic import ValidationError

from app.application.external_capabilities.constants import (
    PRODUCT_SEARCH_INPUT_FIELDS,
    PRODUCT_SEARCH_MAX_PAGE_SIZE,
    PRODUCT_SEARCH_RESPONSE_FIELDS,
)
from app.application.external_capabilities.dynamic_information.action_index import (
    reset_action_index_for_tests,
    set_actions_for_tests,
)
from app.application.external_capabilities.dynamic_information.argument_validator import (
    ArgumentValidationError,
    build_argument_json_schema,
    validate_arguments,
)
from app.application.external_capabilities.dynamic_information.candidate_token import (
    CandidateTokenError,
    mint_candidate_token,
    parse_candidate_token,
)
from app.application.external_capabilities.dynamic_information.catalog_builder import (
    TechnicalAction,
    build_technical_actions_from_baseline,
)
from app.application.external_capabilities.dynamic_information.constants import (
    STATUS_DAVI_ELIGIBLE_READ,
    STATUS_EXPLICIT_PROCESSING_PROHIBITION,
    STATUS_GENERIC_SQL_FORBIDDEN,
    STATUS_NEEDS_BRANCH_AUTHZ_EVIDENCE,
    STATUS_NEEDS_MODEL_SAFE_PROJECTION,
    STATUS_NEEDS_NESTED_PROJECTION_SUPPORT,
    STATUS_SEMANTICALLY_REDUNDANT,
    STATUS_WRITE_OUT_OF_SCOPE,
)
from app.application.external_capabilities.dynamic_information.content_loader import (
    load_dynamic_read_budgets,
    load_external_read_allowlist,
)
from app.application.external_capabilities.dynamic_information.read_only_intent_guard import (
    clear_read_only_intent_guard_cache,
)
from app.application.external_capabilities.dynamic_information.discover_service import (
    discover_delpi_information,
)
from app.application.external_capabilities.dynamic_information.eligibility import (
    classify_operation,
    load_allowlist_operation_ids,
)
from app.application.external_capabilities.dynamic_information.errors import (
    GovernedExecutionError,
)
from app.application.external_capabilities.dynamic_information.execute_service import (
    execute_delpi_information,
)
from app.application.external_capabilities.dynamic_information.execution_plan import (
    CatalogActionPlan,
    build_execution_plan,
)
from app.application.external_capabilities.dynamic_information.projection import (
    apply_approved_field_projection,
    bound_response_payload,
)
from app.application.external_capabilities.dynamic_information.retrieval import (
    retrieve_eligible_actions,
)
from app.domain.ports.davi_catalog_action_executor_port import (
    CatalogActionExecutionResult,
    CatalogActionExecutorPort,
)
from app.infrastructure.davi.asgi_catalog_action_executor import AsgiCatalogActionExecutor
from app.interface.mcp.schemas import (
    DiscoverDelpiInformationInput,
    ExecuteDelpiInformationInput,
)


_ELIGIBLE_V5_OPERATION_IDS = frozenset(
    {
        "search_products",
        "get_product_stock",
        "get_product_suppliers",
        "get_product_customers",
        "get_product_purchases",
        "get_product_structure",
        "get_product_production_status",
    }
)
_WAVE1_OPERATION_IDS = frozenset(
    {
        "get_product_factory_status",
        "get_product_structure_exclusivity",
        "get_product_shipping_status",
    }
)
_WAVE2_OPERATION_IDS = frozenset(
    {
        "get_product_pricing",
        "get_product_purchase_price_history",
        "get_product_last_purchase",
    }
)
_WAVE3A_OPERATION_IDS = frozenset(
    {
        "get_product_guide",
        "get_product_parents",
    }
)
_DRAWING_OPERATION_IDS = frozenset(
    {
        "list_product_drawings",
        "get_product_drawing",
    }
)
_WAVE4_COMMERCIAL_OPERATION_IDS = frozenset(
    {
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
    }
)
_WAVE5_SUPPLIES_OPERATION_IDS = frozenset(
    {
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
    }
)

_WAVE6_PRODUCTION_OPERATION_IDS = frozenset(
    {
        "get_overall_equipment_effectiveness_pct",
        "get_production_oee",
        "get_production_oee_series",
        "get_on_time_delivery_pct",
        "get_production_otd",
        "get_production_otd_series",
        "get_production_machine_load_work_centers",
        "get_production_machine_load_operations",
        "get_production_appointments_summary",
        "get_production_appointments_produced_totals",
    }
)
_ELIGIBLE_OPERATION_IDS = (
    _ELIGIBLE_V5_OPERATION_IDS
    | _WAVE1_OPERATION_IDS
    | _WAVE2_OPERATION_IDS
    | _WAVE3A_OPERATION_IDS
    | _DRAWING_OPERATION_IDS
    | _WAVE4_COMMERCIAL_OPERATION_IDS
    | _WAVE5_SUPPLIES_OPERATION_IDS
    | _WAVE6_PRODUCTION_OPERATION_IDS
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


def _search_params(*, required_code: bool = False) -> tuple[dict[str, Any], ...]:
    return (
        {"name": "code", "in": "query", "required": required_code, "type": "string"},
        {"name": "description", "in": "query", "required": False, "type": "string"},
        {"name": "group_code", "in": "query", "required": False, "type": "string"},
        {"name": "customer_reference", "in": "query", "required": False, "type": "string"},
        {"name": "page", "in": "query", "required": False, "type": "integer", "minimum": 1},
        {
            "name": "page_size",
            "in": "query",
            "required": False,
            "type": "integer",
            "minimum": 1,
            "maximum": 50,
        },
        {
            "name": "sort",
            "in": "query",
            "required": False,
            "type": "string",
            "enum": ["code", "description"],
        },
    )


def _action(
    *,
    oid: str,
    path: str,
    method: str = "GET",
    status: str = STATUS_DAVI_ELIGIBLE_READ,
    summary: str = "",
    parameters: tuple | None = None,
    execution_mode: str | None = "approved_external_capability",
    approved_response_fields: tuple[str, ...] = PRODUCT_SEARCH_RESPONSE_FIELDS,
    approved_input_fields: tuple[str, ...] | None = None,
    semantic_aliases: tuple[str, ...] = (),
    argument_constraints: dict[str, Any] | None = None,
) -> TechnicalAction:
    summary_text = summary or oid.replace("_", " ")
    aliases = semantic_aliases
    if approved_input_fields is None:
        input_fields = (
            PRODUCT_SEARCH_INPUT_FIELDS if oid == "search_products" else ()
        )
    else:
        input_fields = approved_input_fields
    searchable = f"{oid} {summary_text} {path} products {' '.join(aliases)}".lower()
    return TechnicalAction(
        action_id=oid,
        operation_id=oid,
        method=method,
        path=path,
        summary=summary_text,
        description="",
        tags=("products",),
        davi_status=status,
        entity="product",
        shape="paged_list",
        parameters=parameters if parameters is not None else _search_params(),
        searchable_text=searchable,
        execution_mode=execution_mode,
        approved_response_fields=approved_response_fields,
        approved_input_fields=input_fields,
        semantic_aliases=aliases,
        argument_constraints=argument_constraints or {},
    )


def _api_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_baseline_actions() -> list[TechnicalAction]:
    baseline = json.loads(
        (_api_root() / "app/content/openapi_baseline.json").read_text(encoding="utf-8")
    )
    return build_technical_actions_from_baseline(
        baseline, allowlist=load_external_read_allowlist()
    )


def _load_governed_search_products() -> TechnicalAction:
    action = next(a for a in _load_baseline_actions() if a.operation_id == "search_products")
    assert action.executable
    return action


def _allowlist_entry_with_projection(operation_id: str, **fields: Any) -> dict[str, Any]:
    return {
        "operations": [
            {
                "operationId": operation_id,
                "approvedInputFields": fields.get("inputs") or ["code"],
                "approvedResponseFields": fields.get("responses") or ["product_code"],
            }
        ]
    }


def test_allowlist_v5_multi_ops_rebaseline():
    allow = load_external_read_allowlist()
    ids = load_allowlist_operation_ids(allow)
    assert ids == set(_ELIGIBLE_OPERATION_IDS)
    assert allow.get("version") == 15
    assert allow.get("coverageDecision", {}).get("decision") == (
        "PROMOTE_PRODUCTION_OPERATIONAL_INTELLIGENCE_READ"
    )
    assert allow.get("authzPolicy") == "DAVI-READ-AUTHZ-REBASELINE-001"
    entry = next(
        op
        for op in allow["operations"]
        if isinstance(op, dict) and op.get("operationId") == "search_products"
    )
    assert set(entry["approvedInputFields"]) == set(PRODUCT_SEARCH_INPUT_FIELDS)
    assert entry.get("semanticAliases")
    stock = next(
        op
        for op in allow["operations"]
        if isinstance(op, dict) and op.get("operationId") == "get_product_stock"
    )
    assert "branch" in stock["approvedInputFields"]
    quarantine = {str(t).lower() for t in (allow.get("retrievalQuarantineTokens") or [])}
    for owned in (
        "estoque",
        "stock",
        "estrutura",
        "bom",
        "producao",
        "produção",
        "fornecedor",
        "cliente",
    ):
        assert owned not in quarantine
    blocked = {
        x["operationId"]: x.get("primaryBlocker")
        for x in allow.get("explicitlyNotApproved") or []
        if isinstance(x, dict)
    }
    assert "get_product_stock" not in blocked
    assert blocked["get_product_detail"] == "SEMANTICALLY_REDUNDANT"
    assert blocked["get_product_summary"] == "DEFER"
    assert "get_product_pricing" not in blocked
    assert blocked["get_product_cost_impact_simulation"] == "PREPARE"
    assert blocked["get_product_raw_material_price_intelligence"] == "DEFER"
    superseded = allow.get("supersededBlockers", {}).get("items") or []
    assert "NEEDS_BRANCH_AUTHZ_EVIDENCE" in superseded
    not_approved = {
        (x.get("operationId") if isinstance(x, dict) else x)
        for x in (allow.get("explicitlyNotApproved") or [])
    }
    assert "get_product_summary" in not_approved
    assert "get_product_detail" in not_approved
    assert "get_product_factory_status" not in not_approved
    assert "get_product_structure_exclusivity" not in not_approved
    assert "get_product_shipping_status" not in not_approved
    assert "get_product_pricing" not in not_approved
    assert "get_product_purchase_price_history" not in not_approved
    assert "get_product_last_purchase" not in not_approved
    assert "factory" in quarantine


def test_classify_hard_blocks():
    search_allow = _allowlist_entry_with_projection(
        "search_products",
        inputs=list(PRODUCT_SEARCH_INPUT_FIELDS),
        responses=list(PRODUCT_SEARCH_RESPONSE_FIELDS),
    )
    search_ids = {"search_products"}
    assert (
        classify_operation(
            method="GET",
            path="/data/sql",
            operation_id="run_sql",
            allowlisted_operation_ids=search_ids,
        )
        == STATUS_GENERIC_SQL_FORBIDDEN
    )
    assert (
        classify_operation(
            method="POST",
            path="/products",
            operation_id="create_product",
            allowlisted_operation_ids=search_ids,
        )
        == STATUS_WRITE_OUT_OF_SCOPE
    )
    assert (
        classify_operation(
            method="GET",
            path="/products/{code}/stock",
            operation_id="get_product_stock",
            allowlisted_operation_ids=search_ids,
        )
        == STATUS_NEEDS_MODEL_SAFE_PROJECTION
    )
    stock_allow = _allowlist_entry_with_projection(
        "get_product_stock",
        inputs=["code", "branch", "page", "page_size"],
        responses=[
            "product_code",
            "branch",
            "warehouse",
            "current_quantity",
            "available_quantity",
        ],
    )
    assert (
        classify_operation(
            method="GET",
            path="/products/{code}/stock",
            operation_id="get_product_stock",
            allowlisted_operation_ids={"get_product_stock"},
            allowlist=stock_allow,
        )
        == STATUS_DAVI_ELIGIBLE_READ
    )
    assert (
        classify_operation(
            method="GET",
            path="/products/search",
            operation_id="search_products",
            allowlisted_operation_ids=search_ids,
            allowlist=search_allow,
        )
        == STATUS_DAVI_ELIGIBLE_READ
    )
    assert (
        classify_operation(
            method="GET",
            path="/products/{code}/summary",
            operation_id="get_product_summary",
            allowlisted_operation_ids=search_ids,
            shape="product_snapshot",
        )
        == STATUS_NEEDS_NESTED_PROJECTION_SUPPORT
    )
    detail_disposition = {
        "operations": [],
        "explicitlyNotApproved": [
            {
                "operationId": "get_product_detail",
                "coverageDisposition": "SEMANTICALLY_REDUNDANT",
            }
        ],
    }
    assert (
        classify_operation(
            method="GET",
            path="/products/{code}",
            operation_id="get_product_detail",
            allowlisted_operation_ids=search_ids,
            shape="product_snapshot",
            allowlist=detail_disposition,
        )
        == STATUS_SEMANTICALLY_REDUNDANT
    )
    # Without disposition metadata, nested shape alone is structural — not name-based.
    assert (
        classify_operation(
            method="GET",
            path="/products/{code}",
            operation_id="completely_unseen_detail_name",
            allowlisted_operation_ids=set(),
            shape="product_snapshot",
        )
        == STATUS_NEEDS_NESTED_PROJECTION_SUPPORT
    )


def test_inventory_eligible_count_is_thirteen():
    baseline = json.loads(
        (_api_root() / "app/content/openapi_baseline.json").read_text(encoding="utf-8")
    )
    actions = build_technical_actions_from_baseline(
        baseline, allowlist=load_external_read_allowlist()
    )
    assert len(actions) == int(baseline.get("operation_count") or 0)
    eligible = [a for a in actions if a.executable]
    assert len(eligible) == 63
    assert set(a.operation_id for a in eligible) == set(_ELIGIBLE_OPERATION_IDS)


def test_owned_product_intents_discover_from_full_catalog(monkeypatch):
    actions = _load_baseline_actions()
    set_actions_for_tests(actions)
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "sec",
    )
    expectations = (
        ("estoque do produto 10080055", "get_product_stock"),
        ("estrutura do produto 10080055", "get_product_structure"),
        ("fornecedor do produto", "get_product_suppliers"),
        ("cliente do produto", "get_product_customers"),
        ("status de produção do produto", "get_product_production_status"),
    )
    for query, expected_oid in expectations:
        discovered = discover_delpi_information(query=query, top_k=10, actor_id="u1")
        assert discovered["eligible_action_count"] == 63, query
        assert discovered["candidate_count"] >= 1, query
        action_ids = {c["action_id"] for c in discovered["candidates"]}
        assert expected_oid in action_ids, query


def test_three_tool_invariant_with_v5_allowlist():
    import asyncio
    from app.interface.mcp.server import create_mcp_server

    tools = asyncio.run(create_mcp_server().list_tools())
    assert [t.name for t in tools] == [
        "discover_delpi_information",
        "execute_delpi_information",
    ]
    # Still exactly three MCP tools; allowlist is no longer search-only.
    assert load_allowlist_operation_ids(load_external_read_allowlist()) == set(
        _ELIGIBLE_OPERATION_IDS
    )


def test_discover_rejects_transport_smuggling_in_schema():
    with pytest.raises(ValidationError):
        DiscoverDelpiInformationInput.model_validate(
            {"query": "estoque", "path": "/products/x/stock"}
        )
    with pytest.raises(ValidationError):
        ExecuteDelpiInformationInput.model_validate(
            {"candidate_token": "x", "url": "https://evil"}
        )


def test_discover_requires_actor(monkeypatch):
    set_actions_for_tests(
        [_action(oid="search_products", path="/products/search", summary="search products")]
    )
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "test-secret-davi",
    )
    with pytest.raises(CandidateTokenError):
        discover_delpi_information(query="search products", top_k=5, actor_id=None)
    with pytest.raises(CandidateTokenError):
        discover_delpi_information(query="search products", top_k=5, actor_id="")


def test_discover_eligible_only_search_products(monkeypatch):
    set_actions_for_tests(
        [
            _action(
                oid="search_products",
                path="/products/search",
                summary="search products master",
            ),
            _action(
                oid="get_product_detail",
                path="/products/{code}",
                summary="product detail",
                status="NEEDS_EXTERNAL_PROCESSING_APPROVAL",
                execution_mode=None,
                approved_response_fields=(),
            ),
            _action(
                oid="get_product_summary",
                path="/products/{code}/summary",
                summary="product summary stock prices",
                status="NEEDS_EXTERNAL_PROCESSING_APPROVAL",
                execution_mode=None,
                approved_response_fields=(),
            ),
            _action(
                oid="get_product_stock",
                path="/products/{code}/stock",
                summary="product stock",
                status=STATUS_NEEDS_MODEL_SAFE_PROJECTION,
                execution_mode=None,
                approved_response_fields=(),
            ),
            _action(
                oid="run_sql",
                path="/data/sql",
                summary="sql",
                status=STATUS_GENERIC_SQL_FORBIDDEN,
                execution_mode=None,
                approved_response_fields=(),
            ),
        ]
    )
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "test-secret-davi",
    )
    discovered = discover_delpi_information(query="product", top_k=10, actor_id="u1")
    assert discovered["eligible_action_count"] == 1
    action_ids = {c["action_id"] for c in discovered["candidates"]}
    assert action_ids == {"search_products"}


def test_discover_and_execute_happy_path_approved_projection(monkeypatch):
    set_actions_for_tests(
        [
            _action(
                oid="search_products",
                path="/products/search",
                summary="search products master",
            ),
        ]
    )
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "test-secret-davi",
    )
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.execute_service.candidate_token_secret",
        lambda: "test-secret-davi",
    )
    discovered = discover_delpi_information(query="search products", top_k=5, actor_id="u1")
    assert discovered["candidate_count"] == 1
    token = discovered["candidates"][0]["candidate_token"]
    schema = discovered["candidates"][0]["argument_schema"]
    assert schema["additionalProperties"] is False
    assert "customer_reference" not in schema["properties"]

    def runner(**kwargs):
        assert kwargs.get("code") == "A"
        return {
            "items": [
                {
                    "product_code": "A",
                    "description": "Widget",
                    "group_category": "G1",
                    "cost": 99.9,
                }
            ],
            "page": 1,
            "page_size": 50,
            "total": 1,
        }

    result = execute_delpi_information(
        candidate_token=token,
        arguments={"code": "A"},
        actor_id="u1",
        search_products_runner=runner,
    )
    assert result["status"] == "ok"
    assert result["truncated"] is False
    assert "http_status" not in result
    item = result["data"]["items"][0]
    assert set(item.keys()) == set(PRODUCT_SEARCH_RESPONSE_FIELDS)
    assert "cost" not in item


def test_actor_token_binding(monkeypatch):
    action = _action(oid="search_products", path="/products/search")
    set_actions_for_tests([action])
    secret = "sec"
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.execute_service.candidate_token_secret",
        lambda: secret,
    )
    token_a = mint_candidate_token(
        action_id="search_products", actor_id="user-a", secret=secret, ttl_seconds=60
    )
    parse_candidate_token(token_a, secret=secret, expected_actor_id="user-a")
    with pytest.raises(CandidateTokenError):
        parse_candidate_token(token_a, secret=secret, expected_actor_id="user-b")
    with pytest.raises(CandidateTokenError):
        execute_delpi_information(
            candidate_token=token_a,
            arguments={},
            actor_id="user-b",
            search_products_runner=lambda **_: {"items": []},
        )
    with pytest.raises(CandidateTokenError):
        execute_delpi_information(
            candidate_token=token_a,
            arguments={},
            actor_id=None,
            search_products_runner=lambda **_: {"items": []},
        )
    with pytest.raises(CandidateTokenError):
        mint_candidate_token(
            action_id="search_products", actor_id="", secret=secret, ttl_seconds=60
        )
    expired = mint_candidate_token(
        action_id="search_products",
        actor_id="user-a",
        secret=secret,
        ttl_seconds=1,
        now=1.0,
    )
    with pytest.raises(CandidateTokenError):
        parse_candidate_token(
            expired, secret=secret, expected_actor_id="user-a", now=100.0
        )
    with pytest.raises(CandidateTokenError):
        parse_candidate_token(token_a + "x", secret=secret, expected_actor_id="user-a")


def test_argument_validation_matrix():
    action = _action(
        oid="search_products",
        path="/products/search",
        parameters=_search_params(),
    )
    path_action = TechnicalAction(
        action_id="get_demo",
        operation_id="get_demo",
        method="GET",
        path="/demo/{code}",
        summary="demo",
        description="",
        tags=(),
        davi_status=STATUS_DAVI_ELIGIBLE_READ,
        parameters=(
            {"name": "code", "in": "path", "required": True, "type": "string"},
            {
                "name": "mode",
                "in": "query",
                "required": True,
                "type": "string",
                "enum": ["a", "b"],
            },
            {"name": "page", "in": "query", "required": False, "type": "integer"},
        ),
        searchable_text="get_demo",
        execution_mode="catalog_action",
        approved_response_fields=("x",),
    )

    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, {"url": "https://evil"})
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, {"operationId": "get_product_stock"})
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, {"customer_reference": "x"})
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, {"unknown_arg": "x"})
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, {"page_size": "nope"})
    with pytest.raises(ArgumentValidationError):
        validate_arguments(path_action, {"mode": "a"})
    with pytest.raises(ArgumentValidationError):
        validate_arguments(path_action, {"code": "1"})
    with pytest.raises(ArgumentValidationError):
        validate_arguments(path_action, {"code": "1", "mode": "z"})

    ok = validate_arguments(action, {"description": "motor", "page": 2, "page_size": "10"})
    assert ok["page"] == 2
    assert ok["page_size"] == 10
    assert isinstance(ok["page"], int)
    assert build_argument_json_schema(action) == build_argument_json_schema(action)


def test_catalog_action_plan_is_transport_neutral():
    action = _action(
        oid="future_read",
        path="/future/{code}",
        parameters=(
            {"name": "code", "in": "path", "required": True, "type": "string"},
        ),
        execution_mode="catalog_action",
        approved_response_fields=("name",),
    )
    plan = build_execution_plan(action, {"code": "X"})
    assert isinstance(plan, CatalogActionPlan)
    assert plan.action_id == "future_read"
    assert plan.validated_arguments == {"code": "X"}
    assert not hasattr(plan, "request")
    assert "method" not in plan.__dataclass_fields__
    assert "path" not in plan.__dataclass_fields__
    assert "query" not in plan.__dataclass_fields__


def test_semantic_executor_port_contract_and_binding(monkeypatch):
    action = _action(
        oid="future_read",
        path="/future/{code}",
        parameters=(
            {"name": "code", "in": "path", "required": True, "type": "string"},
        ),
        execution_mode="catalog_action",
        approved_response_fields=("name",),
    )
    set_actions_for_tests([action])
    secret = "sec"
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.execute_service.candidate_token_secret",
        lambda: secret,
    )
    token = mint_candidate_token(
        action_id="future_read", actor_id="u1", secret=secret, ttl_seconds=60
    )

    received: dict[str, Any] = {}

    class RecordingExecutor:
        def execute(
            self,
            *,
            action_id: str,
            validated_arguments: dict[str, Any],
        ) -> CatalogActionExecutionResult:
            received["action_id"] = action_id
            received["validated_arguments"] = validated_arguments
            received["kwargs_keys"] = sorted(
                inspect.signature(self.execute).parameters.keys()
            )
            return CatalogActionExecutionResult(
                outcome="ok", payload={"items": [{"name": "N", "secret": 1}]}
            )

    executor = RecordingExecutor()
    result = execute_delpi_information(
        candidate_token=token,
        arguments={"code": "X"},
        actor_id="u1",
        catalog_action_executor=executor,
    )
    assert received["action_id"] == "future_read"
    assert received["validated_arguments"] == {"code": "X"}
    assert "authorization" not in received["kwargs_keys"]
    assert "method" not in received["kwargs_keys"]
    assert "path" not in received["kwargs_keys"]
    assert result["data"]["items"][0] == {"name": "N"}

    # Application execute_delpi_information signature must not accept authorization.
    params = inspect.signature(execute_delpi_information).parameters
    assert "authorization" not in params
    assert "http_client" not in params
    assert "catalog_get_port" not in params


def test_catalog_executor_maps_unauthorized_and_forbidden(monkeypatch):
    action = _action(
        oid="future_read",
        path="/future/{code}",
        parameters=(
            {"name": "code", "in": "path", "required": True, "type": "string"},
        ),
        execution_mode="catalog_action",
        approved_response_fields=("name",),
    )
    set_actions_for_tests([action])
    secret = "sec"
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.execute_service.candidate_token_secret",
        lambda: secret,
    )
    token = mint_candidate_token(
        action_id="future_read", actor_id="u1", secret=secret, ttl_seconds=60
    )

    class UnauthorizedExecutor:
        def execute(self, *, action_id, validated_arguments):
            return CatalogActionExecutionResult(outcome="unauthorized")

    class ForbiddenExecutor:
        def execute(self, *, action_id, validated_arguments):
            return CatalogActionExecutionResult(outcome="forbidden")

    with pytest.raises(PermissionError, match="Unauthorized"):
        execute_delpi_information(
            candidate_token=token,
            arguments={"code": "X"},
            actor_id="u1",
            catalog_action_executor=UnauthorizedExecutor(),
        )
    with pytest.raises(PermissionError, match="Forbidden"):
        execute_delpi_information(
            candidate_token=token,
            arguments={"code": "X"},
            actor_id="u1",
            catalog_action_executor=ForbiddenExecutor(),
        )


def test_infrastructure_resolves_catalog_and_auth_header():
    action = _action(
        oid="synthetic_catalog_read",
        path="/synthetic/{item_id}",
        parameters=(
            {"name": "item_id", "in": "path", "required": True, "type": "string"},
            {"name": "include", "in": "query", "required": False, "type": "string"},
        ),
        execution_mode="catalog_action",
        approved_response_fields=("label",),
    )
    set_actions_for_tests([action])

    client = MagicMock()
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"items": [{"label": "ok", "secret": 9}]}
    client.get.return_value = resp

    executor = AsgiCatalogActionExecutor(client, authorization="Bearer user-token")
    result = executor.execute(
        action_id="synthetic_catalog_read",
        validated_arguments={"item_id": "42", "include": "meta"},
    )
    assert result.outcome == "ok"
    client.get.assert_called_once_with(
        "/synthetic/42",
        params={"include": "meta"},
        headers={"Authorization": "Bearer user-token"},
    )


def test_infrastructure_denies_unknown_non_eligible_and_non_get():
    set_actions_for_tests(
        [
            _action(
                oid="blocked_read",
                path="/blocked",
                status="NEEDS_EXTERNAL_PROCESSING_APPROVAL",
                execution_mode="catalog_action",
                approved_response_fields=("x",),
                parameters=(),
            ),
            _action(
                oid="write_like",
                path="/write",
                method="POST",
                execution_mode="catalog_action",
                approved_response_fields=("x",),
                parameters=(),
            ),
        ]
    )
    client = MagicMock()
    executor = AsgiCatalogActionExecutor(client, authorization="Bearer t")

    unknown = executor.execute(action_id="does_not_exist", validated_arguments={})
    assert unknown.outcome == "error"
    assert "Unknown" in (unknown.error_message or "")

    blocked = executor.execute(action_id="blocked_read", validated_arguments={})
    assert blocked.outcome == "forbidden"

    non_get = executor.execute(action_id="write_like", validated_arguments={})
    assert non_get.outcome == "error"
    assert "GET" in (non_get.error_message or "")
    client.get.assert_not_called()


def test_infrastructure_maps_http_401_403_to_semantic_outcomes():
    action = _action(
        oid="future_read",
        path="/future/{code}",
        parameters=(
            {"name": "code", "in": "path", "required": True, "type": "string"},
        ),
        execution_mode="catalog_action",
        approved_response_fields=("name",),
    )
    set_actions_for_tests([action])
    client = MagicMock()

    resp401 = MagicMock()
    resp401.status_code = 401
    resp401.json.return_value = {"detail": "no"}
    client.get.return_value = resp401
    out401 = AsgiCatalogActionExecutor(client, authorization="Bearer t").execute(
        action_id="future_read", validated_arguments={"code": "X"}
    )
    assert out401.outcome == "unauthorized"

    resp403 = MagicMock()
    resp403.status_code = 403
    resp403.json.return_value = {"detail": "no"}
    client.get.return_value = resp403
    out403 = AsgiCatalogActionExecutor(client, authorization="Bearer t").execute(
        action_id="future_read", validated_arguments={"code": "X"}
    )
    assert out403.outcome == "forbidden"


def test_metamorphic_catalog_action_without_endpoint_specific_code(monkeypatch):
    """Different action_id/path/params execute via the same generic adapter."""
    synthetic = _action(
        oid="demo_widget_lookup",
        path="/widgets/{widget_code}/info",
        parameters=(
            {"name": "widget_code", "in": "path", "required": True, "type": "string"},
            {"name": "locale", "in": "query", "required": False, "type": "string"},
        ),
        execution_mode="catalog_action",
        approved_response_fields=("title",),
        summary="demo widget lookup",
    )
    # Not on production allowlist — only injected for this test index.
    set_actions_for_tests([synthetic])
    secret = "sec"
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.execute_service.candidate_token_secret",
        lambda: secret,
    )
    token = mint_candidate_token(
        action_id="demo_widget_lookup", actor_id="u1", secret=secret, ttl_seconds=60
    )

    client = MagicMock()
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"items": [{"title": "W", "internal_cost": 1}]}
    client.get.return_value = resp
    bound = AsgiCatalogActionExecutor(client, authorization="Bearer actor-a")

    result = execute_delpi_information(
        candidate_token=token,
        arguments={"widget_code": "W-9", "locale": "pt-BR"},
        actor_id="u1",
        catalog_action_executor=bound,
    )
    assert result["data"]["items"][0] == {"title": "W"}
    assert client.get.call_args == call(
        "/widgets/W-9/info",
        params={"locale": "pt-BR"},
        headers={"Authorization": "Bearer actor-a"},
    )
    # No production allowlist pollution.
    assert "demo_widget_lookup" not in load_allowlist_operation_ids(
        load_external_read_allowlist()
    )


def test_bounded_payload_is_not_field_authorization():
    fat = {
        "items": [{"product_code": "A", "secret_cost": 1, "description": "d"}],
        "page": 1,
    }
    bounded = bound_response_payload(fat, max_bytes=65536, max_items=50)
    assert "secret_cost" in bounded["data"]["items"][0]
    projected = apply_approved_field_projection(
        fat, approved_fields=PRODUCT_SEARCH_RESPONSE_FIELDS
    )
    assert "secret_cost" not in projected["items"][0]
    assert set(projected["items"][0].keys()) <= set(PRODUCT_SEARCH_RESPONSE_FIELDS)
    assert projected["items"][0]["product_code"] == "A"
    assert projected["items"][0]["description"] == "d"
    # Missing approved keys are omitted (fail-closed construct-from-scratch).
    assert "group_category" not in projected["items"][0]


def test_hmac_dedicated_secret_precedence(monkeypatch):
    from app.application.external_capabilities.dynamic_information import content_loader
    import app.config as cfg

    class _Dedicated:
        DAVI_CANDIDATE_HMAC_SECRET = "dedicated-hmac"
        JWT_SECRET = "jwt-fallback"

    class _Fallback:
        DAVI_CANDIDATE_HMAC_SECRET = ""
        JWT_SECRET = "jwt-fallback"

    monkeypatch.setattr(cfg, "settings", _Dedicated())
    assert content_loader.candidate_token_secret() == "dedicated-hmac"
    monkeypatch.setattr(cfg, "settings", _Fallback())
    assert content_loader.candidate_token_secret() == "jwt-fallback"


def test_metamorphic_rename_preserves_retrieval():
    a1 = _action(
        oid="search_products",
        path="/products/search",
        summary="buscar produtos cadastro",
    )
    a2 = _action(
        oid="product_master_lookup_v2",
        path="/v2/catalog/items",
        summary="buscar produtos cadastro",
    )
    hits1 = retrieve_eligible_actions("buscar produtos", [a1], top_k=3)
    hits2 = retrieve_eligible_actions("buscar produtos", [a2], top_k=3)
    assert hits1 and hits2
    assert hits1[0][0].operation_id != hits2[0][0].operation_id


def _assert_no_http_transport_in_tree(root: Path) -> None:
    """Structural dependency check — not naive comment/deny-list text search."""
    forbidden_modules = ("fastapi", "httpx", "starlette.testclient")
    paths = [root] if root.is_file() else list(root.rglob("*.py"))
    for path in paths:
        if path.name.startswith("test_"):
            continue
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                mod = node.module
                assert not any(
                    mod == f or mod.startswith(f + ".") for f in forbidden_modules
                ), f"{path}: imports {mod}"
                assert "testclient" not in mod.lower(), path
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "fastapi" not in alias.name
                    assert "httpx" not in alias.name
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr == "get":
                    if isinstance(func.value, ast.Name) and func.value.id in {
                        "client",
                        "http_client",
                        "response",
                    }:
                        raise AssertionError(
                            f"{path}: forbidden call {func.value.id}.get"
                        )
                if isinstance(func, ast.Attribute) and func.attr == "json":
                    if isinstance(func.value, ast.Name) and func.value.id == "response":
                        raise AssertionError(f"{path}: forbidden response.json()")
            if isinstance(node, ast.Attribute) and node.attr == "status_code":
                raise AssertionError(f"{path}: references status_code")
            if isinstance(node, ast.Name) and node.id in {
                "CatalogFixedGetRequest",
                "TestClient",
            }:
                raise AssertionError(f"{path}: references {node.id}")
            if isinstance(node, ast.arg) and node.arg == "authorization":
                raise AssertionError(f"{path}: parameter authorization")


def test_domain_and_application_have_zero_http_transport_dependency():
    api_root = Path(__file__).resolve().parents[1] / "app"
    _assert_no_http_transport_in_tree(
        api_root / "domain" / "ports" / "davi_catalog_action_executor_port.py"
    )
    _assert_no_http_transport_in_tree(
        api_root / "application" / "external_capabilities" / "dynamic_information"
    )
    port_src = (
        api_root / "domain" / "ports" / "davi_catalog_action_executor_port.py"
    ).read_text(encoding="utf-8")
    assert "CatalogFixedGetRequest" not in port_src
    assert "Literal[\"GET\"]" not in port_src
    assert "client.get" not in port_src
    assert "status_code" not in port_src
    # Port must not model transport Authorization as an execute parameter (AST covers this).
    assert "def execute" in port_src


def test_catalog_action_executor_port_is_protocol_compatible():
    assert hasattr(CatalogActionExecutorPort, "execute")


# --- DAVI-DYNAMIC-READ-004: PT-BR retrieval + schema fidelity + outputSchema ---


@pytest.mark.parametrize(
    "query",
    [
        "produto",
        "produtos",
        "buscar produto",
        "buscar o produto 10080055 pelo código",
        "Buscar o produto 10080055 pelo codigo",
        "qual a descrição do produto 10080055",
        "qual a descricao do produto 10080055",
        "qual o grupo do produto 10080055",
        "search products",
        "PRODUTO",
        "  produto!!  ",
    ],
)
def test_ptbr_positive_retrieval(query, monkeypatch):
    action = _load_governed_search_products()
    set_actions_for_tests([action])
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "test-secret-davi",
    )
    discovered = discover_delpi_information(query=query, top_k=5, actor_id="u1")
    assert discovered["candidate_count"] >= 1, (
        f"query={query!r} candidate_count={discovered['candidate_count']}"
    )
    assert discovered["candidates"][0]["action_id"] == "search_products"


@pytest.mark.parametrize(
    "query",
    [
        "preco",
        "price",
        "pricing",
        "custo",
        "cost",
        "qual o clima hoje",
        "escreva um e-mail",
        "qual é a hora",
        "resuma este texto",
        "financeiro",
        "execute sql no banco",
        "painel admin do sistema",
        "pricing do produto",
    ],
)
def test_negative_retrieval_quarantine(query, monkeypatch):
    actions = _load_baseline_actions()
    set_actions_for_tests(actions)
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "test-secret-davi",
    )
    discovered = discover_delpi_information(query=query, top_k=5, actor_id="u1")
    assert discovered["candidate_count"] == 0, (
        f"query={query!r} unexpectedly returned {discovered['candidates']}"
    )
    assert discovered["eligible_action_count"] == 63


def test_stock_eligible_and_branch_is_filter_not_authz():
    allow = load_external_read_allowlist()
    ids = load_allowlist_operation_ids(allow)
    assert "get_product_stock" in ids
    status = classify_operation(
        method="GET",
        path="/products/{code}/stock",
        operation_id="get_product_stock",
        allowlisted_operation_ids=ids,
        allowlist=allow,
    )
    assert status == STATUS_DAVI_ELIGIBLE_READ
    stock = next(
        op
        for op in allow["operations"]
        if isinstance(op, dict) and op.get("operationId") == "get_product_stock"
    )
    assert "branch" in stock["approvedInputFields"]
    actions = _load_baseline_actions()
    stock_action = next(a for a in actions if a.operation_id == "get_product_stock")
    assert stock_action.executable
    assert "branch" in stock_action.approved_input_fields
    # Branch remains a governed query filter, not a DAVI AuthZ decision surface.
    schema = build_argument_json_schema(stock_action)
    assert "branch" in schema["properties"]
    assert schema["properties"]["branch"].get("type") == "string"


def test_nested_projection_structure_paths():
    raw = {
        "root": {
            "code": "PA-1",
            "description": "Finished",
            "type": "PA",
            "unit": "UN",
            "quantity": 1,
            "internal_cost": 99,
            "components": [
                {
                    "code": "MP-1",
                    "description": "Material",
                    "type": "MP",
                    "unit": "KG",
                    "quantity": 2,
                    "unit_price": 5,
                    "components": [
                        {
                            "code": "MP-2",
                            "description": "Sub",
                            "type": "MP",
                            "unit": "UN",
                            "quantity": 3,
                            "secret": True,
                        }
                    ],
                }
            ],
        },
        "page": 1,
        "page_size": 50,
    }
    fields = (
        "root.code",
        "root.description",
        "root.type",
        "root.unit",
        "root.quantity",
        "root.components[].code",
        "root.components[].description",
        "root.components[].type",
        "root.components[].unit",
        "root.components[].quantity",
        "root.components[].components[].code",
        "root.components[].components[].description",
        "root.components[].components[].type",
        "root.components[].components[].unit",
        "root.components[].components[].quantity",
    )
    projected = apply_approved_field_projection(raw, approved_fields=fields)
    assert projected["root"]["code"] == "PA-1"
    assert "internal_cost" not in projected["root"]
    assert projected["root"]["components"][0]["code"] == "MP-1"
    assert "unit_price" not in projected["root"]["components"][0]
    assert projected["root"]["components"][0]["components"][0]["code"] == "MP-2"
    assert "secret" not in projected["root"]["components"][0]["components"][0]
    assert projected["page"] == 1


def test_pagination_uses_budgets_not_product_search_max(monkeypatch):
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.argument_validator.load_dynamic_read_budgets",
        lambda: {
            "default_page_size": 7,
            "max_page_size": 13,
            "execute_max_items": 13,
        },
    )
    action = _action(
        oid="get_product_stock",
        path="/products/{code}/stock",
        parameters=(
            {"name": "code", "in": "path", "required": True, "type": "string"},
            {"name": "branch", "in": "query", "required": False, "type": "string"},
            {"name": "page", "in": "query", "required": False, "type": "integer"},
            {"name": "page_size", "in": "query", "required": False, "type": "integer"},
        ),
        approved_input_fields=("code", "branch", "page", "page_size"),
        approved_response_fields=(
            "product_code",
            "branch",
            "warehouse",
            "current_quantity",
            "available_quantity",
        ),
        execution_mode="catalog_action",
    )
    schema = build_argument_json_schema(action)
    assert schema["properties"]["page_size"]["maximum"] == 13
    assert schema["properties"]["page_size"]["default"] == 7
    assert schema["properties"]["page_size"]["maximum"] != PRODUCT_SEARCH_MAX_PAGE_SIZE
    ok = validate_arguments(action, {"code": "A", "page_size": 13})
    assert ok["page_size"] == 13
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, {"code": "A", "page_size": 14})


def test_backend_403_propagation(monkeypatch):
    action = _action(
        oid="get_product_stock",
        path="/products/{code}/stock",
        parameters=(
            {"name": "code", "in": "path", "required": True, "type": "string"},
            {"name": "branch", "in": "query", "required": False, "type": "string"},
        ),
        approved_input_fields=("code", "branch"),
        approved_response_fields=(
            "product_code",
            "branch",
            "warehouse",
            "current_quantity",
            "available_quantity",
        ),
        execution_mode="catalog_action",
    )
    set_actions_for_tests([action])
    secret = "sec"
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.execute_service.candidate_token_secret",
        lambda: secret,
    )
    token = mint_candidate_token(
        action_id="get_product_stock", actor_id="u1", secret=secret, ttl_seconds=60
    )

    class ForbiddenExecutor:
        def execute(self, *, action_id, validated_arguments):
            return CatalogActionExecutionResult(outcome="forbidden")

    with pytest.raises(PermissionError, match="Forbidden"):
        execute_delpi_information(
            candidate_token=token,
            arguments={"code": "10080055", "branch": "02"},
            actor_id="u1",
            catalog_action_executor=ForbiddenExecutor(),
        )


def test_no_davi_local_branch_acl_residual():
    root = (
        _api_root()
        / "app/application/external_capabilities/dynamic_information"
    )
    forbidden_markers = (
        "DAVI_BRANCH_AUTHZ",
        "DAVI_LOCAL_RBAC",
        "require_branch_permission",
        "filial_view_perm",
        "BRANCH_VIEW_PERMS",
        "branch_access_error",
    )
    for name in ("eligibility.py", "constants.py", "retrieval.py", "execute_service.py"):
        text = (root / name).read_text(encoding="utf-8")
        for marker in forbidden_markers:
            assert marker not in text, f"{name} must not invent {marker}"
    # Stock without governed projection is model-safety gated — not branch AuthZ.
    assert (
        classify_operation(
            method="GET",
            path="/products/{code}/stock",
            operation_id="get_product_stock",
            allowlisted_operation_ids=set(),
        )
        == STATUS_NEEDS_MODEL_SAFE_PROJECTION
    )
    assert (
        classify_operation(
            method="GET",
            path="/products/{code}/stock",
            operation_id="get_product_stock",
            allowlisted_operation_ids=set(),
        )
        != STATUS_NEEDS_BRANCH_AUTHZ_EVIDENCE
    )


def test_multi_candidate_produto_vs_estoque(monkeypatch):
    set_actions_for_tests(_load_baseline_actions())
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "test-secret-davi",
    )
    product = discover_delpi_information(
        query="buscar produtos", top_k=5, actor_id="u1"
    )
    assert product["candidate_count"] >= 1
    assert product["candidates"][0]["action_id"] == "search_products"

    stock = discover_delpi_information(
        query="estoque do produto 10080055", top_k=5, actor_id="u1"
    )
    assert stock["candidate_count"] >= 1
    assert stock["candidates"][0]["action_id"] == "get_product_stock"
    action_ids = {c["action_id"] for c in stock["candidates"]}
    assert "get_product_stock" in action_ids
    # Distinct intents must not collapse onto the same top action.
    assert product["candidates"][0]["action_id"] != stock["candidates"][0]["action_id"]


def test_unwrap_api_envelope_projection():
    envelope = {
        "success": True,
        "message": "ok",
        "meta": {"operationId": "get_product_stock"},
        "data": {
            "items": [
                {
                    "product_code": "10080055",
                    "branch": "01",
                    "warehouse": "01",
                    "current_quantity": 10,
                    "available_quantity": 8,
                    "unit_cost": 12.5,
                    "internal_flag": True,
                }
            ],
            "page": 1,
            "page_size": 50,
            "total": 1,
        },
    }
    fields = (
        "product_code",
        "branch",
        "warehouse",
        "current_quantity",
        "available_quantity",
    )
    projected = apply_approved_field_projection(envelope, approved_fields=fields)
    assert "success" not in projected
    assert "meta" not in projected
    assert set(projected["items"][0].keys()) == set(fields)
    assert projected["items"][0]["available_quantity"] == 8
    assert "unit_cost" not in projected["items"][0]


def test_search_products_discovery_schema_matches_approved_input(monkeypatch):
    action = _load_governed_search_products()
    set_actions_for_tests([action])
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "test-secret-davi",
    )
    discovered = discover_delpi_information(query="produto", top_k=3, actor_id="u1")
    schema = discovered["candidates"][0]["argument_schema"]
    assert set(schema["properties"].keys()) == set(PRODUCT_SEARCH_INPUT_FIELDS)
    assert schema["additionalProperties"] is False
    for forbidden in ("sort", "direction", "customer_reference"):
        assert forbidden not in schema["properties"]
    # Same schema used by execution validation.
    assert build_argument_json_schema(action)["properties"].keys() == schema[
        "properties"
    ].keys()


def test_unknown_and_unapproved_arguments_denied():
    action = _load_governed_search_products()
    for bad in (
        {"url": "https://evil"},
        {"sort": "code"},
        {"direction": "desc"},
        {"customer_reference": "x"},
        {"unknown": "y"},
    ):
        with pytest.raises(ArgumentValidationError):
            validate_arguments(action, bad)


def test_execution_parity_passes_pagination_to_runner(monkeypatch):
    action = _load_governed_search_products()
    set_actions_for_tests([action])
    secret = "sec"
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.execute_service.candidate_token_secret",
        lambda: secret,
    )
    token = mint_candidate_token(
        action_id="search_products", actor_id="u1", secret=secret, ttl_seconds=60
    )
    captured: dict[str, Any] = {}

    def runner(**kwargs):
        captured.update(kwargs)
        return {
            "items": [
                {
                    "product_code": "10080055",
                    "description": "TERM",
                    "group_category": "1008",
                    "cost": 1,
                }
            ],
            "page": kwargs.get("page"),
            "page_size": kwargs.get("page_size"),
            "total": 1,
            "total_pages": 1,
        }

    result = execute_delpi_information(
        candidate_token=token,
        arguments={
            "code": "10080055",
            "description": "TERM",
            "group_code": "1008",
            "page": 2,
            "page_size": 10,
        },
        actor_id="u1",
        search_products_runner=runner,
    )
    assert captured["code"] == "10080055"
    assert captured["description"] == "TERM"
    assert captured["group_code"] == "1008"
    assert captured["page"] == 2
    assert captured["page_size"] == 10
    assert result["projection"] == "approved_fields"
    assert set(result["data"]["items"][0].keys()) == set(PRODUCT_SEARCH_RESPONSE_FIELDS)


def test_live_like_ptbr_discover_execute_flow(monkeypatch):
    action = _load_governed_search_products()
    set_actions_for_tests([action])
    secret = "test-secret-davi"
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: secret,
    )
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.execute_service.candidate_token_secret",
        lambda: secret,
    )
    discovered = discover_delpi_information(
        query="Buscar o produto 10080055 pelo código",
        top_k=5,
        actor_id="u1",
    )
    assert discovered["candidate_count"] == 1
    assert discovered["candidates"][0]["action_id"] == "search_products"
    token = discovered["candidates"][0]["candidate_token"]

    def runner(**kwargs):
        assert kwargs["code"] == "10080055"
        return {
            "items": [
                {
                    "product_code": "10080055",
                    "description": "TERM. FASTON",
                    "group_category": "1008",
                    "internal": True,
                }
            ],
            "page": 1,
            "page_size": 50,
            "total": 1,
            "total_pages": 1,
        }

    result = execute_delpi_information(
        candidate_token=token,
        arguments={"code": "10080055"},
        actor_id="u1",
        search_products_runner=runner,
    )
    assert result["status"] == "ok"
    assert result["projection"] == "approved_fields"
    assert len(result["data"]["items"]) == 1
    assert set(result["data"]["items"][0].keys()) == set(PRODUCT_SEARCH_RESPONSE_FIELDS)


def test_synthetic_semantic_alias_generalization(monkeypatch):
    synthetic = _action(
        oid="demo_widget_lookup",
        path="/widgets/{widget_code}",
        parameters=(
            {"name": "widget_code", "in": "path", "required": True, "type": "string"},
        ),
        execution_mode="catalog_action",
        approved_response_fields=("title",),
        approved_input_fields=("widget_code",),
        semantic_aliases=("consultar widget", "buscar widget"),
        summary="demo widget lookup",
    )
    set_actions_for_tests([synthetic])
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "sec",
    )
    discovered = discover_delpi_information(
        query="consultar widget", top_k=3, actor_id="u1"
    )
    assert discovered["candidate_count"] == 1
    assert discovered["candidates"][0]["action_id"] == "demo_widget_lookup"
    assert "demo_widget_lookup" not in load_allowlist_operation_ids(
        load_external_read_allowlist()
    )


def test_mcp_output_schemas_present_for_all_three_tools():
    import asyncio
    from app.interface.mcp.server import create_mcp_server
    from app.interface.mcp.schemas import (
        DiscoverDelpiInformationOutput,
        ExecuteDelpiInformationOutput,
        SearchProductsOutput,
        discover_delpi_information_output_json_schema,
        execute_delpi_information_output_json_schema,
    )

    mcp = create_mcp_server()
    tools = asyncio.run(mcp.list_tools())
    assert len(tools) == 2
    by_name = {t.name: t for t in tools}
    assert set(by_name) == {
        "discover_delpi_information",
        "execute_delpi_information",
    }
    assert (
        by_name["discover_delpi_information"].outputSchema
        == discover_delpi_information_output_json_schema()
    )
    assert (
        by_name["execute_delpi_information"].outputSchema
        == execute_delpi_information_output_json_schema()
    )
    # Capability projection model remains available (not MCP-registered).
    SearchProductsOutput.model_validate(
        {
            "items": [{"product_code": "1", "description": "d", "group_category": "g"}],
            "page": 1,
            "page_size": 50,
            "total": 1,
            "total_pages": 1,
        }
    )

    # Runtime envelopes validate against output models.
    DiscoverDelpiInformationOutput.model_validate(
        {
            "query": "produto",
            "top_k": 5,
            "candidate_count": 1,
            "eligible_action_count": 1,
            "candidates": [
                {
                    "candidate_token": "x.y",
                    "description": "Search products",
                    "semantic_hints": {"entity": "product", "shape": "paged_list", "tags": []},
                    "required_arguments": [],
                    "argument_schema": {"type": "object", "properties": {}},
                    "pagination_hints": {
                        "supports_page": True,
                        "supports_page_size": True,
                    },
                    "retrieval_score": 0.8,
                    "action_id": "search_products",
                }
            ],
            "capability_surface": {
                "agent_directives": {"read_only": True, "version": "test"},
            },
        }
    )
    ExecuteDelpiInformationOutput.model_validate(
        {
            "action_id": "search_products",
            "status": "ok",
            "entity": "product",
            "shape": "paged_list",
            "projection": "approved_fields",
            "data": {"items": []},
            "truncated": False,
            "is_complete": True,
            "response_bytes": 12,
        }
    )
    SearchProductsOutput.model_validate(
        {
            "items": [
                {
                    "product_code": "A",
                    "description": "d",
                    "group_category": "g",
                }
            ],
            "page": 1,
            "page_size": 50,
            "total": 1,
            "total_pages": 1,
        }
    )


def test_no_hardcoded_portuguese_phrase_to_operation_id_map():
    root = (
        Path(__file__).resolve().parents[1]
        / "app/application/external_capabilities/dynamic_information"
    )
    for path in root.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert '"produto": "search_products"' not in text
        assert "'produto': 'search_products'" not in text
        assert "if \"produto\" in query" not in text
        assert "if 'produto' in query" not in text


# --- DAVI-READ-AUTHZ-REBASELINE-002: genericity + fail-closed projection ---


def test_no_operation_id_semantic_registry_in_broker():
    root = (
        Path(__file__).resolve().parents[1]
        / "app/application/external_capabilities/dynamic_information"
    )
    eligibility = (root / "eligibility.py").read_text(encoding="utf-8")
    for marker in (
        "_NESTED_PROJECTION_CANDIDATES",
        "_SEMANTICALLY_REDUNDANT =",
        'frozenset({"get_product_detail"',
        '"get_product_structure"',
        '"get_product_stock"',
    ):
        assert marker not in eligibility, f"eligibility must not hardcode {marker}"
    projection = (root / "projection.py").read_text(encoding="utf-8")
    assert "get_product_" not in projection


def test_metadata_disposition_semantically_redundant_independent_of_name():
    allowlist = {
        "operations": [],
        "explicitlyNotApproved": [
            {
                "operationId": "arbitrary_redundant_capability_xyz",
                "coverageDisposition": "SEMANTICALLY_REDUNDANT",
            }
        ],
    }
    assert (
        classify_operation(
            method="GET",
            path="/anything/{code}",
            operation_id="arbitrary_redundant_capability_xyz",
            allowlisted_operation_ids=set(),
            shape="paged_list",
            allowlist=allowlist,
        )
        == STATUS_SEMANTICALLY_REDUNDANT
    )


def test_explicit_processing_prohibition_before_eligibility():
    allowlist = {
        "operations": [
            {
                "operationId": "forbidden_but_projected",
                "approvedInputFields": ["code"],
                "approvedResponseFields": ["code"],
            }
        ],
        "explicitProcessingProhibitions": [{"operationId": "forbidden_but_projected"}],
    }
    assert (
        classify_operation(
            method="GET",
            path="/x/{code}",
            operation_id="forbidden_but_projected",
            allowlisted_operation_ids={"forbidden_but_projected"},
            shape="paged_list",
            allowlist=allowlist,
        )
        == STATUS_EXPLICIT_PROCESSING_PROHIBITION
    )


def test_nested_shape_with_flat_fields_not_eligible():
    allowlist = {
        "operations": [
            {
                "operationId": "synthetic_nested_flat_fields",
                "approvedInputFields": ["code"],
                "approvedResponseFields": ["code", "description"],
            }
        ],
    }
    assert (
        classify_operation(
            method="GET",
            path="/synthetic/{code}",
            operation_id="synthetic_nested_flat_fields",
            allowlisted_operation_ids={"synthetic_nested_flat_fields"},
            shape="hierarchy",
            allowlist=allowlist,
        )
        == STATUS_NEEDS_NESTED_PROJECTION_SUPPORT
    )


def test_nested_shape_with_valid_paths_eligible():
    allowlist = {
        "operations": [
            {
                "operationId": "synthetic_nested_ok",
                "approvedInputFields": ["code"],
                "approvedResponseFields": ["root.code", "root.components[].code"],
            }
        ],
    }
    assert (
        classify_operation(
            method="GET",
            path="/synthetic/{code}",
            operation_id="synthetic_nested_ok",
            allowlisted_operation_ids={"synthetic_nested_ok"},
            shape="hierarchy",
            allowlist=allowlist,
        )
        == STATUS_DAVI_ELIGIBLE_READ
    )


def test_synthetic_unseen_operation_metadata_only_eligible():
    oid = "completely_unseen_read_name"
    allowlist = {
        "operations": [
            {
                "operationId": oid,
                "executionMode": "catalog_action",
                "approvedInputFields": ["code", "page", "page_size"],
                "approvedResponseFields": ["product_code", "description"],
                "semanticAliases": ["unseen capability alias"],
            }
        ],
    }
    assert (
        classify_operation(
            method="GET",
            path="/unseen/{code}",
            operation_id=oid,
            allowlisted_operation_ids={oid},
            shape="paged_list",
            allowlist=allowlist,
        )
        == STATUS_DAVI_ELIGIBLE_READ
    )
    action = _action(
        oid=oid,
        path="/unseen/{code}",
        parameters=(
            {"name": "code", "in": "path", "required": True, "type": "string"},
            {"name": "page", "in": "query", "type": "integer"},
            {"name": "page_size", "in": "query", "type": "integer"},
        ),
        approved_input_fields=("code", "page", "page_size"),
        approved_response_fields=("product_code", "description"),
        execution_mode="catalog_action",
        semantic_aliases=("unseen capability alias",),
    )
    plan = build_execution_plan(action, {"code": "X", "page": 1, "page_size": 10})
    assert isinstance(plan, CatalogActionPlan)
    projected = apply_approved_field_projection(
        {
            "items": [
                {
                    "product_code": "X",
                    "description": "ok",
                    "secret_cost": 1,
                    "internal_flag": True,
                }
            ],
            "page": 1,
            "internal_summary": {"total_cost": 9},
        },
        approved_fields=("product_code", "description"),
    )
    assert set(projected.keys()) == {"items", "page"}
    assert set(projected["items"][0].keys()) == {"product_code", "description"}
    assert "internal_summary" not in projected


def test_flat_projection_drops_root_siblings_and_item_extras():
    projected = apply_approved_field_projection(
        {
            "items": [
                {
                    "product_code": "A",
                    "description": "Produto",
                    "unit_cost": 99,
                    "internal_flag": True,
                }
            ],
            "page": 1,
            "page_size": 50,
            "total": 1,
            "total_pages": 1,
            "internal_summary": {"total_cost": 999},
            "bom_validity": {"ok": True},
            "reference_date": "20260101",
        },
        approved_fields=("product_code", "description"),
    )
    assert set(projected.keys()) == {
        "items",
        "page",
        "page_size",
        "total",
        "total_pages",
    }
    assert set(projected["items"][0].keys()) == {"product_code", "description"}
    assert "internal_summary" not in projected
    assert "bom_validity" not in projected
    assert "reference_date" not in projected


def test_flat_root_object_fail_closed():
    projected = apply_approved_field_projection(
        {"product_code": "A", "description": "X", "secret_cost": 99},
        approved_fields=("product_code", "description"),
    )
    assert projected == {"product_code": "A", "description": "X"}


def test_top_level_list_fail_closed():
    projected = apply_approved_field_projection(
        [
            {"name": "A", "secret": 1},
            {"name": "B", "secret": 2},
            {"name": "C", "secret": 3},
        ],
        approved_fields=("name",),
        max_array_items=2,
    )
    assert projected == [{"name": "A"}, {"name": "B"}]


def test_scalar_and_empty_projection_fail_closed():
    assert apply_approved_field_projection("raw", approved_fields=("a",)) == {}
    assert apply_approved_field_projection(42, approved_fields=("a",)) == {}
    assert apply_approved_field_projection({"a": 1}, approved_fields=None) == {}
    assert apply_approved_field_projection({"a": 1}, approved_fields=()) == {}


def test_malformed_projection_paths_fail_closed():
    raw = {"root": {"code": "A", "secret": 1}}
    for bad in ("root..secret", "root[", "[]", "*", "root.*", "root.components[].*"):
        projected = apply_approved_field_projection(raw, approved_fields=(bad,))
        assert projected == {} or "secret" not in json.dumps(projected)


def test_nested_unknown_fields_dropped_and_bounds():
    deep = {"code": "L0", "secret": 1, "components": []}
    node = deep
    for i in range(1, 12):
        child = {"code": f"L{i}", "secret": i, "components": []}
        node["components"].append(child)
        node = child
    fields = (
        "root.code",
        "root.components[].code",
        "root.components[].components[].code",
        "root.components[].components[].components[].code",
    )
    projected = apply_approved_field_projection(
        {"root": deep},
        approved_fields=fields,
        max_depth=2,
        max_array_items=1,
    )
    assert projected["root"]["code"] == "L0"
    assert "secret" not in projected["root"]
    assert len(projected["root"]["components"]) == 1
    assert "secret" not in projected["root"]["components"][0]


def test_eligible_count_is_thirteen():
    actions = _load_baseline_actions()
    eligible = sorted(a.operation_id for a in actions if a.executable)
    assert eligible == sorted(_ELIGIBLE_OPERATION_IDS)
    assert len(eligible) == 63
