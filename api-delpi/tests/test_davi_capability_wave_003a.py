"""DAVI Wave 3A — governed product routing + where-used READ promotion."""

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
_WAVE3A = ("get_product_guide", "get_product_parents")
_CURRENT_THIRTEEN = (
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
)
_UNKNOWN_ARGS = (
    "sql",
    "url",
    "path",
    "method",
    "operationId",
    "legacy",
    "debug",
    "sort",
    "direction",
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


def test_wave3a_eligible_count_includes_wave3a_ops():
    eligible = sorted(a.operation_id for a in _actions() if a.executable)
    assert len(eligible) == 17
    assert set(_CURRENT_THIRTEEN) | set(_WAVE3A) <= set(eligible)
    assert {"list_product_drawings", "get_product_drawing"} <= set(eligible)
    allow = load_external_read_allowlist()
    assert allow.get("version") == 9
    assert "get_product_raw_material_set_shortages" not in set(eligible)
    blocked = {
        item.get("operationId")
        for item in allow.get("explicitlyNotApproved") or []
        if isinstance(item, dict)
    }
    assert "get_product_cost_impact_simulation" in blocked
    assert "get_product_guide" not in blocked
    assert "get_product_parents" not in blocked
    assert "get_product_drawing_pdf" in blocked
    assert "get_product_analyser" in blocked


def test_wave3a_mcp_tools_remain_three():
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
        ("roteiro do produto 90261805", "get_product_guide"),
        ("operações do produto 90261805", "get_product_guide"),
        ("sequência de operações do produto 90261805", "get_product_guide"),
        ("centros de trabalho do produto 90261805", "get_product_guide"),
        ("onde o 10080055 é usado", "get_product_parents"),
        ("onde a MP 10080055 é usada", "get_product_parents"),
        ("quais PAs usam 10080055", "get_product_parents"),
        ("BOM reversa do 10080055", "get_product_parents"),
        ("produto 10080055", "search_products"),
        ("estoque 10080001", "get_product_stock"),
        ("fornecedores 10080055", "get_product_suppliers"),
        ("clientes do produto", "get_product_customers"),
        ("compras do produto", "get_product_purchases"),
        ("estrutura do produto 90261805", "get_product_structure"),
        ("status de produção 10080055", "get_product_production_status"),
        ("status fabril do produto", "get_product_factory_status"),
        ("MP exclusiva", "get_product_structure_exclusivity"),
        ("expedição", "get_product_shipping_status"),
        ("preço comercial do produto 10080055", "get_product_pricing"),
        ("histórico de preço de compra", "get_product_purchase_price_history"),
        ("último preço de compra", "get_product_last_purchase"),
    ],
)
def test_wave3a_and_current_thirteen_retrieval(query, expected, monkeypatch):
    set_actions_for_tests(_actions())
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "sec",
    )
    discovered = discover_delpi_information(query=query, top_k=5, actor_id="u1")
    assert discovered["eligible_action_count"] == 17, query
    assert discovered["candidate_count"] >= 1, query
    assert discovered["candidates"][0]["action_id"] == expected, (
        query,
        [c["action_id"] for c in discovered["candidates"]],
    )


@pytest.mark.parametrize(
    ("query", "expected", "forbidden"),
    [
        ("roteiro do produto", "get_product_guide", "get_product_structure"),
        ("sequência de operações", "get_product_guide", "get_product_production_status"),
        ("onde o produto é usado", "get_product_parents", "get_product_structure"),
        ("quais PAs usam esta MP", "get_product_parents", "get_product_structure_exclusivity"),
        ("estrutura do produto", "get_product_structure", "get_product_parents"),
        ("MP exclusiva", "get_product_structure_exclusivity", "get_product_parents"),
        ("status de produção", "get_product_production_status", "get_product_guide"),
        ("status fabril", "get_product_factory_status", "get_product_guide"),
    ],
)
def test_wave3a_collision_disambiguation(query, expected, forbidden, monkeypatch):
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
        "sql",
        "admin",
        "inteligência de preço de matéria-prima",
        "simulação de custo",
    ],
)
def test_wave3a_quarantine_regression(query, monkeypatch):
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
        "altere o roteiro do produto",
        "adicione uma operação ao roteiro",
        "mude o centro de trabalho do produto",
        "edite a sequência de operações",
        "altere os produtos pai",
        "mude onde esta MP é usada",
        "corrija a BOM reversa",
        "edite a estrutura desse componente",
        "reserve matéria-prima",
        "reprograme a OP",
    ],
)
def test_wave3a_write_intent_returns_zero(query, monkeypatch):
    set_actions_for_tests(_actions())
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "sec",
    )
    discovered = discover_delpi_information(query=query, top_k=5, actor_id="u1")
    assert discovered["candidate_count"] == 0, (query, discovered["candidates"])


def test_wave3a_inputs_outputs_and_constraints():
    guide = _allowlist_entry("get_product_guide")
    parents = _allowlist_entry("get_product_parents")
    assert guide["approvedInputFields"] == [
        "code",
        "branch",
        "page",
        "page_size",
        "max_depth",
    ]
    assert parents["approvedInputFields"] == ["code", "max_depth", "page", "page_size"]
    assert len(guide["approvedResponseFields"]) == 15
    assert len(parents["approvedResponseFields"]) == 25
    assert not any("*" in f for f in guide["approvedResponseFields"])
    assert not any("*" in f for f in parents["approvedResponseFields"])
    assert guide["executionMode"] == parents["executionMode"] == "catalog_action"

    guide_limits = guide["argumentConstraints"]["argumentLimits"]
    assert guide_limits["max_depth"] == {"minimum": 1, "maximum": 8, "default": 8}
    assert guide_limits["page"]["default"] == 1
    assert guide_limits["page_size"] == {"minimum": 1, "maximum": 50, "default": 50}

    parents_limits = parents["argumentConstraints"]["argumentLimits"]
    assert parents_limits["max_depth"] == {"minimum": 1, "maximum": 4, "default": 4}
    assert parents_limits["page"]["default"] == 1
    assert parents_limits["page_size"] == {"minimum": 1, "maximum": 50, "default": 50}

    nested_paths = [
        f for f in parents["approvedResponseFields"] if f.startswith("items[].parents")
    ]
    assert max(p.count("parents[]") for p in nested_paths) == 3  # 4 visible levels total


def test_routing_defaults_and_depth_bounds():
    action = _action("get_product_guide")
    omitted = validate_arguments(action, {"code": "90261805"})
    assert omitted["page"] == 1
    assert omitted["page_size"] == 50
    assert omitted["max_depth"] == 8
    assert validate_arguments(action, {"code": "X", "max_depth": 1})["max_depth"] == 1
    assert validate_arguments(action, {"code": "X", "max_depth": 8})["max_depth"] == 8
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, {"code": "X", "max_depth": 9})
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, {"code": "X", "page_size": 51})
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, {"code": "X", "page": 0})
    assert validate_arguments(action, {"code": "X", "branch": "all"})["branch"] == "all"
    assert validate_arguments(action, {"code": "X", "branch": "01"})["branch"] == "01"
    assert validate_arguments(action, {"code": "X", "branch": "02"})["branch"] == "02"
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, {"code": "X", "branch": "03"})


def test_where_used_defaults_and_depth_invariant():
    action = _action("get_product_parents")
    omitted = validate_arguments(action, {"code": "10080055"})
    assert omitted["page"] == 1
    assert omitted["page_size"] == 50
    assert omitted["max_depth"] == 4
    assert validate_arguments(action, {"code": "X", "max_depth": 1})["max_depth"] == 1
    assert validate_arguments(action, {"code": "X", "max_depth": 4})["max_depth"] == 4
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, {"code": "X", "max_depth": 5})
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, {"code": "X", "page_size": 51})
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, {"code": "X", "page": 0})
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, {"code": "X", "branch": "01"})
    schema = build_argument_json_schema(action)
    assert "branch" not in schema["properties"]
    assert schema["properties"]["max_depth"]["maximum"] == 4
    assert schema["properties"]["max_depth"]["default"] == 4
    assert schema["additionalProperties"] is False


@pytest.mark.parametrize("oid", _WAVE3A)
@pytest.mark.parametrize("bad", _UNKNOWN_ARGS)
def test_wave3a_unknown_arguments_rejected(oid, bad):
    action = _action(oid)
    args: dict[str, Any] = {"code": "10080001"}
    args[bad] = "x"
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, args)


def test_no_operation_specific_validator_branches():
    source = (
        _API_ROOT
        / "app/application/external_capabilities/dynamic_information/argument_validator.py"
    ).read_text(encoding="utf-8")
    assert "get_product_guide" not in source
    assert "get_product_parents" not in source
    assert "if action.operation_id" not in source


def _guide_raw_fixture() -> dict[str, Any]:
    return {
        "items": [
            {
                "branch": "01",
                "route_code": "R1",
                "product_code": "90261805",
                "operation_code": "10",
                "operation_description": "Corte",
                "resource_code": "RES1",
                "work_center": "CT01",
                "setup_hours": 0.5,
                "standard_time_hours_piece": 0.1,
                "standard_time_minutes_piece": 6.0,
                "operation_type": "P",
                "component_code": "MP1",
                "component_description": "Chapa",
                "component_sequence": 1,
                "bom_level": 0,
                "standard_time_hour_mil": 100,
                "mandatory_operation": True,
                "mandatory_sequence": True,
                "mandatory_report": False,
                "internal_debug": True,
            },
            {
                "branch": "01",
                "route_code": "R1",
                "product_code": "90261805",
                "operation_code": "20",
                "operation_description": "Solda",
                "resource_code": "RES2",
                "work_center": "CT02",
                "setup_hours": 0.2,
                "standard_time_hours_piece": 0.2,
                "standard_time_minutes_piece": 12.0,
                "operation_type": "P",
                "component_code": None,
                "component_description": None,
                "component_sequence": None,
                "bom_level": 0,
            },
        ],
        "page": 1,
        "page_size": 50,
        "total": 2,
        "total_pages": 1,
        "raw_sql": "SELECT 1",
        "customer_reference": "SECRET",
        "unexpected": True,
    }


def _parents_raw_fixture() -> dict[str, Any]:
    level5 = {
        "code": "L5",
        "description": "hidden",
        "type": "PA",
        "unit": "UN",
        "quantity": 1.0,
        "parents": [],
        "raw_sql": "SELECT",
        "record_id": 99,
        "internal_debug": True,
        "legacy": True,
        "secret": "x",
    }
    level4 = {
        "code": "L4",
        "description": "PA4",
        "type": "PA",
        "unit": "UN",
        "quantity": 1.0,
        "parents": [level5],
        "raw_sql": "SELECT",
    }
    level3 = {
        "code": "L3",
        "description": "PA3",
        "type": "PA",
        "unit": "UN",
        "quantity": 1.0,
        "parents": [level4],
    }
    level2 = {
        "code": "L2",
        "description": "PI2",
        "type": "PI",
        "unit": "UN",
        "quantity": 2.0,
        "parents": [level3],
    }
    level1 = {
        "code": "L1",
        "description": "PA1",
        "type": "PA",
        "unit": "UN",
        "quantity": 3.0,
        "parents": [level2],
        "secret": "nope",
    }
    return {
        "root": {
            "code": "10080055",
            "description": "MP",
            "type": "MP",
            "unit": "KG",
            "quantity": 1.0,
            "internal_debug": True,
        },
        "items": [level1],
        "page": 1,
        "page_size": 50,
        "total": 1,
        "total_pages": 1,
        "raw_sql": "SELECT *",
        "legacy": True,
    }


def test_routing_projection_drops_forbidden_siblings():
    fields = tuple(_allowlist_entry("get_product_guide")["approvedResponseFields"])
    projected = apply_approved_field_projection(_guide_raw_fixture(), approved_fields=fields)
    dumped = _dumped(projected)
    assert projected["items"][0]["operation_code"] == "10"
    assert projected["items"][0]["work_center"] == "CT01"
    assert projected["items"][0]["standard_time_hours_piece"] == 0.1
    assert projected["items"][0]["standard_time_minutes_piece"] == 6.0
    for sibling in (
        "standard_time_hour_mil",
        "mandatory_operation",
        "mandatory_sequence",
        "mandatory_report",
        "internal_debug",
        "raw_sql",
        "customer_reference",
        "unexpected",
    ):
        assert sibling not in dumped


def test_where_used_projection_four_levels_and_drops_forbidden():
    fields = tuple(_allowlist_entry("get_product_parents")["approvedResponseFields"])
    projected = apply_approved_field_projection(
        _parents_raw_fixture(), approved_fields=fields
    )
    dumped = _dumped(projected)
    assert projected["root"]["code"] == "10080055"
    item = projected["items"][0]
    assert item["code"] == "L1"
    assert item["parents"][0]["code"] == "L2"
    assert item["parents"][0]["parents"][0]["code"] == "L3"
    assert item["parents"][0]["parents"][0]["parents"][0]["code"] == "L4"
    # fifth level not in approved paths — dropped
    deepest = item["parents"][0]["parents"][0]["parents"][0]
    assert "parents" not in deepest or deepest.get("parents") in (None, [], {})
    for sibling in ("raw_sql", "record_id", "internal_debug", "legacy", "secret"):
        assert sibling not in dumped
    assert "L5" not in dumped


def test_wave3a_execute_projects_without_raw_fallback(monkeypatch):
    set_actions_for_tests(_actions())
    secret = "sec"
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.execute_service.candidate_token_secret",
        lambda: secret,
    )
    guide = _action("get_product_guide")
    token = mint_candidate_token(
        action_id=guide.action_id, actor_id="u1", secret=secret, ttl_seconds=60
    )
    executor = _PayloadExecutor({"success": True, "data": _guide_raw_fixture()})
    result = execute_delpi_information(
        candidate_token=token,
        arguments={"code": "90261805"},
        actor_id="u1",
        catalog_action_executor=executor,
    )
    assert result["status"] == "ok"
    assert executor.calls[0][1]["page"] == 1
    assert executor.calls[0][1]["page_size"] == 50
    assert executor.calls[0][1]["max_depth"] == 8
    assert "mandatory_operation" not in _dumped(result["data"])

    parents = _action("get_product_parents")
    token_p = mint_candidate_token(
        action_id=parents.action_id, actor_id="u1", secret=secret, ttl_seconds=60
    )
    executor_p = _PayloadExecutor({"success": True, "data": _parents_raw_fixture()})
    result_p = execute_delpi_information(
        candidate_token=token_p,
        arguments={"code": "10080055"},
        actor_id="u1",
        catalog_action_executor=executor_p,
    )
    assert result_p["status"] == "ok"
    assert executor_p.calls[0][1]["max_depth"] == 4
    assert "L5" not in _dumped(result_p["data"])
    assert "secret" not in _dumped(result_p["data"])


def test_shortages_not_executable():
    eligible = {a.operation_id for a in _actions() if a.executable}
    assert "get_product_raw_material_set_shortages" not in eligible
    allow = load_external_read_allowlist()
    ids = {o["operationId"] for o in allow["operations"]}
    assert "get_product_raw_material_set_shortages" not in ids


def test_no_per_operation_executor_or_wave3a_router():
    roots = [
        _API_ROOT / "app/application/external_capabilities",
        _API_ROOT / "app/infrastructure/davi",
        _API_ROOT / "app/interface/mcp",
        _API_ROOT / "app/composition/davi_dynamic_read_composer.py",
    ]
    forbidden_names = {
        "execute_product_guide",
        "execute_product_parents",
        "GuideProjector",
        "ParentsProjector",
        "WhereUsedProjector",
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
                'if action_id == "get_product_guide"',
                'if action.operation_id == "get_product_guide"',
                'if action.operation_id == "get_product_parents"',
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
        "get_product_guide",
        "get_product_parents",
        "get_product_raw_material_set_shortages",
        "roteiro",
        "where-used",
        "where used",
        "eligible_read = 15",
        "davi_eligible_read",
    ):
        assert banned not in block, banned
