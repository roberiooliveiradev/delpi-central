"""Evidence-only tests for DAVI capability expansion inventory generation."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from app.application.external_capabilities.constants import (
    MCP_TOOL_DISCOVER_DELPI_INFORMATION,
    MCP_TOOL_EXECUTE_DELPI_INFORMATION,
    MCP_TOOL_SEARCH_PRODUCTS,
)
from app.application.external_capabilities.dynamic_information.content_loader import (
    load_external_read_allowlist,
)
from app.application.external_capabilities.dynamic_information.eligibility import (
    load_allowlist_operation_ids,
)

_API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_API_ROOT / "scripts"))

from davi_capability_expansion_lib import (  # noqa: E402
    build_actions,
    build_inventory_document,
    freeze_records,
    git_sha,
    write_artifacts,
)

_ELIGIBLE = {
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
}


_HISTORICAL = (
    "docs/integrations/evidence/davi-api-delpi-operation-inventory.json",
    "docs/integrations/evidence/davi-api-delpi-operation-inventory.md",
    "docs/integrations/evidence/davi-governed-read-coverage-rebaseline-001.json",
    "app/content/davi_external_read_allowlist.json",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_current_eligible_set_matches_allowlist() -> None:
    actions = build_actions()
    eligible = {a.operation_id for a in actions if a.executable}
    baseline = json.loads(
        (_API_ROOT / "app/content/openapi_baseline.json").read_text(encoding="utf-8")
    )
    expected_total = int(baseline.get("operation_count") or 0)
    assert len(actions) == expected_total
    assert sum(1 for a in actions if a.method == "GET") == sum(
        1 for a in actions if str(a.method).upper() == "GET"
    )
    assert eligible == _ELIGIBLE
    assert len(eligible) == 53


def test_mcp_tools_remain_three() -> None:
    source = (_API_ROOT / "app/interface/mcp/server.py").read_text(encoding="utf-8")
    assert source.count("@mcp.tool(") == 3
    assert "name=MCP_TOOL_SEARCH_PRODUCTS" in source
    assert "name=MCP_TOOL_DISCOVER_DELPI_INFORMATION" in source
    assert "name=MCP_TOOL_EXECUTE_DELPI_INFORMATION" in source
    assert [
        MCP_TOOL_SEARCH_PRODUCTS,
        MCP_TOOL_DISCOVER_DELPI_INFORMATION,
        MCP_TOOL_EXECUTE_DELPI_INFORMATION,
    ] == [
        "search_products",
        "discover_delpi_information",
        "execute_delpi_information",
    ]
    assert load_allowlist_operation_ids(load_external_read_allowlist()) == _ELIGIBLE


def test_inventory_covers_all_gets_and_freezes_wave1(tmp_path: Path) -> None:
    source_head = git_sha("HEAD")
    doc = build_inventory_document(source_head=source_head, origin_main=source_head)
    get_rows = [r for r in doc["technical_operations"] if r["method"] == "GET"]
    actions = build_actions()
    assert len(get_rows) == sum(1 for a in actions if a.method == "GET")
    assert all(r.get("bounded_context") for r in get_rows)
    assert all(r.get("current_davi_disposition") for r in get_rows)

    frozen = freeze_records(doc["capabilities"])
    assert [c["capability_id"] for c in frozen] == [
        "product.factory.status",
        "product.structure.exclusivity",
        "product.shipping.status",
    ]
    for cap in frozen:
        assert cap["READ_PREPARE_ACT"] == "READ"
        assert cap["identity_model"] == "END_USER_ACCOUNT"
        assert cap["business_authz_owner"] == "NONE"
        assert str(cap["backend_authz"]).startswith("PROVEN")
        assert cap["required_inputs"]
        assert cap["output_allowlist_candidate"]
        assert not any("*" in f for f in cap["output_allowlist_candidate"])
        assert cap["retrieval_aliases_ptbr"]
        assert cap["projection_mode"] == "nested"
        assert cap["negative_authz_test_required"] == "YES"

    assert doc["wave_1_freeze"]["current_eligible"] == 53
    assert doc["wave_1_freeze"]["new_capabilities"] == 3
    assert doc["wave_1_freeze"]["expected_eligible_after_implementation"] == 56
    assert doc["wave_1_freeze"]["expected_mcp_tools_after_implementation"] == 3
    assert doc["wave_1_freeze"]["agent_instruction_change"] == "NO"

    seeded = doc["seeded_candidate_decisions"]
    assert seeded["get_product_detail"] == "REDUNDANT"
    assert seeded["get_product_summary"] == "DEFER"
    assert seeded["get_product_factory_status"] == "PROMOTE"
    assert seeded["get_product_structure_exclusivity"] == "PROMOTE"
    assert seeded["get_product_pricing"] == "DEFER"

    paths = write_artifacts(doc, out_dir=tmp_path)
    for path in paths.values():
        assert path.exists()
        assert path.stat().st_size > 100


def test_generator_does_not_change_runtime_or_historical_hashes() -> None:
    before = {rel: _sha256(_API_ROOT / rel) for rel in _HISTORICAL}
    source_head = git_sha("HEAD")
    build_inventory_document(source_head=source_head, origin_main=source_head)
    after = {rel: _sha256(_API_ROOT / rel) for rel in _HISTORICAL}
    assert before == after


def test_committed_artifacts_are_evidence_not_runtime() -> None:
    inventory = json.loads(
        (
            _API_ROOT
            / "docs/integrations/evidence/davi-capability-expansion-inventory-001.json"
        ).read_text(encoding="utf-8")
    )
    freeze = json.loads(
        (
            _API_ROOT / "docs/integrations/evidence/davi-capability-wave-001-freeze.json"
        ).read_text(encoding="utf-8")
    )
    assert inventory["metadata"]["artifact_class"] == "EVIDENCE_NOT_RUNTIME_AUTHORITY"
    assert freeze["artifact_class"] == "EVIDENCE_NOT_RUNTIME_AUTHORITY"
    assert inventory["runtime_invariants"]["eligible_must_remain"] == 7
    assert inventory["runtime_invariants"]["mcp_tools_must_remain"] == 3
    assert inventory["technical_operation_counts"]["DAVI_ELIGIBLE_READ"] == 7
    assert "product.factory.status" in inventory["wave_1_freeze"]["capability_ids"]
