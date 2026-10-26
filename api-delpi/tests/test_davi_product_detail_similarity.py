"""DAVI — governed product detail for similarity/duplicate analysis (GLPI #530).

TASK: DAVI-PRODUCT-DETAIL-SIMILARITY-001

``get_product_detail`` was classified SEMANTICALLY_REDUNDANT while the detail
route carries ~90 cadastral fields vs the 3-field ``search_products`` slice.
This suite proves the promotion with a fail-closed technical projection:
approved ``product.*`` paths only — financial, fiscal, accounting, commercial,
internal-control and user-identity fields never reach the consumer.

Field status semantics (contract, no runtime map):
  approved + non-null  → FIELD_PRESENT
  approved + null      → FIELD_EMPTY
  not in entity        → FIELD_NOT_AVAILABLE
  not approved         → FIELD_NOT_AUTHORIZED (never projected)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

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
from app.application.external_capabilities.dynamic_information.discover_service import (
    discover_delpi_information,
)
from app.application.external_capabilities.dynamic_information.execute_service import (
    execute_delpi_information,
)
from app.application.external_capabilities.dynamic_information.read_only_intent_guard import (
    clear_read_only_intent_guard_cache,
)
from app.domain.ports.davi_catalog_action_executor_port import (
    CatalogActionExecutionResult,
)

_API_ROOT = Path(__file__).resolve().parents[1]
_DETAIL = "get_product_detail"


@pytest.fixture(autouse=True)
def _reset():
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


class _PayloadExecutor:
    def __init__(self, payload: Any):
        self.payload = payload
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def execute(self, *, action_id: str, validated_arguments: dict[str, Any]):
        self.calls.append((action_id, dict(validated_arguments)))
        return CatalogActionExecutionResult(outcome="ok", payload=self.payload)


def _discover(monkeypatch, query: str):
    set_actions_for_tests(_actions())
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information."
        "discover_service.candidate_token_secret",
        lambda: "sec",
    )
    return discover_delpi_information(query=query, top_k=5, actor_id="u1")


def _token(candidates, action_id: str) -> str:
    return next(
        c["candidate_token"] for c in candidates if c["action_id"] == action_id
    )


def _execute(monkeypatch, token: str, arguments: dict, executor):
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information."
        "execute_service.candidate_token_secret",
        lambda: "sec",
    )
    return execute_delpi_information(
        candidate_token=token,
        arguments=arguments,
        actor_id="u1",
        catalog_action_executor=executor,
    )


# ------------------------- T11 — promotion & discovery -----------------------

def test_detail_promoted_not_blocked():
    allow = load_external_read_allowlist()
    blocked = {
        e.get("operationId")
        for e in allow.get("explicitlyNotApproved") or []
        if isinstance(e, dict)
    }
    assert _DETAIL not in blocked
    action = _action(_DETAIL)
    assert action.executable
    entry = _allowlist_entry(_DETAIL)
    assert entry["executionMode"] == "catalog_action"
    assert entry["approvedInputFields"] == ["code"]
    assert not any("*" in f for f in entry["approvedResponseFields"])


@pytest.mark.parametrize(
    "query",
    [
        "traga o cadastro completo do produto 10080001",
        "ficha técnica do produto 10080001",
        "detalhes do produto 10080001",
        "product detail 10080001",
        "dados cadastrais do produto",
    ],
)
def test_detail_discovery(query, monkeypatch):
    discovered = _discover(monkeypatch, query)
    assert discovered["candidates"], query
    assert discovered["candidates"][0]["action_id"] == _DETAIL, query


def test_mcp_tools_remain_two():
    import asyncio
    from app.interface.mcp.server import create_mcp_server

    tools = asyncio.run(create_mcp_server().list_tools())
    assert [t.name for t in tools] == [
        "discover_delpi_information",
        "execute_delpi_information",
    ]


# ------------- T01/T10/T14 — execute path + fail-closed projection -----------

_FULL_PRODUCT = {
    "success": True,
    "message": "ok",
    "data": {
        "product": {
            "code": "10080001",
            "description": (
                "TERM. BANDEIRA 6,30X0,80 0,50-1,50MM2 "
                "NU S/ISOLACAO FITA ALTURA 16MM UL - ROHS"
            ),
            "type": "MP",
            "group_code": "1008",
            "subgroup": None,
            "previous_code": None,
            "active": "1",
            "blocked": "2",
            "delpi_category": "TERMINAIS",
            "delpi_segment": "COMPONENTES",
            "unit": "PC",
            "secondary_unit": "KG",
            "conversion_factor": 0.012,
            "conversion_type": "M",
            "material_type": None,
            "production_line": None,
            "operation_decimal_type": None,
            "drawing_code": None,
            "current_revision": "03",
            "last_revision_date": "2024-05-10",
            "net_weight": 0.012,
            "package_quantity": 500.0,
            "barcode": None,
            "customer_packaging": "FITA",
            "make_or_buy": "C",
            "default_warehouse": "01",
            "qtd_pi": 0,
            "rohs_indicator": "S",
            "traceability": "N",
            "warranty_product": "N",
            "mrp_considered": "S",
            "power_control": None,
            # ---- non-approved sensitive fields that must never leak ----
            "sale_price": 1.23,
            "standard_cost": 0.87,
            "last_purchase_price": 0.91,
            "last_purchase_date": "2025-01-01",
            "import_expense": 0.05,
            "cost_currency": "BRL",
            "ncm_ipi_position": "8536.90",
            "origin": "0",
            "icms_rate": 18.0,
            "ipi_rate": 9.75,
            "pis_percent": 1.65,
            "cofins_percent": 7.6,
            "accounting_account": "11301",
            "cost_center": "1101",
            "appropriation_type": "M",
            "customer_reference": "CUST-PN-9",
            "customer_reference_old": "CUST-OLD-1",
            "contractual_product": "S",
            "sales_class": "A",
            "lead_time_type": "D",
            "requester_restriction": "N",
            "initial_consumption_date": "2020-01-01",
            "created_by": "jsilva",
            "updated_by": "msouza",
            "mandatory_cc_sc": "S",
            "approval_validation": "N",
            "suggestion_flag": "S",
            "entry_tes": "101",
            "exit_tes": "501",
            "csll_incidence": "2",
            "inss_incidence": "3",
            "retention_by_operation": "N",
            "customs_authority": "RFB",
            "media_product": None,
            "media_quantity": None,
            "intelligent_tes_group": "G1",
            "tax_group": "TG1",
            "imported_product": "N",
            "operation_decimal_type_x": None,
        }
    }
}

_SENSITIVE_KEYS = {
    "sale_price", "standard_cost", "last_purchase_price", "last_purchase_date",
    "import_expense", "cost_currency", "standard_cost_date",
    "cost_reference_date", "ncm_ipi_position", "origin", "imported_product",
    "tax_group", "entry_tes", "exit_tes", "icms_rate", "ipi_rate",
    "pis_incidence", "pis_percent", "cofins_incidence", "cofins_percent",
    "csll_incidence", "inss_incidence", "retention_by_operation",
    "customs_authority", "media_product", "media_quantity",
    "intelligent_tes_group", "accounting_account", "cost_center",
    "appropriation_type", "customer_reference", "customer_reference_old",
    "contractual_product", "sales_class", "lead_time_type",
    "requester_restriction", "initial_consumption_date", "created_by",
    "updated_by", "mandatory_cc_sc", "mandatory_cc_pc", "mandatory_cc_pv",
    "mandatory_cc_mi", "mandatory_cc_nfe", "approval_validation",
    "suggestion_flag", "operation_decimal_type_x",
}


def test_t01_detail_execute_returns_authorized_fields(monkeypatch):
    discovered = _discover(monkeypatch, "cadastro completo do produto 10080001")
    token = _token(discovered["candidates"], _DETAIL)
    result = _execute(
        monkeypatch, token, {"code": "10080001"}, _PayloadExecutor(_FULL_PRODUCT)
    )
    assert result["status"] == "ok"
    product = result["data"]["product"]
    # FIELD_PRESENT — non-null approved fields returned
    assert product["code"] == "10080001"
    assert product["type"] == "MP"
    assert product["unit"] == "PC"
    assert product["secondary_unit"] == "KG"
    assert product["conversion_factor"] == 0.012
    assert product["rohs_indicator"] == "S"
    assert product["make_or_buy"] == "C"
    assert product["package_quantity"] == 500.0
    assert product["current_revision"] == "03"
    assert product["delpi_category"] == "TERMINAIS"
    assert product["previous_code"] is None  # FIELD_EMPTY kept explicit
    # FIELD_NOT_AUTHORIZED — sensitive fields never projected
    assert _SENSITIVE_KEYS.isdisjoint(product)
    flat = json.dumps(result, ensure_ascii=False)
    for forbidden in ("sale_price", "standard_cost", "icms_rate",
                      "accounting_account", "created_by", "customer_reference"):
        assert forbidden not in flat


def test_t02_search_products_projection_unchanged(monkeypatch):
    action = _action("search_products")
    assert action.executable
    assert tuple(action.approved_response_fields) == (
        "product_code", "description", "group_category",
    )


def test_t13_closed_input_schema(monkeypatch):
    discovered = _discover(monkeypatch, "cadastro completo do produto 10080001")
    token = _token(discovered["candidates"], _DETAIL)
    executor = _PayloadExecutor(_FULL_PRODUCT)
    from app.application.external_capabilities.dynamic_information.errors import (
        GovernedExecutionError,
    )

    with pytest.raises(GovernedExecutionError):
        _execute(
            monkeypatch, token,
            {"code": "10080001", "view": "summary", "secret_field": "x"},
            executor,
        )
    # `view` is not an approved input — only `code` may bind
    with pytest.raises(GovernedExecutionError):
        _execute(monkeypatch, token, {"code": "10080001", "view": "summary"}, executor)


def test_t16_code_constraints(monkeypatch):
    discovered = _discover(monkeypatch, "cadastro completo do produto 10080001")
    token = _token(discovered["candidates"], _DETAIL)
    executor = _PayloadExecutor(_FULL_PRODUCT)
    from app.application.external_capabilities.dynamic_information.errors import (
        GovernedExecutionError,
    )

    with pytest.raises(GovernedExecutionError):
        _execute(monkeypatch, token, {"code": "x" * 40}, executor)


def test_t20_negative_authz_executor(monkeypatch):
    discovered = _discover(monkeypatch, "cadastro completo do produto 10080001")
    token = _token(discovered["candidates"], _DETAIL)

    class _Forbidden:
        def execute(self, *, action_id, validated_arguments):
            return CatalogActionExecutionResult(outcome="forbidden", payload=None)

    with pytest.raises(PermissionError):
        _execute(
            monkeypatch, token, {"code": "10080001"}, _Forbidden()
        )


def test_actor_binding_rejects_other_actor(monkeypatch):
    discovered = _discover(monkeypatch, "cadastro completo do produto 10080001")
    token = _token(discovered["candidates"], _DETAIL)
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information."
        "execute_service.candidate_token_secret",
        lambda: "sec",
    )
    from app.application.external_capabilities.dynamic_information.candidate_token import (
        CandidateTokenError,
    )

    with pytest.raises(CandidateTokenError):
        execute_delpi_information(
            candidate_token=token, arguments={"code": "10080001"},
            actor_id="other-user",
            catalog_action_executor=_PayloadExecutor(_FULL_PRODUCT),
        )


# ------------- B — suppliers / part-number ops remain executable -------------

def test_supplier_and_part_number_ops_executable():
    assert _action("get_product_suppliers").executable
    assert _action("search_products_by_supplier_part_number").executable
    entry = _allowlist_entry("search_products_by_supplier_part_number")
    assert "items[].supplier_part_number" in entry["approvedResponseFields"]


@pytest.mark.parametrize(
    "query",
    [
        "part number MS3108E-18-1S",
        "produto com part number do fornecedor MS3108E-18-1S",
        "fornecedores do produto 10080001",
    ],
)
def test_supplier_surface_discovery(query, monkeypatch):
    discovered = _discover(monkeypatch, query)
    ids = {c["action_id"] for c in discovered["candidates"]}
    assert ids & {
        "search_products_by_supplier_part_number",
        "get_product_suppliers",
    }, query


def test_part_number_projection_carries_dedup_evidence():
    """T05/T06 — the part-number projection must carry the fields needed to
    distinguish same-PN products (description + PN), e.g. straight vs 90°
    connectors sharing MS3108E-18-1S (10090850 vs 10090680)."""
    fields = set(_allowlist_entry(
        "search_products_by_supplier_part_number"
    )["approvedResponseFields"])
    assert {
        "items[].product_code",
        "items[].product_description",
        "items[].supplier_part_number",
        "items[].supplier_name",
        "items[].unit",
    } <= fields


# ------------- T17 — existing governed contracts unchanged -------------------

def test_knowledge_and_search_surfaces_unchanged():
    assert _action("read_governed_technical_knowledge").executable
    assert _action("search_products").executable
    assert _action("search_products_by_supplier_part_number").executable
