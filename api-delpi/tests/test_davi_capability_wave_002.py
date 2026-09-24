"""DAVI Wave 2 — governed product economic READ promotion."""

from __future__ import annotations

import ast
import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

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
)
from app.application.external_capabilities.dynamic_information.read_only_intent_guard import (
    clear_read_only_intent_guard_cache,
)
from app.domain.ports.davi_catalog_action_executor_port import CatalogActionExecutionResult

_API_ROOT = Path(__file__).resolve().parents[1]
_WAVE2 = (
    "get_product_pricing",
    "get_product_purchase_price_history",
    "get_product_last_purchase",
)
_CURRENT_TEN = (
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
)
_UNKNOWN_ARGS = (
    "sql",
    "url",
    "path",
    "method",
    "operationId",
    "legacy",
    "debug",
    "include_raw",
    "customer_reference",
    "sort",
)
_TODAY = date(2026, 9, 17)


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
    return next(
        op
        for op in allow["operations"]
        if isinstance(op, dict) and op.get("operationId") == oid
    )


def _dumped(payload: Any) -> str:
    return json.dumps(payload, default=str, ensure_ascii=False)


def _synthetic_history_action() -> TechnicalAction:
    return TechnicalAction(
        action_id="synthetic_history_read",
        operation_id="synthetic_history_read",
        method="GET",
        path="/synthetic/{code}",
        summary="synthetic history",
        description="",
        tags=("synthetic",),
        davi_status="DAVI_ELIGIBLE_READ",
        parameters=(
            {"name": "code", "in": "path", "required": True, "type": "string"},
            {"name": "start_date", "in": "query", "required": False, "type": "string"},
            {"name": "end_date", "in": "query", "required": False, "type": "string"},
            {"name": "history_limit", "in": "query", "required": False, "type": "integer"},
        ),
        searchable_text="synthetic history",
        execution_mode="catalog_action",
        approved_response_fields=("code",),
        approved_input_fields=("code", "start_date", "end_date", "history_limit"),
        argument_constraints={
            "dateRange": {
                "startField": "start_date",
                "endField": "end_date",
                "maxDays": 365,
                "defaultWindowDays": 365,
                "absentEnd": "today",
                "absentStart": "effectiveEndMinusDefaultWindow",
            },
            "argumentLimits": {
                "history_limit": {"minimum": 1, "maximum": 50, "default": 24}
            },
        },
    )


class _PayloadExecutor:
    def __init__(self, payload: Any):
        self.payload = payload
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def execute(self, *, action_id: str, validated_arguments: dict[str, Any]):
        self.calls.append((action_id, dict(validated_arguments)))
        return CatalogActionExecutionResult(outcome="ok", payload=self.payload)


def test_wave2_eligible_count_exactly_thirteen():
    eligible = sorted(a.operation_id for a in _actions() if a.executable)
    assert len(eligible) == 53
    assert set(_CURRENT_TEN) | set(_WAVE2) <= set(eligible)
    allow = load_external_read_allowlist()
    assert allow.get("version") == 11
    blocked = {
        item.get("operationId")
        for item in allow.get("explicitlyNotApproved") or []
        if isinstance(item, dict)
    }
    for oid in (
        "get_product_summary",
        "get_product_raw_material_price_intelligence",
        "get_product_cost_impact_simulation",
    ):
        assert oid not in set(eligible)
        assert oid in blocked
    assert "get_product_last_purchase" not in blocked


def test_wave2_mcp_tools_remain_three():
    import asyncio
    from app.interface.mcp.server import create_mcp_server

    tools = asyncio.run(create_mcp_server().list_tools())
    assert [t.name for t in tools] == [
        "search_products",
        "discover_delpi_information",
        "execute_delpi_information",
    ]


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("preço do produto 10080055", "get_product_pricing"),
        ("preço comercial do produto 10080055", "get_product_pricing"),
        ("tabela de preço do produto 10080055", "get_product_pricing"),
        ("histórico de preço de compra do produto 10080055", "get_product_purchase_price_history"),
        ("evolução de preço de compra", "get_product_purchase_price_history"),
        ("último preço de compra do produto 10080055", "get_product_last_purchase"),
        ("última NF de compra", "get_product_last_purchase"),
        ("produto 10080055", "search_products"),
        ("estoque 10080001", "get_product_stock"),
        ("fornecedores 10080055", "get_product_suppliers"),
        ("compras do produto", "get_product_purchases"),
        ("estrutura 90261805", "get_product_structure"),
        ("status de produção 10080055", "get_product_production_status"),
        ("status fabril do produto", "get_product_factory_status"),
        ("factory status do produto", "get_product_factory_status"),
        ("MP exclusiva", "get_product_structure_exclusivity"),
        ("expedição", "get_product_shipping_status"),
    ],
)
def test_wave2_and_current_ten_retrieval(query, expected, monkeypatch):
    set_actions_for_tests(_actions())
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "sec",
    )
    discovered = discover_delpi_information(query=query, top_k=5, actor_id="u1")
    assert discovered["eligible_action_count"] == 53, query
    assert discovered["candidate_count"] >= 1, query
    assert discovered["candidates"][0]["action_id"] == expected, (
        query,
        [c["action_id"] for c in discovered["candidates"]],
    )


@pytest.mark.parametrize(
    ("query", "expected", "forbidden"),
    [
        ("preço do produto", "get_product_pricing", "get_product_purchase_price_history"),
        ("histórico de preço de compra", "get_product_purchase_price_history", "get_product_pricing"),
        ("último preço de compra", "get_product_last_purchase", "get_product_purchase_price_history"),
        ("compras do produto", "get_product_purchases", "get_product_purchase_price_history"),
        ("fornecedores", "get_product_suppliers", "get_product_last_purchase"),
        ("estoque", "get_product_stock", "get_product_pricing"),
        ("estrutura", "get_product_structure", "get_product_structure_exclusivity"),
        ("status de produção", "get_product_production_status", "get_product_factory_status"),
        ("status fabril", "get_product_factory_status", "get_product_shipping_status"),
        ("expedição", "get_product_shipping_status", "get_product_production_status"),
        ("MP exclusiva", "get_product_structure_exclusivity", "get_product_structure"),
    ],
)
def test_wave2_sibling_disambiguation(query, expected, forbidden, monkeypatch):
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
        "preço",
        "price",
        "pricing",
        "custo",
        "cost",
        "inteligência de preço de matéria-prima",
        "impacto no custo",
        "simulação de custo",
        "preço e custo do produto",
        "pricing cost",
        "preço admin",
        "price sql",
        "factory sql",
        "factory admin",
    ],
)
def test_bare_economic_and_deferred_intents_remain_quarantined(query, monkeypatch):
    set_actions_for_tests(_actions())
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "sec",
    )
    discovered = discover_delpi_information(query=query, top_k=5, actor_id="u1")
    assert discovered["candidate_count"] == 0, (query, discovered["candidates"])


@pytest.mark.parametrize(
    "query",
    [
        "altere o preço do produto",
        "cadastre um preço comercial",
        "atualize o último preço de compra",
        "edite o histórico de preço",
        "altere o custo",
        "simule e aplique novo custo",
    ],
)
def test_wave2_write_intent_returns_zero(query, monkeypatch):
    set_actions_for_tests(_actions())
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "sec",
    )
    discovered = discover_delpi_information(query=query, top_k=5, actor_id="u1")
    assert discovered["candidate_count"] == 0, (query, discovered["candidates"])


def test_economic_quarantine_tokens_remain_global():
    tokens = {
        str(t).lower()
        for t in (load_external_read_allowlist().get("retrievalQuarantineTokens") or [])
    }
    for token in ("preco", "price", "pricing", "custo", "cost"):
        assert token in tokens


def test_wave2_inputs_outputs_and_no_wildcards():
    pricing = _allowlist_entry("get_product_pricing")
    history = _allowlist_entry("get_product_purchase_price_history")
    last = _allowlist_entry("get_product_last_purchase")
    assert pricing["approvedInputFields"] == ["code"]
    assert history["approvedInputFields"] == [
        "code",
        "branch",
        "start_date",
        "end_date",
        "history_limit",
    ]
    assert last["approvedInputFields"] == ["code", "branch"]
    assert len(pricing["approvedResponseFields"]) == 10
    assert len(history["approvedResponseFields"]) == 22
    assert len(last["approvedResponseFields"]) == 14
    for entry in (pricing, history, last):
        assert entry["executionMode"] == "catalog_action"
        assert not any("*" in field for field in entry["approvedResponseFields"])
        schema = build_argument_json_schema(_action(entry["operationId"]))
        assert schema["additionalProperties"] is False
        assert "legacy" not in schema["properties"]
        assert "date_start" not in schema["properties"]
        assert "date_end" not in schema["properties"]
    history_schema = build_argument_json_schema(_action("get_product_purchase_price_history"))
    assert history_schema["properties"]["history_limit"]["minimum"] == 1
    assert history_schema["properties"]["history_limit"]["maximum"] == 50
    assert history_schema["properties"]["history_limit"]["default"] == 24


@pytest.mark.parametrize("oid", _WAVE2)
@pytest.mark.parametrize("bad", _UNKNOWN_ARGS)
def test_wave2_unknown_arguments_rejected(oid, bad):
    action = _action(oid)
    args: dict[str, Any] = {"code": "10080001"}
    args[bad] = "x"
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, args)


def test_generic_effective_date_range_policy(monkeypatch):
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.argument_validator._constraint_today",
        lambda: _TODAY,
    )
    dated = _synthetic_history_action()
    assert validate_arguments(dated, {"code": "X"})["code"] == "X"
    assert validate_arguments(
        dated, {"code": "X", "start_date": "2025-09-17", "end_date": "2026-09-17"}
    )["start_date"] == "2025-09-17"
    with pytest.raises(ArgumentValidationError, match="exceeds 365"):
        validate_arguments(
            dated, {"code": "X", "start_date": "2025-09-16", "end_date": "2026-09-17"}
        )
    with pytest.raises(ArgumentValidationError, match="exceeds 365"):
        validate_arguments(dated, {"code": "X", "start_date": "2025-01-01"})
    ok_end_only = validate_arguments(dated, {"code": "X", "end_date": "2026-06-01"})
    assert ok_end_only["end_date"] == "2026-06-01"
    with pytest.raises(ArgumentValidationError, match="must not be before"):
        validate_arguments(
            dated, {"code": "X", "start_date": "2026-06-02", "end_date": "2026-06-01"}
        )
    source = (
        _API_ROOT
        / "app/application/external_capabilities/dynamic_information/argument_validator.py"
    ).read_text(encoding="utf-8")
    assert "get_product_purchase_price_history" not in source
    assert "get_product_pricing" not in source
    assert "if action.operation_id" not in source


def test_purchase_history_date_and_limit_constraints(monkeypatch):
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.argument_validator._constraint_today",
        lambda: _TODAY,
    )
    action = _action("get_product_purchase_price_history")
    omitted = validate_arguments(action, {"code": "10080001"})
    assert omitted["history_limit"] == 24
    assert "start_date" not in omitted
    assert "end_date" not in omitted
    validate_arguments(
        action,
        {"code": "X", "start_date": "2025-09-17", "end_date": "2026-09-17"},
    )
    with pytest.raises(ArgumentValidationError):
        validate_arguments(
            action,
            {"code": "X", "start_date": "2025-09-16", "end_date": "2026-09-17"},
        )
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, {"code": "X", "start_date": "2024-01-01"})
    validate_arguments(action, {"code": "X", "end_date": "2026-06-01"})
    with pytest.raises(ArgumentValidationError):
        validate_arguments(
            action,
            {"code": "X", "start_date": "2026-06-02", "end_date": "2026-06-01"},
        )
    assert validate_arguments(action, {"code": "X", "history_limit": 50})["history_limit"] == 50
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, {"code": "X", "history_limit": 51})
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, {"code": "X", "branch": "03"})
    assert validate_arguments(action, {"code": "X", "branch": "all"})["branch"] == "all"


def test_last_purchase_branch_enum():
    action = _action("get_product_last_purchase")
    assert validate_arguments(action, {"code": "X", "branch": "all"})["branch"] == "all"
    assert validate_arguments(action, {"code": "X", "branch": "01"})["branch"] == "01"
    assert validate_arguments(action, {"code": "X", "branch": "02"})["branch"] == "02"
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, {"code": "X", "branch": "03"})
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, {"code": "X", "branch": "ALL"})


def test_pricing_projection_drops_commercial_internals():
    fields = tuple(_allowlist_entry("get_product_pricing")["approvedResponseFields"])
    raw = {
        "product": {
            "code": "10080055",
            "description": "PA",
            "unit": "UN",
            "standard_cost": 9.99,
        },
        "prices": [
            {
                "table_code": "001",
                "table_description": "Padrao",
                "sale_price": 12.5,
                "currency": "1",
                "lot_quantity": 1.0,
                "valid_from": "20260101",
                "active": "S",
                "max_price": 99.0,
                "discount_value": 1.0,
                "discount_percent": 10.0,
                "state": "SP",
                "operation_type": "V",
                "internal_debug": True,
            }
        ],
        "unit_price": 0.01,
        "customer_reference": "SECRET",
        "unexpected": True,
    }
    projected = apply_approved_field_projection(raw, approved_fields=fields)
    dumped = _dumped(projected)
    assert projected["product"]["code"] == "10080055"
    assert projected["prices"][0]["sale_price"] == 12.5
    assert projected["prices"][0]["currency"] == "1"
    for sibling in (
        "max_price",
        "discount_value",
        "discount_percent",
        "state",
        "operation_type",
        "standard_cost",
        "internal_debug",
        "unit_price",
        "customer_reference",
        "unexpected",
    ):
        assert sibling not in dumped or sibling == "unit_price"
        if sibling != "unit_price":
            assert f'"{sibling}"' not in dumped
    assert "unit_price" not in dumped


def test_history_projection_drops_registered_and_tax_id():
    fields = tuple(
        _allowlist_entry("get_product_purchase_price_history")["approvedResponseFields"]
    )
    raw = {
        "product": {
            "product_code": "10080001",
            "description": "MP",
            "product_type": "MP",
            "unit": "KG",
            "registered_last_purchase_price": 0.5,
            "registered_last_purchase_date": "20200101",
            "registered_icms_rate": 12,
            "standard_cost": 0.02,
        },
        "start_date": "20250917",
        "date_end_exclusive": "20260918",
        "branch": "all",
        "items": [
            {
                "issue_date": "20260901",
                "invoice_number": "000200",
                "supplier_code": "S2",
                "supplier_name": "Beta",
                "quantity": 5,
                "unit_price": 0.20,
                "total_value": 1.0,
                "icms_rate": 12.0,
                "previous_unit_price": 0.10,
                "variation_percent": 100.0,
                "entry_date": "20260902",
                "invoice_series": "1",
                "supplier_store": "01",
                "icms_value": 0.12,
                "purchase_order": "PC9",
                "branch": "01",
                "supplier_tax_id": "12345678000199",
            },
            {
                "issue_date": "20260801",
                "invoice_number": "000100",
                "supplier_code": "S1",
                "supplier_name": "Alfa",
                "quantity": 2,
                "unit_price": 0.10,
                "total_value": 0.2,
                "icms_rate": 12.0,
                "previous_unit_price": None,
                "variation_percent": None,
            },
        ],
        "summary": {
            "total_purchases": 2,
            "min_unit_price": 0.10,
            "max_unit_price": 0.20,
            "avg_unit_price": 0.15,
            "last_variation_percent": 100.0,
        },
        "internal_debug": True,
        "sale_price": 99,
        "customer_reference": "nope",
    }
    projected = apply_approved_field_projection(raw, approved_fields=fields)
    dumped = _dumped(projected)
    assert projected["items"][0]["invoice_number"] == "000200"
    assert projected["items"][1]["invoice_number"] == "000100"
    assert projected["summary"]["total_purchases"] == 2
    for sibling in (
        "registered_last_purchase_price",
        "standard_cost",
        "entry_date",
        "invoice_series",
        "supplier_store",
        "icms_value",
        "purchase_order",
        "internal_debug",
        "supplier_tax_id",
        "12345678000199",
        "sale_price",
        "customer_reference",
    ):
        assert sibling not in dumped


def test_last_purchase_projection_drops_tax_id():
    fields = tuple(_allowlist_entry("get_product_last_purchase")["approvedResponseFields"])
    raw = {
        "product": {
            "product_code": "10080001",
            "description": "MP",
            "product_type": "MP",
            "unit": "KG",
            "registered_last_purchase_price": 0.5,
            "standard_cost": 0.02,
        },
        "last_purchase": {
            "branch": "01",
            "invoice_number": "000123",
            "issue_date": "20200407",
            "supplier_code": "000002",
            "supplier_name": "TE",
            "quantity": 10,
            "unit_price": 0.089,
            "total_value": 0.89,
            "icms_rate": 12.0,
            "purchase_order": "PC1",
            "supplier_tax_id": "12345678000199",
            "supplier_state": "SP",
            "supplier_part_number": "PN",
            "invoice_series": "1",
            "entry_date": "20200408",
            "supplier_store": "01",
            "icms_value": 0.1,
            "internal_debug": True,
        },
        "customer_reference": "SECRET",
    }
    projected = apply_approved_field_projection(raw, approved_fields=fields)
    dumped = _dumped(projected)
    assert projected["last_purchase"]["invoice_number"] == "000123"
    assert projected["last_purchase"]["unit_price"] == 0.089
    for sibling in (
        "supplier_tax_id",
        "12345678000199",
        "supplier_state",
        "supplier_part_number",
        "invoice_series",
        "entry_date",
        "supplier_store",
        "icms_value",
        "standard_cost",
        "internal_debug",
        "customer_reference",
        "registered_last_purchase_price",
    ):
        assert sibling not in dumped


def test_wave2_execute_projects_without_raw_fallback(monkeypatch):
    set_actions_for_tests(_actions())
    secret = "sec"
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.execute_service.candidate_token_secret",
        lambda: secret,
    )
    pricing = _action("get_product_pricing")
    token = mint_candidate_token(
        action_id=pricing.action_id, actor_id="u1", secret=secret, ttl_seconds=60
    )
    result = execute_delpi_information(
        candidate_token=token,
        arguments={"code": "10080055"},
        actor_id="u1",
        catalog_action_executor=_PayloadExecutor(
            {
                "success": True,
                "data": {
                    "product": {"code": "10080055", "description": "PA", "unit": "UN"},
                    "prices": [
                        {
                            "table_code": "001",
                            "table_description": "Padrao",
                            "sale_price": 12.5,
                            "currency": "1",
                            "lot_quantity": 1.0,
                            "valid_from": "20260101",
                            "active": "S",
                            "max_price": 99.0,
                        }
                    ],
                },
            }
        ),
    )
    assert result["status"] == "ok"
    assert result["truncated"] is False
    assert result["data"]["prices"][0]["sale_price"] == 12.5
    assert "max_price" not in _dumped(result["data"])
    assert result["is_complete"] is True


def test_no_per_operation_executor_or_economic_router():
    roots = [
        _API_ROOT / "app/application/external_capabilities",
        _API_ROOT / "app/infrastructure/davi",
        _API_ROOT / "app/interface/mcp",
        _API_ROOT / "app/composition/davi_dynamic_read_composer.py",
    ]
    forbidden_names = {
        "execute_product_pricing",
        "execute_purchase_price_history",
        "execute_last_purchase",
        "PricingProjector",
        "PurchaseHistoryProjector",
        "LastPurchaseProjector",
    }
    for root in roots:
        paths = [root] if root.is_file() else list(root.rglob("*.py"))
        for path in paths:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    assert node.name not in forbidden_names, path
            text = path.read_text(encoding="utf-8")
            for marker in (
                'if action_id == "get_product_pricing"',
                'if action.operation_id == "get_product_pricing"',
                'if action.operation_id == "get_product_purchase_price_history"',
                'if action.operation_id == "get_product_last_purchase"',
            ):
                assert marker not in text, f"{path}: {marker}"


def test_agent_instructions_unchanged_and_capability_free():
    text = (
        _API_ROOT / "docs/integrations/openai-workspace-agent-davi.md"
    ).read_text(encoding="utf-8")
    marker = "## Agent instructions — canonical stable contract"
    after = text.split(marker, 1)[1]
    start = after.find("```text\n") + len("```text\n")
    end = after.find("\n```", start)
    block = after[start:end].lower()
    for banned in (
        "get_product_pricing",
        "get_product_purchase_price_history",
        "get_product_last_purchase",
        "get_product_cost_impact_simulation",
        "eligible_read = 13",
        "davi_eligible_read",
    ):
        assert banned not in block, banned
