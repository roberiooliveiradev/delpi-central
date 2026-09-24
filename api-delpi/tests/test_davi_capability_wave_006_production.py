"""DAVI Wave 006 — Production Operational Intelligence governed READ promotion."""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest

from app.application.external_capabilities.constants import (
    MCP_TOOL_DISCOVER_DELPI_INFORMATION,
    MCP_TOOL_EXECUTE_DELPI_INFORMATION,
)
from app.application.external_capabilities.dynamic_information.action_index import (
    reset_action_index_for_tests,
    set_actions_for_tests,
)
from app.application.external_capabilities.dynamic_information.argument_validator import (
    ArgumentValidationError,
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

_PRIOR_FIFTY_THREE = (
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

_PROMOTED = (
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
)

_EXPECTED_INPUTS: dict[str, tuple[str, ...]] = {
    "get_overall_equipment_effectiveness_pct": ("start_date", "end_date", "branch"),
    "get_production_oee": (
        "start_date",
        "end_date",
        "branch",
        "work_center",
        "product_type",
    ),
    "get_production_oee_series": ("granularity", "start_date", "end_date", "branch"),
    "get_on_time_delivery_pct": ("start_date", "end_date", "branch"),
    "get_production_otd": ("start_date", "end_date", "branch"),
    "get_production_otd_series": ("granularity", "start_date", "end_date", "branch"),
    "get_production_machine_load_work_centers": (
        "branch",
        "scheduled_start",
        "scheduled_end",
        "delivery_start",
        "delivery_end",
        "work_center",
        "product_code",
        "production_order",
        "tool",
        "open_only",
    ),
    "get_production_machine_load_operations": (
        "branch",
        "scheduled_start",
        "scheduled_end",
        "delivery_start",
        "delivery_end",
        "work_center",
        "product_code",
        "production_order",
        "tool",
        "open_only",
        "page",
        "page_size",
    ),
    "get_production_appointments_summary": (
        "start_date",
        "end_date",
        "branch",
        "work_center",
        "op",
        "product",
        "mother_op",
    ),
    "get_production_appointments_produced_totals": (
        "start_date",
        "end_date",
        "branch",
        "product",
    ),
}

_EXPECTED_OUTPUTS: dict[str, tuple[str, ...]] = {
    "get_overall_equipment_effectiveness_pct": (
        "overall_equipment_effectiveness_pct",
    ),
    "get_production_oee": (
        "branch",
        "start_date",
        "end_date",
        "summary.oee_pct",
        "summary.total_appointments",
        "summary.valid_appointments",
        "summary.outlier_appointments",
        "summary.outlier_percentage",
    ),
    "get_production_oee_series": (
        "granularity",
        "truncated",
        "branch",
        "points[].periodo",
        "points[].start_date",
        "points[].end_date",
        "points[].oee_filial_01",
        "points[].oee_filial_02",
    ),
    "get_on_time_delivery_pct": ("on_time_delivery_pct",),
    "get_production_otd": (
        "branch",
        "start_date",
        "end_date",
        "summary.total_ops_finished",
        "summary.on_time_ops",
        "summary.late_ops",
        "summary.on_time_delivery_pct",
        "summary.late_percentage",
    ),
    "get_production_otd_series": (
        "granularity",
        "truncated",
        "branch",
        "points[].periodo",
        "points[].start_date",
        "points[].end_date",
        "points[].otd_filial_01",
        "points[].otd_filial_02",
    ),
    "get_production_machine_load_work_centers": (
        "work_center",
        "work_center_name",
        "operation_count",
        "order_count",
        "in_production_count",
        "first_scheduled_date",
        "last_scheduled_date",
        "first_due_date",
        "last_due_date",
        "missing_due_date_count",
    ),
    "get_production_machine_load_operations": (
        "scheduled_date",
        "scheduled_start_time",
        "work_center",
        "work_center_name",
        "production_order",
        "operation_code",
        "operation_description",
        "tool",
        "product_code",
        "product_description",
        "planned_qty",
        "operation_produced_qty",
        "operation_pending_qty",
        "unit",
        "due_date",
        "production_status",
        "is_in_production",
    ),
    "get_production_appointments_summary": (
        "period.start",
        "period.end_exclusive",
        "branch",
        "totals.appointment_count",
        "totals.qty_produced",
        "totals.qty_lost",
        "totals.op_count",
        "totals.work_center_count",
        "totals.unit",
        "totals.qty_produced_scope",
        "items[].work_center",
        "items[].work_center_name",
        "items[].is_final_inspection",
        "items[].appointment_count",
        "items[].qty_produced",
        "items[].qty_lost",
        "items[].op_count",
    ),
    "get_production_appointments_produced_totals": (
        "branch",
        "start_date",
        "end_date",
        "products",
        "product_types",
        "qty_produced_un",
        "qty_lost_un",
        "appointment_count",
        "orders_count",
        "inspection_final",
        "mother_op",
    ),
}


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


def test_wave006_allowlist_version_and_eligible_count():
    allow = load_external_read_allowlist()
    assert allow.get("version") == 15
    assert allow.get("coverageDecision", {}).get("taskId") == (
        "DAVI-CAPABILITY-EXPANSION-WAVE-006-PRODUCTION-READ"
    )
    eligible = {a.operation_id for a in _actions() if a.executable}
    assert len(_PRIOR_FIFTY_THREE) == 53
    assert len(_PROMOTED) == 10
    assert len(eligible) == 63
    assert set(_PRIOR_FIFTY_THREE) <= eligible
    assert set(_PROMOTED) <= eligible


@pytest.mark.parametrize("oid", _PROMOTED)
def test_wave006_promoted_contract_matrix(oid: str):
    action = _action(oid)
    entry = _allowlist_entry(oid)
    assert action.method.upper() == "GET"
    assert action.executable is True
    fields_in = list(entry.get("approvedInputFields") or [])
    fields_out = list(entry.get("approvedResponseFields") or [])
    assert tuple(fields_in) == _EXPECTED_INPUTS[oid]
    assert tuple(fields_out) == _EXPECTED_OUTPUTS[oid]
    assert all("*" not in f for f in fields_out)
    assert all("/" not in f for f in fields_in)
    param_names = {p["name"] for p in (action.parameters or ()) if isinstance(p, dict)}
    for name in fields_in:
        assert name in param_names or name in action.path, (oid, name)
    assert "url" not in fields_in
    assert "operationId" not in fields_in
    assert "sql" not in fields_in
    assert entry.get("semanticAliases")
    assert entry.get("executionMode") == "catalog_action"


def test_wave006_mcp_tools_remain_two():
    import asyncio

    from app.interface.mcp.server import create_mcp_server

    tools = asyncio.run(create_mcp_server().list_tools())
    assert [t.name for t in tools] == [
        MCP_TOOL_DISCOVER_DELPI_INFORMATION,
        MCP_TOOL_EXECUTE_DELPI_INFORMATION,
    ]


def test_wave006_agent_intelligence_unchanged_and_no_hardcoded_ops():
    intel = json.loads(
        (_API_ROOT / "app/content/davi_agent_intelligence.json").read_text(
            encoding="utf-8"
        )
    )
    assert intel.get("version") == "2026.09.24.3"
    blob = json.dumps(intel)
    for oid in _PROMOTED:
        assert oid not in blob


@pytest.mark.parametrize(
    ("oid", "forbidden"),
    [
        ("get_production_oee", "operator_code"),
        ("get_production_oee", "production_order"),
        ("get_production_oee", "status"),
        ("get_production_oee", "page"),
        ("get_production_oee", "page_size"),
        ("get_production_otd", "status"),
        ("get_production_otd", "page"),
        ("get_production_otd", "sort_by"),
        ("get_production_machine_load_work_centers", "include_closed"),
        ("get_production_machine_load_operations", "include_closed"),
        ("get_production_machine_load_operations", "sort"),
        ("get_production_appointments_summary", "date_start"),
        ("get_production_appointments_summary", "date_end"),
        ("get_production_appointments_produced_totals", "product_types"),
        ("get_production_appointments_produced_totals", "date_start"),
    ],
)
def test_wave006_rejects_unapproved_arguments(oid: str, forbidden: str):
    action = _action(oid)
    with pytest.raises(ArgumentValidationError, match="Unknown argument"):
        validate_arguments(action, {forbidden: "x"})


def test_wave006_date_bounds_366():
    action = _action("get_overall_equipment_effectiveness_pct")
    start = date(2025, 1, 1)
    ok_end = start + timedelta(days=366)
    bad_end = start + timedelta(days=367)
    validate_arguments(
        action,
        {"start_date": start.isoformat(), "end_date": ok_end.isoformat()},
    )
    with pytest.raises(ArgumentValidationError, match="exceeds 366"):
        validate_arguments(
            action,
            {"start_date": start.isoformat(), "end_date": bad_end.isoformat()},
        )


def test_wave006_machine_load_scheduled_and_delivery_windows_90():
    action = _action("get_production_machine_load_operations")
    start = date(2026, 1, 1)
    ok = start + timedelta(days=89)
    bad = start + timedelta(days=90)
    # 90 days inclusive span = (end-start).days == 89? Brief says <= 90 days.
    # Validator uses (end - start).days > max_days → max span days delta is 90.
    # So start + 90 days is allowed (delta=90), start+91 fails.
    ok_end = start + timedelta(days=90)
    bad_end = start + timedelta(days=91)
    validate_arguments(
        action,
        {
            "scheduled_start": start.isoformat(),
            "scheduled_end": ok_end.isoformat(),
        },
    )
    with pytest.raises(ArgumentValidationError, match="scheduled_"):
        validate_arguments(
            action,
            {
                "scheduled_start": start.isoformat(),
                "scheduled_end": bad_end.isoformat(),
            },
        )
    validate_arguments(
        action,
        {
            "delivery_start": start.isoformat(),
            "delivery_end": ok_end.isoformat(),
        },
    )
    with pytest.raises(ArgumentValidationError, match="delivery_"):
        validate_arguments(
            action,
            {
                "delivery_start": start.isoformat(),
                "delivery_end": bad_end.isoformat(),
            },
        )
    # Neither window → canonical default preserved (no DAVI injection / no error)
    cleaned = validate_arguments(action, {"branch": "01"})
    assert "scheduled_start" not in cleaned
    assert "delivery_start" not in cleaned
    _ = ok  # silence lint
    _ = bad


def test_wave006_machine_load_page_size_bound():
    action = _action("get_production_machine_load_operations")
    validate_arguments(action, {"page": 1, "page_size": 50})
    with pytest.raises(ArgumentValidationError, match="page_size"):
        validate_arguments(action, {"page": 1, "page_size": 51})
    with pytest.raises(ArgumentValidationError, match="page"):
        validate_arguments(action, {"page": 0, "page_size": 10})


def test_wave006_granularity_enum():
    action = _action("get_production_oee_series")
    validate_arguments(
        action,
        {
            "granularity": "month",
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
        },
    )
    with pytest.raises(ArgumentValidationError, match="enum"):
        validate_arguments(
            action,
            {
                "granularity": "quarter",
                "start_date": "2026-01-01",
                "end_date": "2026-01-31",
            },
        )


def test_wave006_projection_strips_forbidden_fields():
    oee = apply_approved_field_projection(
        {
            "branch": "01",
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
            "summary": {
                "oee_pct": 77.5,
                "total_appointments": 10,
                "valid_appointments": 8,
                "outlier_appointments": 2,
                "outlier_percentage": 20.0,
                "secret": "no",
            },
            "appointments": {
                "items": [
                    {
                        "appointment_id": 1,
                        "operator_code": "X",
                        "production_order": "OP1",
                        "oee_pct": 50,
                    }
                ]
            },
        },
        approved_fields=_EXPECTED_OUTPUTS["get_production_oee"],
    )
    assert "appointments" not in oee
    assert oee["summary"]["oee_pct"] == 77.5
    assert "secret" not in oee["summary"]

    otd = apply_approved_field_projection(
        {
            "branch": "01",
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
            "summary": {
                "total_ops_finished": 5,
                "on_time_ops": 4,
                "late_ops": 1,
                "on_time_delivery_pct": 80.0,
                "late_percentage": 20.0,
            },
            "orders": {"items": [{"production_order": "OP", "days_diff": 3}]},
        },
        approved_fields=_EXPECTED_OUTPUTS["get_production_otd"],
    )
    assert "orders" not in otd

    ops = apply_approved_field_projection(
        {
            "items": [
                {
                    "scheduled_date": "20260101",
                    "scheduled_start_time": "0800",
                    "work_center": "CT-10",
                    "work_center_name": "Tornearia",
                    "production_order": "10964501001",
                    "operation_code": "01",
                    "operation_description": "Usinar",
                    "tool": "MOD",
                    "product_code": "PA1",
                    "product_description": "Produto",
                    "planned_qty": 10,
                    "operation_produced_qty": 2,
                    "operation_pending_qty": 8,
                    "unit": "UN",
                    "due_date": "2026-01-10",
                    "production_status": "in_progress",
                    "is_in_production": True,
                    "active_operator_code": "USR1",
                    "active_operator_name": "Alice",
                    "active_operator_count": 1,
                    "production_started_date": "20260101",
                    "production_started_time": "0900",
                }
            ]
        },
        approved_fields=_EXPECTED_OUTPUTS["get_production_machine_load_operations"],
    )
    item = ops["items"][0]
    assert "active_operator_name" not in item
    assert "active_operator_code" not in item
    assert "active_operator_count" not in item
    assert "production_started_date" not in item
    assert "production_started_time" not in item
    assert item["production_order"] == "10964501001"

    produced = apply_approved_field_projection(
        {
            "branch": "01",
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
            "products": [],
            "product_types": ["PA", "PI"],
            "qty_produced_un": 100.0,
            "qty_lost_un": 1.0,
            "qty_produced_milheiro": 0.1,
            "qty_lost_milheiro": 0.0,
            "appointment_count": 3,
            "orders_count": 2,
            "inspection_final": True,
            "mother_op": True,
            "items": [{"product_code": "PA1"}],
            "by_product": [{"product_code": "PA1"}],
        },
        approved_fields=_EXPECTED_OUTPUTS[
            "get_production_appointments_produced_totals"
        ],
    )
    assert "qty_produced_milheiro" not in produced
    assert "qty_lost_milheiro" not in produced
    assert "items" not in produced
    assert "by_product" not in produced
    assert produced["qty_produced_un"] == 100.0


def test_wave006_null_kpi_stays_null():
    projected = apply_approved_field_projection(
        {"overall_equipment_effectiveness_pct": None, "noise": 0},
        approved_fields=("overall_equipment_effectiveness_pct",),
    )
    assert projected["overall_equipment_effectiveness_pct"] is None

    projected_otd = apply_approved_field_projection(
        {"on_time_delivery_pct": None},
        approved_fields=("on_time_delivery_pct",),
    )
    assert projected_otd["on_time_delivery_pct"] is None

    series = apply_approved_field_projection(
        {
            "granularity": "month",
            "truncated": False,
            "branch": None,
            "points": [
                {
                    "periodo": "2026-01",
                    "sort_key": "202601",
                    "start_date": "2026-01-01",
                    "end_date": "2026-01-31",
                    "oee_filial_01": None,
                    "oee_filial_02": 70.0,
                }
            ],
        },
        approved_fields=_EXPECTED_OUTPUTS["get_production_oee_series"],
    )
    assert "sort_key" not in series["points"][0]
    assert series["points"][0]["oee_filial_01"] is None


def test_wave006_canonical_authz_decorators_unchanged():
    production_router = (
        _API_ROOT / "app/interface/http/routes/production/production_router.py"
    ).read_text(encoding="utf-8")
    machine_router = (
        _API_ROOT / "app/interface/http/routes/production/machine_load_router.py"
    ).read_text(encoding="utf-8")
    appointments_router = (
        _API_ROOT
        / "app/interface/http/routes/production_appointments/production_appointments_router.py"
    ).read_text(encoding="utf-8")
    branch_access = (
        _API_ROOT
        / "app/interface/http/routes/production_appointments/production_appointments_branch_access.py"
    ).read_text(encoding="utf-8")

    assert "KPI_PRODUCTION_ACCESS" in production_router
    assert "@require_any_permission(KPI_PRODUCTION_ACCESS)" in production_router
    assert "KPI_PRODUCTION_ACCESS" in machine_router
    assert "PRODUCTION_APPOINTMENTS_READ_PERMISSIONS" in appointments_router
    assert "branch_access_error" in appointments_router
    assert "def branch_access_error" in branch_access
    broker = (
        _API_ROOT / "app/application/external_capabilities"
    ).resolve()
    # No local RBAC duplication in dynamic_information
    for path in broker.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "KPI_PRODUCTION_ACCESS" not in text
        assert "PRODUCTION_APPOINTMENTS_READ_PERMISSIONS" not in text
        assert "branch_access_error" not in text


def _discover(query: str, monkeypatch) -> dict[str, Any]:
    set_actions_for_tests(_actions())
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "sec",
    )
    return discover_delpi_information(query=query, top_k=5, actor_id="u1")


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("OEE", "get_overall_equipment_effectiveness_pct"),
        ("OEE de produção", "get_overall_equipment_effectiveness_pct"),
        ("eficiência geral dos equipamentos", "get_overall_equipment_effectiveness_pct"),
        ("evolução do OEE", "get_production_oee_series"),
        ("OTD de produção", "get_on_time_delivery_pct"),
        ("OTD das OPs", "get_on_time_delivery_pct"),
        ("OTD das ordens de produção", "get_on_time_delivery_pct"),
        ("pontualidade da produção", "get_on_time_delivery_pct"),
        ("OPs no prazo", "get_on_time_delivery_pct"),
        ("OPs atrasadas", "get_on_time_delivery_pct"),
        ("evolução do OTD de produção", "get_production_otd_series"),
        ("carga de máquina", "get_production_machine_load_work_centers"),
        ("carga por CT", "get_production_machine_load_work_centers"),
        ("fila do CT", "get_production_machine_load_work_centers"),
        ("operações programadas", "get_production_machine_load_operations"),
        ("operações alocadas", "get_production_machine_load_operations"),
        ("resumo dos apontamentos", "get_production_appointments_summary"),
        ("apontamentos de produção resumidos", "get_production_appointments_summary"),
        ("quantidade apontada por CT", "get_production_appointments_summary"),
        ("quanto foi produzido", "get_production_appointments_produced_totals"),
        ("quantidade produzida", "get_production_appointments_produced_totals"),
        ("produção realizada no período", "get_production_appointments_produced_totals"),
        ("total produzido", "get_production_appointments_produced_totals"),
    ],
)
def test_wave006_retrieval_positive(query: str, expected: str, monkeypatch):
    discovered = _discover(query, monkeypatch)
    assert discovered["eligible_action_count"] == 63, query
    assert discovered["candidate_count"] >= 1, query
    top = discovered["candidates"][0]["action_id"]
    assert top == expected, (query, top, [c["action_id"] for c in discovered["candidates"][:3]])


@pytest.mark.parametrize(
    ("query", "forbidden_prefix"),
    [
        ("OTD comercial", "get_on_time_delivery_pct"),
        ("OTD comercial", "get_production_otd"),
        ("OTD de compras", "get_on_time_delivery_pct"),
        ("OTD de compras", "get_production_otd"),
        ("OTD suprimentos", "get_on_time_delivery_pct"),
        ("OTD suprimentos", "get_production_otd"),
        ("roteiro do produto", "get_production_machine_load"),
        ("guia de fabricação", "get_production_machine_load"),
        ("listar apontamentos brutos", "get_production_appointments_summary"),
        ("apontamento do operador", "get_production_oee"),
        ("status de produção do produto", "get_overall_equipment_effectiveness"),
    ],
)
def test_wave006_retrieval_collisions(query: str, forbidden_prefix: str, monkeypatch):
    discovered = _discover(query, monkeypatch)
    if discovered["candidate_count"] == 0:
        return
    top = discovered["candidates"][0]["action_id"]
    assert not top.startswith(forbidden_prefix), (query, top)


def test_wave006_bare_otd_not_hardwired_to_production(monkeypatch):
    discovered = _discover("OTD", monkeypatch)
    # Bare OTD must not be hardwired to Production. Legitimate multi-family ties
    # (commercial/supplies/production) are acceptable ambiguity — do not force.
    if discovered["candidate_count"] == 0:
        return
    ids = [c["action_id"] for c in discovered["candidates"]]
    production = {
        "get_on_time_delivery_pct",
        "get_production_otd",
        "get_production_otd_series",
    }
    top = ids[0]
    if top in production:
        assert any(
            i.startswith("get_sales_order_otd")
            or i.startswith("get_supplies_otd")
            or i.startswith("get_supplies_purchase_order_otd")
            for i in ids
        ), ids



def test_wave006_execute_projection_end_to_end(monkeypatch):
    set_actions_for_tests(_actions())
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.execute_service.candidate_token_secret",
        lambda: "sec",
    )
    action = _action("get_production_oee")
    token = mint_candidate_token(
        action_id=action.action_id,
        actor_id="u1",
        secret="sec",
        ttl_seconds=300,
    )

    class _Executor:
        def execute(self, *, action_id: str, validated_arguments: dict[str, Any]):
            assert action_id == "get_production_oee"
            assert "operator_code" not in validated_arguments
            return CatalogActionExecutionResult(
                outcome="ok",
                payload={
                    "success": True,
                    "data": {
                        "branch": "01",
                        "start_date": "2026-01-01",
                        "end_date": "2026-01-31",
                        "summary": {
                            "oee_pct": None,
                            "total_appointments": 0,
                            "valid_appointments": 0,
                            "outlier_appointments": 0,
                            "outlier_percentage": 0.0,
                        },
                        "appointments": {
                            "items": [{"operator_code": "SECRET", "appointment_id": 9}]
                        },
                    },
                },
            )

    result = execute_delpi_information(
        candidate_token=token,
        arguments={
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
            "branch": "01",
        },
        actor_id="u1",
        catalog_action_executor=_Executor(),
    )
    data = result.get("data") or result
    assert data.get("summary", {}).get("oee_pct") is None
    assert "appointments" not in data


def test_wave006_no_gpt_actions_impact():
    root = _API_ROOT
    hits = []
    for pattern in ("**/gpt-actions*", "**/*actions*openapi*", "**/gpt_actions*"):
        hits.extend(root.glob(pattern))
    # Residual: Wave 006 must not touch gpt-actions trees if present.
    for path in hits:
        if path.is_file() and "wave_006" in path.name.lower():
            raise AssertionError(f"unexpected wave006 gpt-actions file: {path}")
