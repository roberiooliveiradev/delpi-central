"""DAVI Wave 2 — product economic intelligence freeze evidence (no runtime mutation)."""

from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from app.application.external_capabilities.constants import (
    MCP_TOOL_DISCOVER_DELPI_INFORMATION,
    MCP_TOOL_EXECUTE_DELPI_INFORMATION,
    MCP_TOOL_SEARCH_PRODUCTS,
)
from app.application.external_capabilities.dynamic_information.catalog_builder import (
    TechnicalAction,
    build_technical_actions_from_baseline,
)
from app.application.external_capabilities.dynamic_information.content_loader import (
    load_external_read_allowlist,
)
from app.application.external_capabilities.dynamic_information.projection import (
    apply_approved_field_projection,
)

_API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_API_ROOT / "scripts"))

from davi_wave_002_economic_freeze_lib import (  # noqa: E402
    CURRENT_ELIGIBLE,
    ECONOMIC_QUARANTINE_TOKENS,
    MCP_TOOLS,
    REQUIRED_FREEZE_FIELDS,
    build_documents,
    candidate_records,
    frozen_records,
    git_sha,
    simulation_has_persistence,
    write_artifacts,
)

_WAVE2_OPS = {
    "get_product_pricing",
    "get_product_purchase_price_history",
    "get_product_raw_material_price_intelligence",
    "get_product_cost_impact_simulation",
    "get_product_last_purchase",
    "get_product_summary",
}
_RUNTIME_FILES = (
    "app/content/davi_external_read_allowlist.json",
    "app/content/davi_dynamic_read_budgets.json",
    "app/interface/mcp/server.py",
    "docs/integrations/openai-workspace-agent-davi.md",
)
_HISTORICAL = (
    "docs/integrations/evidence/davi-capability-wave-001-freeze.json",
    "docs/integrations/evidence/davi-capability-wave-001-freeze.md",
    "docs/integrations/evidence/davi-capability-expansion-inventory-001.json",
    "docs/integrations/evidence/davi-capability-expansion-inventory-001.md",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _actions() -> list[TechnicalAction]:
    baseline = json.loads(
        (_API_ROOT / "app/content/openapi_baseline.json").read_text(encoding="utf-8")
    )
    return build_technical_actions_from_baseline(
        baseline, allowlist=load_external_read_allowlist()
    )


def _committed_freeze() -> dict[str, Any]:
    return json.loads(
        (
            _API_ROOT / "docs/integrations/evidence/davi-capability-wave-002-freeze.json"
        ).read_text(encoding="utf-8")
    )


def _committed_inventory() -> dict[str, Any]:
    return json.loads(
        (
            _API_ROOT
            / "docs/integrations/evidence/davi-capability-wave-002-economic-inventory.json"
        ).read_text(encoding="utf-8")
    )


def test_freeze_records_pre_implementation_eligible_baseline() -> None:
    freeze = _committed_freeze()
    assert freeze["current_eligible"] == 10
    assert freeze["expected_eligible_after_implementation"] == 13
    allow = load_external_read_allowlist()
    blocked = {
        item.get("operationId")
        for item in allow.get("explicitlyNotApproved") or []
        if isinstance(item, dict)
    }
    assert "get_product_cost_impact_simulation" in blocked
    eligible = {a.operation_id for a in _actions() if a.executable}
    assert len(eligible) >= 53
    assert set(CURRENT_ELIGIBLE) <= eligible


def test_mcp_tools_remain_two() -> None:
    source = (_API_ROOT / "app/interface/mcp/server.py").read_text(encoding="utf-8")
    assert source.count("@mcp.tool(") == 2
    assert [
        MCP_TOOL_DISCOVER_DELPI_INFORMATION,
        MCP_TOOL_EXECUTE_DELPI_INFORMATION,
    ] == MCP_TOOLS


def test_deferred_wave2_operations_are_not_executable() -> None:
    eligible = {a.operation_id for a in _actions() if a.executable}
    allow = load_external_read_allowlist()
    blocked = {
        item.get("operationId")
        for item in allow.get("explicitlyNotApproved") or []
        if isinstance(item, dict)
    }
    for oid in (
        "get_product_raw_material_price_intelligence",
        "get_product_cost_impact_simulation",
        "get_product_summary",
    ):
        assert oid not in eligible
        assert oid in blocked
    for oid in (
        "get_product_pricing",
        "get_product_purchase_price_history",
        "get_product_last_purchase",
    ):
        assert oid in eligible
        assert oid not in blocked


def test_economic_quarantine_tokens_unchanged() -> None:
    allow = load_external_read_allowlist()
    tokens = allow.get("retrievalQuarantineTokens") or []
    for token in ECONOMIC_QUARANTINE_TOKENS:
        assert token in tokens


def test_agent_instructions_omit_economic_capability_enumeration() -> None:
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
        "get_product_raw_material_price_intelligence",
        "get_product_cost_impact_simulation",
        "get_product_last_purchase",
        "eligible_read = 10",
        "davi_eligible_read",
    ):
        assert banned not in block, banned


def test_simulation_is_compute_only() -> None:
    assert simulation_has_persistence() is False


def test_freeze_records_are_complete_and_wildcard_free() -> None:
    frozen = frozen_records()
    assert [c["capabilityId"] for c in frozen] == [
        "product.commercial.pricing",
        "product.purchase.price_history",
        "product.purchase.last_valid",
    ]
    assert len(frozen) == 3
    for cap in frozen:
        for key in REQUIRED_FREEZE_FIELDS:
            assert key in cap and cap[key] not in (None, ""), key
        assert cap["status"] == "FROZEN_FOR_IMPLEMENTATION"
        assert cap["readPrepareAct"] == "READ"
        assert str(cap["backendAuthz"]).startswith("PROVEN")
        assert cap["identity"] == "END_USER_ACCOUNT"
        assert cap["projectionMode"] == "nested"
        assert cap["perOperationProjectorRequired"] is False
        assert cap["approvedResponseFields"]
        assert not any("*" in f for f in cap["approvedResponseFields"])
        assert cap["semanticAliasesPtBr"]
        assert cap["semanticAliasesEn"]
        assert "preço" not in cap["semanticAliasesPtBr"]
        assert "custo" not in cap["semanticAliasesPtBr"]
        assert "produto" not in cap["semanticAliasesPtBr"]


def test_cost_simulation_is_prepare_deferred_from_read_wave() -> None:
    by_id = {c["capabilityId"]: c for c in candidate_records()}
    sim = by_id["product.cost.impact_simulation"]
    assert sim["readPrepareAct"] == "PREPARE"
    assert sim["status"] == "DEFER_FROM_READ_WAVE"
    assert sim["readWavePromotion"] == "NO"
    assert sim["simulationBoundary"]["computeOnly"] is True
    assert sim["simulationBoundary"]["sideEffects"] == "NONE_PROVEN"
    assert sim["canonicalOperations"] == ["get_product_cost_impact_simulation"]
    frozen_ids = {c["capabilityId"] for c in frozen_records()}
    assert "product.cost.impact_simulation" not in frozen_ids


def test_pricing_does_not_claim_currentness() -> None:
    pricing = next(
        c
        for c in candidate_records()
        if c["capabilityId"] == "product.commercial.pricing"
    )
    name = f"{pricing['businessName']['ptBr']} {pricing['businessName']['en']}"
    need = pricing["businessNeed"]
    blob = f"{name} {need} {pricing['timeSemantics']}".lower()
    assert "atual" not in pricing["businessName"]["ptBr"].lower()
    assert "current" not in pricing["businessName"]["en"].lower()
    assert "current/commercial" not in need.lower()
    assert "current effective" in blob or "não afirmar" in need.lower() or "sem afirmar" in need.lower()


def test_purchase_history_full_period_completeness_not_proven() -> None:
    history = next(
        c
        for c in candidate_records()
        if c["capabilityId"] == "product.purchase.price_history"
    )
    assert history["fullPeriodCompleteness"] == "NOT_PROVEN"
    assert "bounded latest-n" in history["datasetScope"].lower()
    assert "NOT_PROVEN" in history["completeness"]
    assert "must not be interpreted" in history["completeness"].lower()
    assert "complete purchase history for the requested period" not in history["completeness"].lower()


def test_deferred_candidates_have_reasons() -> None:
    by_id = {c["capabilityId"]: c for c in candidate_records()}
    assert by_id["product.raw_material.price_intelligence"]["status"] == "DEFER"
    assert by_id["product.snapshot.summary"]["status"] == "DEFER"
    assert by_id["product.cost.impact_simulation"]["status"] == "DEFER_FROM_READ_WAVE"
    assert by_id["product.raw_material.price_intelligence"]["deferReason"]
    assert by_id["product.snapshot.summary"]["deferReason"]
    assert by_id["product.cost.impact_simulation"]["deferReason"]
    assert by_id["product.raw_material.price_intelligence"]["approvedResponseFields"] == []
    last = by_id["product.purchase.last_valid"]
    assert last["status"] == "FROZEN_FOR_IMPLEMENTATION"
    assert last["canonicalOperations"] == ["get_product_last_purchase"]


def test_generator_validates_source_and_writes_only_wave2_artifacts(tmp_path: Path) -> None:
    before_runtime = {rel: _sha256(_API_ROOT / rel) for rel in _RUNTIME_FILES}
    before_hist = {rel: _sha256(_API_ROOT / rel) for rel in _HISTORICAL}
    source_head = git_sha("HEAD")
    inventory, freeze = build_documents(source_head=source_head, origin_main=source_head)
    assert inventory["sourceValidation"]["ok"] is True
    paths = write_artifacts(inventory, freeze, out_dir=tmp_path)
    for path in paths.values():
        assert path.exists()
        assert path.stat().st_size > 100
    assert before_runtime == {rel: _sha256(_API_ROOT / rel) for rel in _RUNTIME_FILES}
    assert before_hist == {rel: _sha256(_API_ROOT / rel) for rel in _HISTORICAL}


def test_committed_freeze_agrees_with_markdown_and_inventory() -> None:
    freeze = _committed_freeze()
    inventory = _committed_inventory()
    freeze_md = (
        _API_ROOT / "docs/integrations/evidence/davi-capability-wave-002-freeze.md"
    ).read_text(encoding="utf-8")
    inventory_md = (
        _API_ROOT
        / "docs/integrations/evidence/davi-capability-wave-002-economic-inventory.md"
    ).read_text(encoding="utf-8")
    assert freeze["artifact_class"] == "EVIDENCE_NOT_RUNTIME_AUTHORITY"
    assert inventory["metadata"]["artifact_class"] == "EVIDENCE_NOT_RUNTIME_AUTHORITY"
    assert freeze["current_eligible"] == 10
    assert freeze["expected_mcp_tools_after_implementation"] == 3
    assert freeze["agent_instruction_change"] == "NO"
    assert freeze["implementation"] == "NOT_STARTED"
    assert freeze["new_capabilities"] == 3
    assert freeze["wave2_read_additions"] == 3
    assert freeze["expected_eligible_after_implementation"] == 13
    assert freeze["implementationHandoff"]["expectedEligibleCount"] == 13
    assert freeze["implementationHandoff"]["canonicalOperationsToImplement"] == [
        "get_product_pricing",
        "get_product_purchase_price_history",
        "get_product_last_purchase",
    ]
    assert "get_product_cost_impact_simulation" not in freeze[
        "implementationHandoff"
    ]["canonicalOperationsToImplement"]
    assert freeze["implementationHandoff"]["doNotImplement"] == [
        "get_product_cost_impact_simulation"
    ]
    assert freeze["primary_decisions"]["product.cost.impact_simulation"] == (
        "PREPARE / DEFER_FROM_READ_WAVE"
    )
    pricing = next(
        c
        for c in inventory["candidates"]
        if c["capabilityId"] == "product.commercial.pricing"
    )
    assert "atual" not in pricing["businessName"]["ptBr"].lower()
    assert "current" not in pricing["businessName"]["en"].lower()
    history = next(
        c
        for c in inventory["candidates"]
        if c["capabilityId"] == "product.purchase.price_history"
    )
    assert history["fullPeriodCompleteness"] == "NOT_PROVEN"
    for cid in freeze["capability_ids"]:
        assert f"`{cid}`" in freeze_md
        assert cid in inventory_md
    assert freeze["primary_decisions"]["product.raw_material.price_intelligence"] == "DEFER"
    assert "DEFER" in freeze_md
    assert "PREPARE" in freeze_md
    assert "13" in freeze_md
    assert "Current commercial product pricing" not in freeze_md
    assert "Preço comercial atual do produto" not in freeze_md
    inv_status = {c["capabilityId"]: c["status"] for c in inventory["candidates"]}
    freeze_status = {c["capabilityId"]: c["status"] for c in freeze["capabilities"]}
    for cid, status in freeze_status.items():
        assert inv_status[cid] == status == "FROZEN_FOR_IMPLEMENTATION"
        assert cid in freeze_md


def test_source_openapi_and_authz_for_frozen_operations() -> None:
    freeze = _committed_freeze()
    inventory = _committed_inventory()
    proofs = {
        row["operationId"]: row for row in inventory["sourceValidation"]["proofs"]
    }
    for cap in freeze["capabilities"]:
        oid = cap["canonicalOperations"][0]
        proof = proofs[oid]
        assert proof["method"] == "GET"
        assert proof["authz"]["authzEvidence"] == "PROVEN"
        assert proof["currentlyEligible"] is False
        for field in cap["approvedInputFields"]:
            assert field in proof["parameters"]


def test_generic_projector_drops_unapproved_economic_siblings() -> None:
    payload = {
        "product": {"code": "10080001", "description": "MP", "unit": "UN"},
        "prices": [
            {
                "table_code": "001",
                "table_description": "Padrao",
                "sale_price": 1.25,
                "currency": "1",
                "lot_quantity": 1.0,
                "valid_from": "20260101",
                "active": "S",
                "max_price": 9.99,
                "discount_percent": 12.0,
                "internal_debug": True,
                "raw_sql": "SELECT 1",
                "secret": "x",
            }
        ],
        "unexpected": {"cost": 99},
    }
    pricing = next(
        c
        for c in frozen_records()
        if c["capabilityId"] == "product.commercial.pricing"
    )
    projected = apply_approved_field_projection(
        payload, approved_fields=pricing["approvedResponseFields"]
    )
    dumped = json.dumps(projected, default=str)
    assert "1.25" in dumped
    assert "001" in dumped
    assert "max_price" not in dumped
    assert "discount_percent" not in dumped
    assert "internal_debug" not in dumped
    assert "raw_sql" not in dumped
    assert "secret" not in dumped
    assert "unexpected" not in dumped


def test_last_purchase_projection_drops_tax_id() -> None:
    payload = {
        "product": {
            "product_code": "10080001",
            "description": "MP",
            "product_type": "MP",
            "unit": "UN",
            "standard_cost": 0.02,
        },
        "last_purchase": {
            "branch": "01",
            "invoice_number": "000123",
            "issue_date": "20260407",
            "supplier_code": "000002",
            "supplier_name": "TE",
            "quantity": 10,
            "unit_price": 0.089,
            "total_value": 0.89,
            "icms_rate": 12.0,
            "purchase_order": "PC1",
            "supplier_tax_id": "12345678000199",
            "secret": "nope",
        },
    }
    cap = next(
        c for c in frozen_records() if c["capabilityId"] == "product.purchase.last_valid"
    )
    projected = apply_approved_field_projection(
        payload, approved_fields=cap["approvedResponseFields"]
    )
    dumped = json.dumps(projected, default=str)
    assert "000123" in dumped
    assert "0.089" in dumped
    assert "12345678000199" not in dumped
    assert "supplier_tax_id" not in dumped
    assert "standard_cost" not in dumped
    assert "secret" not in dumped


def test_no_new_allowlist_or_mcp_surface() -> None:
    tree = ast.parse(
        (_API_ROOT / "scripts/davi_wave_002_economic_freeze_lib.py").read_text(
            encoding="utf-8"
        )
    )
    assert any(isinstance(node, ast.FunctionDef) for node in tree.body)
    allow = json.loads(
        (_API_ROOT / "app/content/davi_external_read_allowlist.json").read_text(
            encoding="utf-8"
        )
    )
    op_ids = {
        item.get("operationId")
        for item in allow.get("operations") or []
        if isinstance(item, dict)
    }
    assert "get_product_pricing" in op_ids
    assert "get_product_purchase_price_history" in op_ids
    assert "get_product_last_purchase" in op_ids
    assert "get_product_cost_impact_simulation" not in op_ids
    mcp = (_API_ROOT / "app/interface/mcp/server.py").read_text(encoding="utf-8")
    assert mcp.count("@mcp.tool(") == 2
