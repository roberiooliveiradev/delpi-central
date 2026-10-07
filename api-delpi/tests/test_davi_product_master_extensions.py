"""DAVI Product Master extensions — frozen promotion coverage (POS-01..POS-09).

Exercises the productive catalog path: real allowlist + live OpenAPI →
TechnicalAction → retrieval/discovery → candidate token → validated arguments →
catalog-fixed executor → approved projection. No DAVI-local AuthZ is added or
asserted; backend denial stays a governed outcome.
"""

from __future__ import annotations

import json
from functools import lru_cache
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
    CandidateTokenError,
    mint_candidate_token,
    parse_candidate_token,
)
from app.application.external_capabilities.dynamic_information.catalog_builder import (
    TechnicalAction,
    build_technical_actions_from_baseline,
    build_technical_actions_from_openapi,
)
from app.application.external_capabilities.dynamic_information.constants import (
    SEMANTIC_TRANSPORT_READ_POST,
    STATUS_DAVI_ELIGIBLE_READ,
    STATUS_NEEDS_BOUNDED_EXECUTION,
)
from app.application.external_capabilities.dynamic_information.content_loader import (
    load_external_read_allowlist,
)
from app.application.external_capabilities.dynamic_information.discover_service import (
    discover_delpi_information,
)
from app.application.external_capabilities.dynamic_information.execute_service import (
    execute_delpi_information,
)
from app.application.external_capabilities.dynamic_information.retrieval import (
    retrieve_eligible_actions,
)
from app.infrastructure.davi.asgi_catalog_action_executor import (
    AsgiCatalogActionExecutor,
)

_ACTOR = "11111111-1111-4111-8111-111111111111"
_OTHER_ACTOR = "22222222-2222-4222-8222-222222222222"
_SECRET = "test-secret-davi-product-master-ext"
_API_ROOT = Path(__file__).resolve().parents[1]

PROMOTED_GET = {
    "search_products_by_supplier_part_number",
    "list_exclusive_raw_materials_catalog",
    "get_product_internal_movements",
    "get_product_inbound_invoice_items",
    "get_product_outbound_invoice_items",
    "get_product_sales_summary",
    "get_product_sales_open_orders",
}
PROMOTED_POST = {
    "list_product_physical_locations",
    "list_product_inventory_blocks",
}
PROMOTED = PROMOTED_GET | PROMOTED_POST
# get_product_raw_material_set_shortages was not promoted at this wave and
# was later approved by
# DAVI-INVENTORY-MATERIAL-FLOW-IMPLEMENTATION-001 (allowlist v18).
NOT_PROMOTED = {
    "get_product_sales_billing",
    "get_product_directives",
    "get_product_purchase_budget_history",
}


@lru_cache(maxsize=1)
def _openapi() -> dict[str, Any]:
    from app.main import app

    return app.openapi()


@lru_cache(maxsize=1)
def _actions() -> list[TechnicalAction]:
    return build_technical_actions_from_openapi(
        _openapi(), allowlist=load_external_read_allowlist()
    )


def _baseline_actions() -> list[TechnicalAction]:
    baseline = json.loads(
        (_API_ROOT / "app/content/openapi_baseline.json").read_text(encoding="utf-8")
    )
    return build_technical_actions_from_baseline(
        baseline, allowlist=load_external_read_allowlist()
    )


def _action(oid: str) -> TechnicalAction:
    return next(a for a in _actions() if a.operation_id == oid)


@pytest.fixture(autouse=True)
def _reset_index():
    reset_action_index_for_tests()
    load_external_read_allowlist.cache_clear()
    yield
    reset_action_index_for_tests()
    load_external_read_allowlist.cache_clear()


@pytest.fixture
def _seeded(monkeypatch):
    set_actions_for_tests(_actions())
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information."
        "discover_service.candidate_token_secret",
        lambda: _SECRET,
    )
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information."
        "execute_service.candidate_token_secret",
        lambda: _SECRET,
    )
    return True


class _FakeResponse:
    def __init__(self, status_code: int, body: Any):
        self.status_code = status_code
        self._body = body
        self.text = json.dumps(body, ensure_ascii=False)

    def json(self):
        return self._body


class _FakeClient:
    def __init__(self, response: _FakeResponse):
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def get(self, path, *, params=None, headers=None):
        self.calls.append(
            {"verb": "get", "path": path, "params": params, "headers": headers}
        )
        return self.response

    def post(self, path, *, json=None, params=None, headers=None):
        self.calls.append(
            {
                "verb": "post",
                "path": path,
                "json": json,
                "params": params,
                "headers": headers,
            }
        )
        return self.response


def _mint(action_id: str, actor_id: str = _ACTOR) -> str:
    return mint_candidate_token(
        action_id=action_id, actor_id=actor_id, secret=_SECRET, ttl_seconds=120
    )


def _execute(
    oid: str,
    arguments: dict[str, Any] | None,
    *,
    actor_id: str = _ACTOR,
    owner_payload: Any,
    status: int = 200,
) -> tuple[dict[str, Any], _FakeClient]:
    """End-to-end: token → validated args → real catalog executor → projection."""
    client = _FakeClient(
        _FakeResponse(status, {"success": True, "data": owner_payload})
    )
    executor = AsgiCatalogActionExecutor(client, authorization="Bearer end-user")
    result = execute_delpi_information(
        candidate_token=_mint(oid, actor_id=actor_id),
        arguments=arguments,
        actor_id=actor_id,
        catalog_action_executor=executor,
    )
    return result, client


# ---------------------------------------------------------------------------
# Promotion invariants
# ---------------------------------------------------------------------------


def test_allowlist_v17_promotes_exactly_nine_operations() -> None:
    allow = load_external_read_allowlist()
    assert allow.get("version") >= 17
    ids = {e["operationId"] for e in allow["operations"]}
    assert len(ids) >= 77
    assert PROMOTED <= ids
    for oid in PROMOTED_POST:
        entry = next(e for e in allow["operations"] if e["operationId"] == oid)
        assert entry.get("semanticTransport") == SEMANTIC_TRANSPORT_READ_POST
    for oid in PROMOTED:
        entry = next(e for e in allow["operations"] if e["operationId"] == oid)
        assert entry.get("executionMode") == "catalog_action"
        assert entry.get("approvedInputFields")
        assert entry.get("approvedResponseFields")


def test_redundant_and_deferred_operations_not_promoted() -> None:
    allow = load_external_read_allowlist()
    ids = {e["operationId"] for e in allow["operations"]}
    assert NOT_PROMOTED.isdisjoint(ids)
    enp = {
        (x.get("operationId") if isinstance(x, dict) else x)
        for x in (allow.get("explicitlyNotApproved") or [])
    }
    assert NOT_PROMOTED <= enp


def test_all_nine_executable_on_live_openapi() -> None:
    actions = {a.operation_id: a for a in _actions()}
    assert sum(1 for a in actions.values() if a.executable) >= 77
    for oid in PROMOTED:
        action = actions[oid]
        assert action.davi_status == STATUS_DAVI_ELIGIBLE_READ, oid
        assert action.executable, oid


def test_baseline_fallback_keeps_semantic_posts_closed() -> None:
    """Baseline rows carry no requestBody contract → POSTs fail closed."""
    actions = {a.operation_id: a for a in _baseline_actions()}
    assert sum(1 for a in actions.values() if a.executable) == 87
    for oid in PROMOTED_POST:
        action = actions[oid]
        assert action.davi_status == STATUS_NEEDS_BOUNDED_EXECUTION, oid
        assert not action.executable, oid
        assert action.semantic_transport == SEMANTIC_TRANSPORT_READ_POST


# ---------------------------------------------------------------------------
# POS-01..POS-09 — catalog binding, method/path, projection, execution
# ---------------------------------------------------------------------------

_SPECS: dict[str, dict[str, Any]] = {
    "list_product_physical_locations": {
        "method": "POST",
        "path": "/products/physical-locations",
        "post": True,
        "required": {"branch", "product_codes"},
        "args": {"branch": "01", "product_codes": ["10070821"]},
        "owner": {
            "branch": "01",
            "product_codes": ["10070821"],
            "items": [
                {
                    "product_code": "10070821",
                    "physical_location": "A-01",
                    "bz_internal": "X",
                }
            ],
            "summary": {"requested_count": 1, "returned_count": 1, "dbg": 1},
        },
        "expected_items": [
            {"product_code": "10070821", "physical_location": "A-01"}
        ],
        "expected_root": {"branch": "01"},
        "expected_summary": {"requested_count": 1, "returned_count": 1},
    },
    "list_product_inventory_blocks": {
        "method": "POST",
        "path": "/products/inventory-blocks",
        "post": True,
        "required": {"branch", "product_codes"},
        "args": {"branch": "01", "product_codes": ["10070821"]},
        "owner": {
            "branch": "01",
            "warehouse": "01",
            "as_of": "2026-10-01",
            "product_codes": ["10070821"],
            "items": [
                {
                    "product_code": "10070821",
                    "branch": "01",
                    "warehouse": "01",
                    "inventory_blocked": True,
                    "inventory_block_start": "20260901",
                    "inventory_block_end": None,
                    "inventory_block_start_iso": "2026-09-01",
                    "inventory_block_end_iso": None,
                    "b2_raw": "x",
                }
            ],
            "summary": {
                "requested_count": 1,
                "returned_count": 1,
                "blocked_count": 1,
                "dbg": 2,
            },
        },
        "expected_root": {"branch": "01", "warehouse": "01", "as_of": "2026-10-01"},
        "expected_items": [
            {
                "product_code": "10070821",
                "branch": "01",
                "warehouse": "01",
                "inventory_blocked": True,
                "inventory_block_start_iso": "2026-09-01",
                "inventory_block_end_iso": None,
            }
        ],
        "expected_summary": {
            "requested_count": 1,
            "returned_count": 1,
            "blocked_count": 1,
        },
    },
    "search_products_by_supplier_part_number": {
        "method": "GET",
        "path": "/products/by-supplier-part-number",
        "required": {"supplier_part_number"},
        "args": {"supplier_part_number": "008700056"},
        "owner": {
            "items": [
                {
                    "product_code": "10080055",
                    "product_description": "O-RING",
                    "unit": "PC",
                    "supplier_code": "000192",
                    "supplier_store": "01",
                    "supplier_name": "MOLEX",
                    "supplier_part_number": "008700056",
                    "catalog_code": "C1",
                    "barcode": "B1",
                    "registered_lead_time_days": 5,
                    "real_avg_lead_time_days": 4,
                    "real_min_lead_time_days": 2,
                    "real_max_lead_time_days": 7,
                    "real_lead_time_sample_size": 3,
                    "last_price": 9.9,
                    "last_price_date": "2026-01-01",
                }
            ],
            "page": 1,
            "page_size": 50,
            "total": 1,
            "total_pages": 1,
        },
        "expected_items": [
            {
                "product_code": "10080055",
                "product_description": "O-RING",
                "unit": "PC",
                "supplier_code": "000192",
                "supplier_store": "01",
                "supplier_name": "MOLEX",
                "supplier_part_number": "008700056",
            }
        ],
    },
    "get_product_internal_movements": {
        "method": "GET",
        "path": "/products/{code}/internal-movements",
        "required": {"code"},
        "args": {"code": "10080055", "kind": "warehouse_transfer"},
        "owner": {
            "items": [
                {
                    "branch": "01",
                    "location": "01",
                    "document": "000123",
                    "issue_date": "2026-09-30",
                    "product_code": "10080055",
                    "product_description": "ORING",
                    "unit": "PC",
                    "movement_type": "RE0",
                    "quantity": 4.0,
                    "production_order": "OP1",
                    "cf": "RE0",
                    "user_name": "JOSE",
                }
            ],
            "page": 1,
            "page_size": 50,
            "total": 1,
            "total_pages": 1,
        },
        "expected_items": [
            {
                "branch": "01",
                "location": "01",
                "document": "000123",
                "issue_date": "2026-09-30",
                "product_code": "10080055",
                "product_description": "ORING",
                "unit": "PC",
                "movement_type": "RE0",
                "quantity": 4.0,
                "production_order": "OP1",
            }
        ],
    },
    "get_product_inbound_invoice_items": {
        "method": "GET",
        "path": "/products/{code}/inbound-invoice-items",
        "required": {"code"},
        "args": {"code": "10080055"},
        "owner": {
            "items": [
                {
                    "branch": "01",
                    "invoice_number": "123",
                    "invoice_series": "1",
                    "item": "01",
                    "issue_date": "2026-09-30",
                    "product_code": "10080055",
                    "product_description": "ORING",
                    "unit": "PC",
                    "quantity": 2.0,
                    "supplier_code": "000192",
                    "supplier_name": "MOLEX",
                    "unit_price": 9.9,
                    "total_value": 19.8,
                }
            ],
            "page": 1,
            "page_size": 50,
            "total": 1,
            "total_pages": 1,
        },
        "expected_items": [
            {
                "branch": "01",
                "invoice_number": "123",
                "invoice_series": "1",
                "item": "01",
                "issue_date": "2026-09-30",
                "product_code": "10080055",
                "product_description": "ORING",
                "unit": "PC",
                "quantity": 2.0,
                "supplier_code": "000192",
                "supplier_name": "MOLEX",
            }
        ],
    },
    "get_product_outbound_invoice_items": {
        "method": "GET",
        "path": "/products/{code}/outbound-invoice-items",
        "required": {"code"},
        "args": {"code": "10080055"},
        "owner": {
            "items": [
                {
                    "branch": "01",
                    "invoice_number": "456",
                    "invoice_series": "1",
                    "item": "02",
                    "issue_date": "2026-09-30",
                    "product_code": "10080055",
                    "product_description": "ORING",
                    "unit": "PC",
                    "quantity": 3.0,
                    "customer_code": "C1",
                    "customer_name": "ACME",
                    "unit_price": 9.9,
                    "total_value": 29.7,
                }
            ],
            "page": 1,
            "page_size": 50,
            "total": 1,
            "total_pages": 1,
        },
        "expected_items": [
            {
                "branch": "01",
                "invoice_number": "456",
                "invoice_series": "1",
                "item": "02",
                "issue_date": "2026-09-30",
                "product_code": "10080055",
                "product_description": "ORING",
                "unit": "PC",
                "quantity": 3.0,
                "customer_code": "C1",
                "customer_name": "ACME",
            }
        ],
    },
    "get_product_sales_summary": {
        "method": "GET",
        "path": "/products/{code}/sales",
        "required": {"code"},
        "args": {"code": "10080055"},
        "owner": {
            "product_code": "10080055",
            "product_description": "ORING",
            "unit": "PC",
            "total_quantity": 10.0,
            "total_value": 100.0,
            "average_price": 10.0,
            "documents": 2,
            "first_sale_date": "2026-01-01",
            "last_sale_date": "2026-09-01",
            "invoice_lines": [{"x": 1}],
            "customers": [{"c": 1}],
            "branch_totals": {"01": 5},
        },
        "expected_root": {
            "product_code": "10080055",
            "product_description": "ORING",
            "unit": "PC",
            "total_quantity": 10.0,
            "total_value": 100.0,
            "average_price": 10.0,
            "documents": 2,
            "first_sale_date": "2026-01-01",
            "last_sale_date": "2026-09-01",
        },
    },
    "get_product_sales_open_orders": {
        "method": "GET",
        "path": "/products/{code}/sales/open-orders",
        "required": {"code"},
        "args": {"code": "10080055", "branch": "01"},
        "owner": {
            "items": [
                {
                    "branch": "01",
                    "order_number": "000123",
                    "order_item": "01",
                    "customer_code": "C1",
                    "customer_store": "01",
                    "customer_name": "ACME",
                    "open_quantity": 16.0,
                    "unit_price": 9.9,
                    "open_value": 9202.08,
                    "delivery_date": "2026-10-10",
                    "issue_date": "2026-09-30",
                }
            ],
            "summary": {"quantity": 16.0, "value": 9202.08, "orders": 1},
            "quantity": 16.0,
            "value": 9202.08,
            "orders": 1,
            "page": 1,
            "page_size": 50,
            "total": 1,
            "total_pages": 1,
        },
        "expected_items": [
            {
                "branch": "01",
                "order_number": "000123",
                "order_item": "01",
                "customer_code": "C1",
                "customer_store": "01",
                "customer_name": "ACME",
                "open_quantity": 16.0,
                "delivery_date": "2026-10-10",
                "issue_date": "2026-09-30",
            }
        ],
        "expected_root": {
            "summary": {"quantity": 16.0, "value": 9202.08, "orders": 1}
        },
    },
}


@pytest.mark.parametrize("oid", sorted(_SPECS))
def test_pos_catalog_binding_method_and_path(oid: str) -> None:
    spec = _SPECS[oid]
    action = _action(oid)
    assert action.method == spec["method"]
    assert action.path == spec["path"]
    assert action.executable
    assert action.execution_mode == "catalog_action"
    schema = build_argument_json_schema(action)
    assert spec["required"] <= set(schema.get("required") or [])


@pytest.mark.parametrize("oid", sorted(_SPECS))
def test_pos_executes_catalog_fixed_and_projects(_seeded, oid: str) -> None:
    spec = _SPECS[oid]
    action = _action(oid)
    # Cleaned arguments include governed defaults injected by the validator.
    cleaned = validate_arguments(action, dict(spec["args"]))
    path_param_names = {
        seg[1:-1]
        for seg in spec["path"].split("/")
        if seg.startswith("{") and seg.endswith("}")
    }
    result, client = _execute(oid, dict(spec["args"]), owner_payload=spec["owner"])
    assert result["status"] == "ok"
    assert result["action_id"] == oid
    assert result["projection"] == "approved_fields"
    call = client.calls[0]
    expected_path = spec["path"]
    for name in path_param_names:
        expected_path = expected_path.replace("{" + name + "}", str(cleaned[name]))
    assert call["path"] == expected_path
    assert call["headers"] == {"Authorization": "Bearer end-user"}
    non_path = {k: v for k, v in cleaned.items() if k not in path_param_names}
    if spec.get("post"):
        body_fields = action.body_fields
        assert call["verb"] == "post"
        assert call["json"] == {k: v for k, v in non_path.items() if k in body_fields}
        assert call["params"] in (None, {}) or call["params"] == {
            k: v for k, v in non_path.items() if k not in body_fields
        }
    else:
        assert call["verb"] == "get"
        assert call["params"] == non_path
    data = result["data"]
    if "expected_items" in spec:
        assert data["items"] == spec["expected_items"]
    if "expected_root" in spec:
        for key, value in spec["expected_root"].items():
            assert data[key] == value
    if "expected_summary" in spec:
        assert data["summary"] == spec["expected_summary"]


def test_pos_exclusive_catalog_by_material_projection(_seeded) -> None:
    owner = {
        "view": "by_material",
        "items": [
            {
                "raw_material_code": "MP1",
                "raw_material_description": "RESIN",
                "raw_material_unit": "KG",
                "raw_material_group": "G1",
                "finished_product_code": "PA1",
                "finished_product_description": "PART",
                "finished_product_unit": "PC",
                "exclusive_raw_material": True,
                "max_depth_used": 3,
            }
        ],
        "summary": {
            "returned_exclusive_links": 1,
            "totals_available": True,
            "total_exclusive_materials": 1,
            "total_finished_products_with_exclusive": 1,
            "hidden_total": 9,
        },
        "pagination": {
            "limit": 50,
            "offset": 0,
            "returned": 1,
            "is_complete": True,
            "internal_cursor": "x",
        },
    }
    result, client = _execute(
        "list_exclusive_raw_materials_catalog", {}, owner_payload=owner
    )
    assert result["status"] == "ok"
    assert client.calls[0]["verb"] == "get"
    assert client.calls[0]["path"] == "/products/exclusive-raw-materials/catalog"
    data = result["data"]
    assert data["view"] == "by_material"
    item = data["items"][0]
    assert set(item) == {
        "raw_material_code",
        "raw_material_description",
        "raw_material_unit",
        "raw_material_group",
        "finished_product_code",
        "finished_product_description",
        "finished_product_unit",
        "exclusive_raw_material",
    }
    assert "max_depth_used" not in item
    assert set(data["summary"]) == {
        "returned_exclusive_links",
        "totals_available",
        "total_exclusive_materials",
        "total_finished_products_with_exclusive",
    }
    assert set(data["pagination"]) == {"limit", "offset", "returned", "is_complete"}


def test_pos_exclusive_catalog_by_finished_product_nested_projection(_seeded) -> None:
    owner = {
        "view": "by_finished_product",
        "items": [
            {
                "finished_product_code": "PA1",
                "finished_product_description": "PART",
                "finished_product_unit": "PC",
                "exclusive_raw_material_count": 1,
                "exclusive_raw_materials": [
                    {
                        "raw_material_code": "MP1",
                        "raw_material_description": "RESIN",
                        "raw_material_unit": "KG",
                        "raw_material_group": "G1",
                        "supplier_lead_time": 5,
                    }
                ],
                "internal": True,
            }
        ],
        "summary": {
            "returned_exclusive_links": 1,
            "totals_available": True,
            "total_finished_products": 1,
            "total_exclusive_links": 1,
        },
        "pagination": {"limit": 50, "offset": 0, "returned": 1, "is_complete": True},
    }
    result, _ = _execute(
        "list_exclusive_raw_materials_catalog",
        {"view": "by_finished_product"},
        owner_payload=owner,
    )
    item = result["data"]["items"][0]
    assert set(item) == {
        "finished_product_code",
        "finished_product_description",
        "finished_product_unit",
        "exclusive_raw_material_count",
        "exclusive_raw_materials",
    }
    nested = item["exclusive_raw_materials"][0]
    assert set(nested) == {
        "raw_material_code",
        "raw_material_description",
        "raw_material_unit",
        "raw_material_group",
    }


# ---------------------------------------------------------------------------
# Retrieval + discovery + candidate token
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("query", "oid"),
    [
        ("local físico do produto 10080055", "list_product_physical_locations"),
        (
            "bloqueio de inventário do produto 10080055",
            "list_product_inventory_blocks",
        ),
        (
            "part number do fornecedor 008700056",
            "search_products_by_supplier_part_number",
        ),
        (
            "matéria-prima exclusiva do produto",
            "list_exclusive_raw_materials_catalog",
        ),
        (
            "movimentação interna do produto 10080055",
            "get_product_internal_movements",
        ),
        (
            "notas fiscais de entrada do produto 10080055",
            "get_product_inbound_invoice_items",
        ),
        (
            "notas fiscais de saída do produto 10080055",
            "get_product_outbound_invoice_items",
        ),
        ("quanto este produto vendeu 10080055", "get_product_sales_summary"),
        (
            "pedidos de venda em aberto do produto 10080055",
            "get_product_sales_open_orders",
        ),
    ],
)
def test_pos_owned_intent_discovers_candidate(_seeded, query: str, oid: str) -> None:
    ranked_ids = [
        a.operation_id for a, _ in retrieve_eligible_actions(query, _actions(), top_k=10)
    ]
    assert oid in ranked_ids, (query, ranked_ids)
    discovered = discover_delpi_information(query=query, top_k=5, actor_id=_ACTOR)
    assert discovered["eligible_action_count"] == 90
    ids = [c["action_id"] for c in discovered["candidates"]]
    assert oid in ids, (query, ids)
    top = discovered["candidates"][0]
    assert top["action_id"] == oid
    assert top["candidate_token"]
    # Token decodes only for the discovering actor.
    payload = parse_candidate_token(
        top["candidate_token"], secret=_SECRET, expected_actor_id=_ACTOR
    )
    assert payload["action_id"] == oid
    assert payload["actor_id"] == _ACTOR


@pytest.mark.parametrize(
    ("query", "absent_oid"),
    [
        (
            "pedido de compra do produto 10080055",
            "get_product_sales_open_orders",
        ),
        (
            "ordem de produção do produto 10080055",
            "get_product_sales_open_orders",
        ),
        (
            "relatório financeiro do produto 10080055",
            "get_product_inbound_invoice_items",
        ),
        (
            "faturamento do produto 10080055",
            "get_product_internal_movements",
        ),
        (
            "saldo em estoque do produto 10080055",
            "list_product_physical_locations",
        ),
        (
            "disponibilidade do estoque",
            "list_product_inventory_blocks",
        ),
        (
            "histórico de preço do fornecedor 000192",
            "search_products_by_supplier_part_number",
        ),
    ],
)
def test_retrieval_collision_guards(_seeded, query: str, absent_oid: str) -> None:
    """Ambiguous/cross-domain intents must not be owned by the promoted op."""
    discovered = discover_delpi_information(query=query, top_k=10, actor_id=_ACTOR)
    ids = [c["action_id"] for c in discovered["candidates"]]
    assert not ids or ids[0] != absent_oid, (query, ids)


def test_invoice_direction_is_semantic_not_caller_dispatch(_seeded) -> None:
    """direction must never be a caller-controlled backend selector."""
    for oid in (
        "get_product_inbound_invoice_items",
        "get_product_outbound_invoice_items",
    ):
        action = _action(oid)
        schema = build_argument_json_schema(action)
        assert "direction" not in schema["properties"]
        with pytest.raises(ArgumentValidationError):
            validate_arguments(action, {"code": "P1", "direction": "inbound"})


def test_candidate_token_actor_binding(_seeded) -> None:
    token = _mint("get_product_sales_summary", actor_id=_ACTOR)

    class _Exec:
        def execute(self, *, action_id, validated_arguments):  # pragma: no cover
            raise AssertionError("must not execute")

    with pytest.raises(CandidateTokenError):
        execute_delpi_information(
            candidate_token=token,
            arguments={"code": "P1"},
            actor_id=_OTHER_ACTOR,
            catalog_action_executor=_Exec(),
        )


# ---------------------------------------------------------------------------
# Argument governance / bounds
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "oid",
    ["list_product_physical_locations", "list_product_inventory_blocks"],
)
@pytest.mark.parametrize("count", [1, 50])
def test_post_product_codes_bounds_pass(oid: str, count: int) -> None:
    action = _action(oid)
    args = {"branch": "01", "product_codes": [f"P{i}" for i in range(count)]}
    cleaned = validate_arguments(action, args)
    assert cleaned["product_codes"] == args["product_codes"]


@pytest.mark.parametrize(
    "oid",
    ["list_product_physical_locations", "list_product_inventory_blocks"],
)
@pytest.mark.parametrize("count", [0, 51])
def test_post_product_codes_bounds_deny(oid: str, count: int) -> None:
    action = _action(oid)
    with pytest.raises(ArgumentValidationError):
        validate_arguments(
            action, {"branch": "01", "product_codes": ["P"] * count}
        )


@pytest.mark.parametrize(
    "oid",
    ["list_product_physical_locations", "list_product_inventory_blocks"],
)
@pytest.mark.parametrize(
    "args",
    [
        {},
        {"branch": "01"},
        {"product_codes": ["P1"]},
        {"branch": "01", "product_codes": "P1,P2"},
        {"branch": "01", "product_codes": ["P1"], "extra": 1},
        {"branch": "01", "product_codes": ["P1"], "url": "http://x"},
        {"branch": "01", "product_codes": ["P1"], "method": "DELETE"},
        {"branch": "01", "product_codes": ["P1"], "path": "/x"},
        {"branch": "01", "product_codes": ["P1"], "host": "h"},
        {"branch": "01", "product_codes": ["P1"], "operationId": "x"},
        {"branch": "01", "product_codes": ["P1"], "Authorization": "t"},
    ],
)
def test_post_argument_governance(oid: str, args: dict[str, Any]) -> None:
    with pytest.raises(ArgumentValidationError):
        validate_arguments(_action(oid), args)


def test_inventory_blocks_warehouse_default_and_server_as_of() -> None:
    action = _action("list_product_inventory_blocks")
    cleaned = validate_arguments(
        action, {"branch": "01", "product_codes": ["P1"]}
    )
    assert cleaned["warehouse"] == "01"
    schema = build_argument_json_schema(action)
    assert "as_of" not in schema["properties"]
    with pytest.raises(ArgumentValidationError):
        validate_arguments(
            action, {"branch": "01", "product_codes": ["P1"], "as_of": "2026-01-01"}
        )


def test_supplier_part_number_required_and_page_bounds() -> None:
    action = _action("search_products_by_supplier_part_number")
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, {})
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, {"supplier_part_number": "X", "page": 0})
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, {"supplier_part_number": "X", "page_size": 51})
    cleaned = validate_arguments(action, {"supplier_part_number": "008700056"})
    assert cleaned["page"] == 1
    assert cleaned["page_size"] == 50


def test_exclusive_catalog_view_enum_and_bounds() -> None:
    action = _action("list_exclusive_raw_materials_catalog")
    for view in ("by_material", "by_finished_product"):
        assert validate_arguments(action, {"view": view})["view"] == view
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, {"view": "raw_dump"})
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, {"limit": 51})
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, {"offset": -1})
    for forbidden in ("include_test_products", "legacy", "max_depth"):
        with pytest.raises(ArgumentValidationError):
            validate_arguments(action, {forbidden: True})


def test_internal_movements_kind_enum_and_tm_denied() -> None:
    action = _action("get_product_internal_movements")
    assert validate_arguments(action, {"code": "P1"}).get("kind") is None
    assert (
        validate_arguments(
            action, {"code": "P1", "kind": "warehouse_transfer"}
        )["kind"]
        == "warehouse_transfer"
    )
    for bad in ({"code": "P1", "kind": "all"}, {"code": "P1", "tm": "123"}):
        with pytest.raises(ArgumentValidationError):
            validate_arguments(action, bad)


_DATE_RANGE_OPS = [
    ("get_product_internal_movements", "start_date", "end_date"),
    ("get_product_inbound_invoice_items", "issue_date_start", "issue_date_end"),
    ("get_product_outbound_invoice_items", "issue_date_start", "issue_date_end"),
]


@pytest.mark.parametrize(("oid", "start_field", "end_field"), _DATE_RANGE_OPS)
def test_date_window_one_sided_bounds(
    oid: str, start_field: str, end_field: str
) -> None:
    action = _action(oid)
    # A. no dates
    cleaned = validate_arguments(action, {"code": "P1"})
    assert start_field not in cleaned
    assert end_field not in cleaned
    # B. start only — passes and no end bound is synthesized
    cleaned = validate_arguments(action, {"code": "P1", start_field: "2026-01-01"})
    assert cleaned[start_field] == "2026-01-01"
    assert end_field not in cleaned
    # C. end only — passes and no start bound is synthesized
    cleaned = validate_arguments(action, {"code": "P1", end_field: "2026-06-30"})
    assert cleaned[end_field] == "2026-06-30"
    assert start_field not in cleaned
    # D. both present, span <= 366 days
    ok = validate_arguments(
        action,
        {"code": "P1", start_field: "2025-10-02", end_field: "2026-10-02"},
    )
    assert ok[start_field] == "2025-10-02"
    assert ok[end_field] == "2026-10-02"
    # E. both present, span > 366 days
    with pytest.raises(ArgumentValidationError):
        validate_arguments(
            action,
            {"code": "P1", start_field: "2025-09-30", end_field: "2026-10-02"},
        )
    # F. end before start
    with pytest.raises(ArgumentValidationError):
        validate_arguments(
            action,
            {"code": "P1", start_field: "2026-10-02", end_field: "2025-10-02"},
        )
    # G/H. malformed dates, single-bound or paired
    for bad in (
        {"code": "P1", start_field: "not-a-date"},
        {"code": "P1", end_field: "2026-13-40"},
        {
            "code": "P1",
            start_field: "2026-01-01",
            end_field: "soon",
        },
    ):
        with pytest.raises(ArgumentValidationError):
            validate_arguments(action, bad)


@pytest.mark.parametrize(("oid", "start_field", "end_field"), _DATE_RANGE_OPS)
def test_date_window_missing_bound_not_sent_to_owner(
    _seeded, oid: str, start_field: str, end_field: str
) -> None:
    owner = _SPECS.get(oid, {}).get("owner") or {}
    result, client = _execute(
        oid, {"code": "P1", start_field: "2026-01-01"}, owner_payload=owner
    )
    assert result["status"] == "ok"
    params = client.calls[0]["params"]
    assert params[start_field] == "2026-01-01"
    assert end_field not in params
    result, client = _execute(
        oid, {"code": "P1", end_field: "2026-06-30"}, owner_payload=owner
    )
    assert result["status"] == "ok"
    params = client.calls[0]["params"]
    assert params[end_field] == "2026-06-30"
    assert start_field not in params


def test_sales_summary_no_optional_inputs() -> None:
    action = _action("get_product_sales_summary")
    schema = build_argument_json_schema(action)
    assert set(schema["properties"]) == {"code"}
    for bad in (
        {"code": "P1", "branch": "01"},
        {"code": "P1", "date": "2026-01-01"},
        {"code": "P1", "customer": "C1"},
        {"code": "P1", "period": "30"},
    ):
        with pytest.raises(ArgumentValidationError):
            validate_arguments(action, bad)


def test_open_orders_branch_narrows_only() -> None:
    action = _action("get_product_sales_open_orders")
    cleaned = validate_arguments(action, {"code": "P1", "branch": "01"})
    assert cleaned["branch"] == "01"
    cleaned = validate_arguments(action, {"code": "P1", "page": 2, "page_size": 10})
    assert cleaned["page"] == 2
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, {"code": "P1", "page_size": 51})


@pytest.mark.parametrize(
    "key",
    ["method", "path", "url", "host", "operationId", "authorization", "Authorization"],
)
def test_transport_smuggling_denied_everywhere(key: str) -> None:
    for oid in PROMOTED:
        action = _action(oid)
        args = {"code": "P1", "branch": "01", "product_codes": ["P1"],
                "supplier_part_number": "X", key: "x"}
        with pytest.raises(ArgumentValidationError):
            validate_arguments(action, args)


# ---------------------------------------------------------------------------
# Failure semantics / end-user AuthZ propagation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("oid", sorted(PROMOTED))
def test_end_user_authorization_propagated(_seeded, oid: str) -> None:
    spec = _SPECS.get(oid) or {"args": {}, "owner": {}}
    _, client = _execute(
        oid, dict(spec.get("args") or {}), owner_payload=spec.get("owner") or {}
    )
    assert client.calls[0]["headers"] == {"Authorization": "Bearer end-user"}


@pytest.mark.parametrize("status", [401, 403])
def test_backend_authz_denial_stays_governed(_seeded, status: int) -> None:
    client = _FakeClient(_FakeResponse(status, {"detail": "denied"}))
    executor = AsgiCatalogActionExecutor(client, authorization="Bearer end-user")
    with pytest.raises(PermissionError):
        execute_delpi_information(
            candidate_token=_mint("get_product_sales_summary"),
            arguments={"code": "P1"},
            actor_id=_ACTOR,
            catalog_action_executor=executor,
        )


def test_execute_blocks_wrong_actor_before_http(_seeded) -> None:
    client = _FakeClient(_FakeResponse(200, {"data": {}}))
    executor = AsgiCatalogActionExecutor(client, authorization="Bearer end-user")
    with pytest.raises(CandidateTokenError):
        execute_delpi_information(
            candidate_token=_mint("get_product_sales_summary", actor_id=_ACTOR),
            arguments={"code": "P1"},
            actor_id=_OTHER_ACTOR,
            catalog_action_executor=executor,
        )
    assert client.calls == []


def test_zero_row_results_are_canonical(_seeded) -> None:
    owner = {"items": [], "page": 1, "page_size": 50, "total": 0, "total_pages": 0}
    result, _ = _execute(
        "get_product_sales_open_orders", {"code": "P1"}, owner_payload=owner
    )
    assert result["status"] == "ok"
    assert result["data"]["items"] == []
    result, _ = _execute(
        "get_product_sales_summary",
        {"code": "P1"},
        owner_payload={
            "product_code": "P1",
            "product_description": None,
            "unit": None,
            "total_quantity": 0.0,
            "total_value": 0.0,
            "average_price": 0.0,
            "documents": 0,
            "first_sale_date": None,
            "last_sale_date": None,
        },
    )
    assert result["data"]["total_quantity"] == 0.0
    assert result["data"]["documents"] == 0
