"""DAVI Wave 1 — operational product intelligence governed READ promotion."""

from __future__ import annotations

import ast
import json
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
_WAVE1 = (
    "get_product_factory_status",
    "get_product_structure_exclusivity",
    "get_product_shipping_status",
)
_CURRENT_SEVEN = (
    "search_products",
    "get_product_stock",
    "get_product_suppliers",
    "get_product_customers",
    "get_product_purchases",
    "get_product_structure",
    "get_product_production_status",
)
_UNKNOWN_ARGS = ("sort", "legacy", "debug", "sql", "url", "operationId", "include_raw")
_INJECTED_SIBLINGS = (
    "secret",
    "internal_debug",
    "raw_sql",
    "unit_price",
    "unexpected",
    "legacy",
    "path",
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
    return next(
        op
        for op in allow["operations"]
        if isinstance(op, dict) and op.get("operationId") == oid
    )


def _dumped(payload: Any) -> str:
    return json.dumps(payload, default=str, ensure_ascii=False)


class _PayloadExecutor:
    def __init__(self, payload: Any):
        self.payload = payload
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def execute(self, *, action_id: str, validated_arguments: dict[str, Any]):
        self.calls.append((action_id, dict(validated_arguments)))
        return CatalogActionExecutionResult(outcome="ok", payload=self.payload)


def test_wave1_eligible_set_remains_and_wave2_added():
    eligible = sorted(a.operation_id for a in _actions() if a.executable)
    assert set(_CURRENT_SEVEN) | set(_WAVE1) <= set(eligible)
    assert len(eligible) == 53
    allow = load_external_read_allowlist()
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
    for oid in (
        "get_product_pricing",
        "get_product_purchase_price_history",
        "get_product_last_purchase",
    ):
        assert oid in set(eligible)
        assert oid not in blocked


def test_wave1_mcp_tools_remain_three():
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
        ("status fabril do produto 10080001", "get_product_factory_status"),
        ("situação fabril do produto", "get_product_factory_status"),
        ("factory status product 10080001", "get_product_factory_status"),
        ("quais MPs são exclusivas no produto 90261805", "get_product_structure_exclusivity"),
        ("matéria-prima exclusiva do produto", "get_product_structure_exclusivity"),
        ("status de expedição do produto", "get_product_shipping_status"),
        ("quantidade expedida do produto", "get_product_shipping_status"),
        ("inspeção final do PA", "get_product_shipping_status"),
        ("produto 10080055", "search_products"),
        ("estoque 10080001", "get_product_stock"),
        ("fornecedores 10080055", "get_product_suppliers"),
        ("clientes 10080055", "get_product_customers"),
        ("compras 10080055", "get_product_purchases"),
        ("estrutura 90261805", "get_product_structure"),
        ("status de produção 10080055", "get_product_production_status"),
    ],
)
def test_wave1_and_current_retrieval(query, expected, monkeypatch):
    set_actions_for_tests(_actions())
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "sec",
    )
    discovered = discover_delpi_information(query=query, top_k=5, actor_id="u1")
    assert discovered["eligible_action_count"] == 53, query
    assert discovered["candidate_count"] >= 1, query
    assert discovered["candidates"][0]["action_id"] == expected, query


@pytest.mark.parametrize(
    ("query", "expected", "forbidden"),
    [
        ("status de produção do produto 10080001", "get_product_production_status", "get_product_factory_status"),
        ("expedição do produto 10080001", "get_product_shipping_status", "get_product_factory_status"),
        ("estrutura do produto 10080001", "get_product_structure", "get_product_factory_status"),
        ("estrutura do produto 90261805", "get_product_structure", "get_product_structure_exclusivity"),
        ("componentes do produto", "get_product_structure", "get_product_structure_exclusivity"),
        ("status de produção", "get_product_production_status", "get_product_shipping_status"),
        ("status fabril", "get_product_factory_status", "get_product_shipping_status"),
        ("status de expedição", "get_product_shipping_status", "get_product_production_status"),
    ],
)
def test_wave1_sibling_disambiguation(query, expected, forbidden, monkeypatch):
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
        "custo do produto",
        "resuma o produto 10080001",
        "execute sql no banco",
        "painel admin do sistema",
        "factory sql",
        "factory admin",
    ],
)
def test_wave1_does_not_unlock_quarantined_intents(query, monkeypatch):
    set_actions_for_tests(_actions())
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "sec",
    )
    discovered = discover_delpi_information(query=query, top_k=5, actor_id="u1")
    assert discovered["candidate_count"] == 0, (query, discovered["candidates"])
    pricing = {
        "get_product_pricing",
        "get_product_purchase_price_history",
        "get_product_raw_material_price_intelligence",
        "get_product_cost_impact_simulation",
        "get_product_summary",
    }
    assert pricing.isdisjoint({c["action_id"] for c in discovered["candidates"]})


def test_factory_quarantine_token_preserved_but_owned_by_aliases(monkeypatch):
    allow = load_external_read_allowlist()
    assert "factory" in {str(t).lower() for t in allow.get("retrievalQuarantineTokens") or []}
    set_actions_for_tests(_actions())
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "sec",
    )
    owned = discover_delpi_information(
        query="factory status do produto 10080001", top_k=5, actor_id="u1"
    )
    assert owned["candidate_count"] >= 1
    assert owned["candidates"][0]["action_id"] == "get_product_factory_status"


def test_wave1_inputs_outputs_and_no_wildcards():
    factory = _allowlist_entry("get_product_factory_status")
    exclusivity = _allowlist_entry("get_product_structure_exclusivity")
    shipping = _allowlist_entry("get_product_shipping_status")
    assert factory["approvedInputFields"] == [
        "code",
        "branch",
        "reference_date",
        "start_date",
        "end_date",
        "max_depth",
    ]
    assert exclusivity["approvedInputFields"] == ["code", "max_depth"]
    assert shipping["approvedInputFields"] == [
        "code",
        "branch",
        "reference_date",
        "start_date",
        "end_date",
    ]
    assert len(factory["approvedResponseFields"]) == 35
    assert len(exclusivity["approvedResponseFields"]) == 19
    assert len(shipping["approvedResponseFields"]) == 15
    for entry in (factory, exclusivity, shipping):
        assert entry["executionMode"] == "catalog_action"
        assert not any("*" in field for field in entry["approvedResponseFields"])
        schema = build_argument_json_schema(_action(entry["operationId"]))
        assert schema["additionalProperties"] is False
        assert "legacy" not in schema["properties"]
        assert "date_start" not in schema["properties"]
        assert "date_end" not in schema["properties"]


@pytest.mark.parametrize("oid", _WAVE1)
@pytest.mark.parametrize("bad", _UNKNOWN_ARGS)
def test_wave1_unknown_arguments_rejected(oid, bad):
    action = _action(oid)
    args: dict[str, Any] = {"code": "10080001"}
    if bad in {"url", "operationId", "sql"}:
        args[bad] = "x"
    else:
        args[bad] = "x"
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, args)


def test_generic_date_range_and_depth_constraints_are_metadata_driven():
    dated = TechnicalAction(
        action_id="synthetic_dated_read",
        operation_id="synthetic_dated_read",
        method="GET",
        path="/synthetic/{code}",
        summary="synthetic dated",
        description="",
        tags=("synthetic",),
        davi_status="DAVI_ELIGIBLE_READ",
        parameters=(
            {"name": "code", "in": "path", "required": True, "type": "string"},
            {"name": "start_date", "in": "query", "required": False, "type": "string"},
            {"name": "end_date", "in": "query", "required": False, "type": "string"},
            {"name": "max_depth", "in": "query", "required": False, "type": "integer"},
        ),
        searchable_text="synthetic dated",
        execution_mode="catalog_action",
        approved_response_fields=("code",),
        approved_input_fields=("code", "start_date", "end_date", "max_depth"),
        argument_constraints={
            "dateRange": {
                "startField": "start_date",
                "endField": "end_date",
                "maxDays": 31,
            },
            "argumentLimits": {"max_depth": {"minimum": 1, "maximum": 8, "default": 8}},
        },
    )
    ok = validate_arguments(
        dated,
        {"code": "X", "start_date": "2026-01-01", "end_date": "2026-02-01"},
    )
    assert ok["start_date"] == "2026-01-01"
    assert validate_arguments(dated, {"code": "X"})["max_depth"] == 8
    with pytest.raises(ArgumentValidationError, match="exceeds 31"):
        validate_arguments(
            dated,
            {"code": "X", "start_date": "2026-01-01", "end_date": "2026-02-02"},
        )
    with pytest.raises(ArgumentValidationError, match="must not be before"):
        validate_arguments(
            dated,
            {"code": "X", "start_date": "2026-02-01", "end_date": "2026-01-31"},
        )
    with pytest.raises(ArgumentValidationError, match="above maximum"):
        validate_arguments(dated, {"code": "X", "max_depth": 9})
    source = (
        _API_ROOT
        / "app/application/external_capabilities/dynamic_information/argument_validator.py"
    ).read_text(encoding="utf-8")
    assert "get_product_factory_status" not in source
    assert "get_product_shipping_status" not in source
    assert "if action_id" not in source
    assert "if action.operation_id" not in source


@pytest.mark.parametrize("oid", ("get_product_factory_status", "get_product_shipping_status"))
def test_wave1_date_interval_and_branch(oid):
    action = _action(oid)
    validate_arguments(
        action, {"code": "10080001", "start_date": "2026-01-01", "end_date": "2026-02-01"}
    )
    with pytest.raises(ArgumentValidationError):
        validate_arguments(
            action,
            {"code": "10080001", "start_date": "2026-01-01", "end_date": "2026-02-02"},
        )
    omitted = validate_arguments(action, {"code": "10080001"})
    assert "start_date" not in omitted
    assert "end_date" not in omitted
    assert validate_arguments(action, {"code": "X", "branch": "all"})["branch"] == "all"
    assert validate_arguments(action, {"code": "X", "branch": "01"})["branch"] == "01"
    assert validate_arguments(action, {"code": "X", "branch": "02"})["branch"] == "02"
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, {"code": "X", "branch": "03"})
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, {"code": "X", "branch": "ALL"})


@pytest.mark.parametrize(
    "oid", ("get_product_factory_status", "get_product_structure_exclusivity")
)
def test_wave1_max_depth_eight(oid):
    action = _action(oid)
    assert validate_arguments(action, {"code": "X", "max_depth": 8})["max_depth"] == 8
    assert validate_arguments(action, {"code": "X"})["max_depth"] == 8
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, {"code": "X", "max_depth": 9})


def test_factory_projection_drops_item_arrays_and_unknown_siblings():
    fields = tuple(_allowlist_entry("get_product_factory_status")["approvedResponseFields"])
    raw = {
        "product": {
            "product_code": "10080001",
            "description": "PA",
            "product_type": "PA",
            "unit": "UN",
            "group_code": "G1",
            "secret": 1,
        },
        "reference_date": "2026-09-17",
        "start_date": "2026-09-17",
        "factory_status": "em_producao",
        "indicators": {
            "total_intermediates": 2,
            "total_raw_materials": 4,
            "total_exclusive_raw_materials": 1,
            "total_raw_materials_without_stock_for_one_pa": 0,
            "max_pa_producible_from_stock": 10,
            "limiting_raw_material_code": "MP1",
            "total_pa_orders": 1,
            "total_pi_orders": 0,
            "total_pa_reported_quantity": 5,
            "total_pi_reported_quantity": 0,
            "total_pa_shipped_quantity": 3,
            "total_inspection_loss_quantity": 0.5,
            "raw_sql": "SELECT 1",
        },
        "structure": {
            "summary": {
                "total_components": 6,
                "total_intermediates": 2,
                "total_raw_materials": 4,
                "total_exclusive_raw_materials": 1,
            },
            "items": [{"component_code": "MP1", "unit_price": 9}],
        },
        "raw_material_stock": {
            "summary": {
                "total_raw_materials": 4,
                "total_without_stock_for_one_pa": 0,
                "max_pa_producible_from_stock": 10,
                "limiting_raw_material_code": "MP1",
            },
            "items": [{"code": "MP1", "internal_debug": True}],
        },
        "production": {
            "summary": {
                "total_pa_orders": 1,
                "total_pi_orders": 0,
                "pa_production_started": True,
                "pi_production_started": False,
            },
            "items": [{"production_order": "OP1"}],
        },
        "shipping": {
            "summary": {
                "total_shipped_quantity": 3,
                "total_inspection_loss_quantity": 0.5,
                "total_reports": 2,
            },
            "items": [{"shipped_quantity": 3}],
        },
        "unexpected": True,
        "legacy": "x",
        "path": "/internal",
    }
    projected = apply_approved_field_projection(raw, approved_fields=fields)
    dumped = _dumped(projected)
    assert projected["factory_status"] == "em_producao"
    assert projected["indicators"]["total_pa_shipped_quantity"] == 3
    assert projected["shipping"]["summary"]["total_reports"] == 2
    assert "items" not in projected.get("structure", {})
    assert "items" not in projected.get("raw_material_stock", {})
    assert "items" not in projected.get("production", {})
    assert "items" not in projected.get("shipping", {})
    for sibling in _INJECTED_SIBLINGS:
        assert sibling not in projected
        assert f'"{sibling}"' not in dumped


def test_exclusivity_projection_drops_path_legacy_and_unknowns():
    fields = tuple(
        _allowlist_entry("get_product_structure_exclusivity")["approvedResponseFields"]
    )
    raw = {
        "product": {
            "product_code": "90261805",
            "description": "PA",
            "product_type": "PA",
            "unit": "UN",
            "secret": 1,
        },
        "items": [
            {
                "level": 1,
                "parent_code": "90261805",
                "parent_description": "PA",
                "component_code": "MP1",
                "component_description": "Steel",
                "component_type": "MP",
                "component_unit": "KG",
                "quantity_per": 2,
                "accumulated_quantity": 2,
                "exclusive_raw_material": True,
                "total_valid_finished_products_using_mp": 1,
                "path": "90261805/MP1",
                "legacy": "SIM",
                "unit_price": 12,
                "internal_debug": True,
            }
        ],
        "summary": {
            "total_components": 1,
            "total_intermediates": 0,
            "total_raw_materials": 1,
            "total_exclusive_raw_materials": 1,
            "raw_sql": "nope",
        },
        "unexpected": True,
    }
    projected = apply_approved_field_projection(raw, approved_fields=fields)
    item = projected["items"][0]
    assert item["exclusive_raw_material"] is True
    assert item["total_valid_finished_products_using_mp"] == 1
    assert projected["summary"]["total_exclusive_raw_materials"] == 1
    dumped = _dumped(projected)
    for sibling in ("path", "legacy", "unit_price", "internal_debug", "raw_sql", "secret"):
        assert sibling not in item
        assert sibling not in projected
        assert f'"{sibling}"' not in dumped


def test_shipping_projection_drops_raw_and_unknown_fields():
    fields = tuple(_allowlist_entry("get_product_shipping_status")["approvedResponseFields"])
    raw = {
        "product": {
            "product_code": "10080001",
            "description": "PA",
            "product_type": "PA",
            "unit": "UN",
        },
        "start_date": "2026-09-17",
        "items": [
            {
                "branch": "01",
                "product_code": "10080001",
                "production_order": "OP1",
                "work_center": "WC1",
                "shipped_quantity": 8,
                "inspection_loss_quantity": 0.2,
                "total_reports": 3,
                "sh6_raw": 1,
                "shb_raw": 2,
                "unexpected": True,
            }
        ],
        "summary": {
            "total_shipped_quantity": 8,
            "total_inspection_loss_quantity": 0.2,
            "total_reports": 3,
        },
        "legacy": True,
        "secret": 9,
    }
    projected = apply_approved_field_projection(raw, approved_fields=fields)
    item = projected["items"][0]
    assert item["shipped_quantity"] == 8
    assert item["inspection_loss_quantity"] == 0.2
    assert item["total_reports"] == 3
    dumped = _dumped(projected)
    for sibling in ("sh6_raw", "shb_raw", "unexpected", "legacy", "secret"):
        assert sibling not in item
        assert sibling not in projected
        assert f'"{sibling}"' not in dumped


def test_factory_execute_preserves_business_values_without_raw_fallback(monkeypatch):
    action = _action("get_product_factory_status")
    set_actions_for_tests(_actions())
    secret = "sec"
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.execute_service.candidate_token_secret",
        lambda: secret,
    )
    token = mint_candidate_token(
        action_id=action.action_id, actor_id="u1", secret=secret, ttl_seconds=60
    )
    payload = {
        "success": True,
        "data": {
            "product": {
                "product_code": "10080001",
                "description": "PA",
                "product_type": "PA",
                "unit": "UN",
                "group_code": "G1",
            },
            "reference_date": "2026-09-17",
            "start_date": "2026-09-17",
            "factory_status": "liberado_expedicao",
            "indicators": {
                "total_intermediates": 2,
                "total_raw_materials": 4,
                "total_exclusive_raw_materials": 1,
                "total_raw_materials_without_stock_for_one_pa": 0,
                "max_pa_producible_from_stock": 10,
                "limiting_raw_material_code": "MP1",
                "total_pa_orders": 1,
                "total_pi_orders": 0,
                "total_pa_reported_quantity": 5,
                "total_pi_reported_quantity": 0,
                "total_pa_shipped_quantity": 3,
                "total_inspection_loss_quantity": 0.5,
            },
            "structure": {
                "summary": {
                    "total_components": 6,
                    "total_intermediates": 2,
                    "total_raw_materials": 4,
                    "total_exclusive_raw_materials": 1,
                },
                "items": [{"component_code": "hidden"}],
            },
            "raw_material_stock": {
                "summary": {
                    "total_raw_materials": 4,
                    "total_without_stock_for_one_pa": 0,
                    "max_pa_producible_from_stock": 10,
                    "limiting_raw_material_code": "MP1",
                },
                "items": [{"code": "hidden"}],
            },
            "production": {
                "summary": {
                    "total_pa_orders": 1,
                    "total_pi_orders": 0,
                    "pa_production_started": True,
                    "pi_production_started": False,
                },
                "items": [{"production_order": "hidden"}],
            },
            "shipping": {
                "summary": {
                    "total_shipped_quantity": 3,
                    "total_inspection_loss_quantity": 0.5,
                    "total_reports": 2,
                },
                "items": [{"shipped_quantity": 3}],
            },
        },
    }
    result = execute_delpi_information(
        candidate_token=token,
        arguments={"code": "10080001"},
        actor_id="u1",
        catalog_action_executor=_PayloadExecutor(payload),
    )
    data = result["data"]
    assert result["status"] == "ok"
    assert result["truncated"] is False
    assert data["factory_status"] == "liberado_expedicao"
    assert data["indicators"]["max_pa_producible_from_stock"] == 10
    assert "items" not in data.get("structure", {})
    assert "hidden" not in _dumped(data)


def test_exclusivity_and_shipping_truncation_and_business_values(monkeypatch):
    set_actions_for_tests(_actions())
    secret = "sec"
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.execute_service.candidate_token_secret",
        lambda: secret,
    )
    exclusivity = _action("get_product_structure_exclusivity")
    token = mint_candidate_token(
        action_id=exclusivity.action_id, actor_id="u1", secret=secret, ttl_seconds=60
    )
    items = []
    for idx in range(51):
        items.append(
            {
                "level": 1,
                "parent_code": "90261805",
                "parent_description": "PA",
                "component_code": f"MP{idx}",
                "component_description": "Steel",
                "component_type": "MP",
                "component_unit": "KG",
                "quantity_per": 1,
                "accumulated_quantity": 1,
                "exclusive_raw_material": idx == 0,
                "total_valid_finished_products_using_mp": 1 if idx == 0 else 4,
                "path": "internal",
            }
        )
    result = execute_delpi_information(
        candidate_token=token,
        arguments={"code": "90261805"},
        actor_id="u1",
        catalog_action_executor=_PayloadExecutor(
            {
                "product": {
                    "product_code": "90261805",
                    "description": "PA",
                    "product_type": "PA",
                    "unit": "UN",
                },
                "items": items,
                "summary": {
                    "total_components": 51,
                    "total_intermediates": 0,
                    "total_raw_materials": 51,
                    "total_exclusive_raw_materials": 1,
                },
            }
        ),
    )
    assert result["truncated"] is True
    assert result["is_complete"] is False
    assert len(result["data"]["items"]) == 50
    assert result["data"]["items"][0]["exclusive_raw_material"] is True
    assert result["data"]["summary"]["total_exclusive_raw_materials"] == 1
    assert "path" not in result["data"]["items"][0]

    shipping = _action("get_product_shipping_status")
    token_s = mint_candidate_token(
        action_id=shipping.action_id, actor_id="u1", secret=secret, ttl_seconds=60
    )
    ship_items = [
        {
            "branch": "01",
            "product_code": "10080001",
            "production_order": f"OP{idx}",
            "work_center": "WC1",
            "shipped_quantity": 2,
            "inspection_loss_quantity": 0.1,
            "total_reports": 1,
            "sh6_raw": True,
        }
        for idx in range(51)
    ]
    ship_result = execute_delpi_information(
        candidate_token=token_s,
        arguments={"code": "10080001"},
        actor_id="u1",
        catalog_action_executor=_PayloadExecutor(
            {
                "product": {
                    "product_code": "10080001",
                    "description": "PA",
                    "product_type": "PA",
                    "unit": "UN",
                },
                "start_date": "2026-09-17",
                "items": ship_items,
                "summary": {
                    "total_shipped_quantity": 102,
                    "total_inspection_loss_quantity": 5.1,
                    "total_reports": 51,
                },
            }
        ),
    )
    assert ship_result["truncated"] is True
    assert ship_result["is_complete"] is False
    assert len(ship_result["data"]["items"]) == 50
    assert ship_result["data"]["items"][0]["shipped_quantity"] == 2
    assert ship_result["data"]["summary"]["total_shipped_quantity"] == 102
    assert "sh6_raw" not in ship_result["data"]["items"][0]


def test_no_per_operation_executor_or_router():
    roots = [
        _API_ROOT / "app/application/external_capabilities",
        _API_ROOT / "app/infrastructure/davi",
        _API_ROOT / "app/interface/mcp",
        _API_ROOT / "app/composition/davi_dynamic_read_composer.py",
    ]
    forbidden_names = {
        "execute_factory_status",
        "execute_shipping_status",
        "execute_structure_exclusivity",
        "factory_runner",
        "shipping_runner",
        "exclusivity_runner",
        "FactoryStatusProjector",
        "ShippingStatusProjector",
        "StructureExclusivityProjector",
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
                "execute_factory_status",
                "execute_shipping_status",
                "execute_structure_exclusivity",
                "factory_runner",
                "shipping_runner",
                "exclusivity_runner",
                "FactoryStatusProjector",
                "ShippingStatusProjector",
                "StructureExclusivityProjector",
                'if action_id == "get_product_factory_status"',
                "if action_id == 'get_product_factory_status'",
                'if action.operation_id == "get_product_factory_status"',
                'if action.operation_id == "get_product_shipping_status"',
                'if action.operation_id == "get_product_structure_exclusivity"',
            ):
                assert marker not in text, f"{path}: {marker}"
