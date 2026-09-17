"""DAVI Wave 3A — product engineering/planning freeze evidence (no runtime mutation)."""

from __future__ import annotations

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

_API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_API_ROOT / "scripts"))

from davi_wave_003a_product_freeze_lib import (  # noqa: E402
    CURRENT_ELIGIBLE,
    MCP_TOOLS,
    REQUIRED_FREEZE_FIELDS,
    WAVE3A_OPS,
    candidate_records,
    deferred_records,
    freeze_path,
    frozen_records,
    guide_uc_default_max_depth,
    inventory_path,
    load_freeze,
    load_inventory,
    openapi_operation_ids,
    parents_uc_default_max_depth,
    shortages_has_pagination,
    validate_source,
)

_RUNTIME_FILES = (
    "app/content/davi_external_read_allowlist.json",
    "app/content/davi_dynamic_read_budgets.json",
    "app/interface/mcp/server.py",
    "docs/integrations/openai-workspace-agent-davi.md",
)
_HISTORICAL = (
    "docs/integrations/evidence/davi-capability-wave-001-freeze.json",
    "docs/integrations/evidence/davi-capability-wave-002-freeze.json",
    "docs/integrations/evidence/davi-capability-wave-002-implementation.json",
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


def test_runtime_eligible_remains_thirteen() -> None:
    allow = load_external_read_allowlist()
    assert allow.get("version") == 7
    eligible = {a.operation_id for a in _actions() if a.executable}
    assert len(eligible) == 13
    assert set(CURRENT_ELIGIBLE) <= eligible
    for op in WAVE3A_OPS:
        assert op not in eligible


def test_mcp_tools_remain_three() -> None:
    source = (_API_ROOT / "app/interface/mcp/server.py").read_text(encoding="utf-8")
    assert source.count("@mcp.tool(") == 3
    assert [
        MCP_TOOL_SEARCH_PRODUCTS,
        MCP_TOOL_DISCOVER_DELPI_INFORMATION,
        MCP_TOOL_EXECUTE_DELPI_INFORMATION,
    ] == MCP_TOOLS


def test_allowlist_operations_unchanged_from_wave2_set() -> None:
    allow = load_external_read_allowlist()
    ids = [o["operationId"] for o in allow["operations"]]
    assert ids == CURRENT_ELIGIBLE


def test_wave3a_ops_exist_in_openapi_and_are_get() -> None:
    from davi_wave_003a_product_freeze_lib import openapi_operation_methods

    methods = openapi_operation_methods()
    assert set(WAVE3A_OPS) <= set(methods)
    assert all(methods[op] == "get" for op in WAVE3A_OPS)
    assert set(WAVE3A_OPS) <= openapi_operation_ids()


def test_source_validation_passes() -> None:
    result = validate_source()
    assert result["ok"] is True
    assert result["eligibleCount"] == 13
    assert all(result["openapiPresent"].values())
    assert all(result["authz"].values())


def test_freeze_and_inventory_agree() -> None:
    freeze = load_freeze()
    inventory = load_inventory()
    assert freeze["taskId"] == inventory["taskId"]
    assert freeze["current_eligible"] == 13
    assert freeze["expected_mcp_tools_after_implementation"] == 3
    assert freeze["agent_instruction_change"] == "NO"
    frozen_ids = {c["capabilityId"] for c in freeze["capabilities"]}
    assert frozen_ids == set(freeze["capability_ids"])
    inv_frozen = {
        c["capabilityId"]
        for c in inventory["candidates"]
        if c["status"] == "FROZEN_FOR_IMPLEMENTATION"
    }
    assert frozen_ids == inv_frozen == {
        "product.routing.guide",
        "product.where_used",
    }
    assert freeze["deferred_capability_ids"] == ["product.raw_material.set_shortages"]
    assert freeze["expected_eligible_after_implementation"] == 15


def test_markdown_artifacts_exist_and_mention_decisions() -> None:
    freeze_md = (
        _API_ROOT / "docs/integrations/evidence/davi-capability-wave-003a-freeze.md"
    ).read_text(encoding="utf-8")
    inv_md = (
        _API_ROOT / "docs/integrations/evidence/davi-capability-wave-003a-inventory.md"
    ).read_text(encoding="utf-8")
    assert "product.routing.guide" in freeze_md
    assert "product.where_used" in freeze_md
    assert "product.raw_material.set_shortages" in freeze_md
    assert "FROZEN_FOR_IMPLEMENTATION" in inv_md
    assert "DEFER" in inv_md
    assert freeze_path().exists() and inventory_path().exists()


def test_frozen_capabilities_have_complete_contracts() -> None:
    for cap in frozen_records():
        for field in REQUIRED_FREEZE_FIELDS:
            assert field in cap, f"{cap['capabilityId']} missing {field}"
        assert cap["approvedResponseFields"], cap["capabilityId"]
        assert "*" not in "".join(cap["approvedResponseFields"])
        assert "..." not in "".join(cap["approvedResponseFields"])
        assert cap["readPrepareAct"] == "READ"
        assert cap["perOperationProjectorRequired"] is False
        assert (
            cap["projectionFeasibility"]
            == "SUPPORTED_BY_CURRENT_GENERIC_PROJECTOR"
        )
        limits = cap["argumentConstraints"]["argumentLimits"]
        assert limits["page_size"]["maximum"] == 50
        if cap["capabilityId"] == "product.routing.guide":
            assert limits["max_depth"]["maximum"] == 8
            assert limits["max_depth"]["default"] == 8
        elif cap["capabilityId"] == "product.where_used":
            assert limits["max_depth"]["minimum"] == 1
            assert limits["max_depth"]["maximum"] == 4
            assert limits["max_depth"]["default"] == 4
            assert cap["limits"]["maxDepth"] == 4
            assert cap["limits"]["modelVisibleNestingLevels"] == 4


def test_where_used_requested_depth_equals_model_visible_depth() -> None:
    where = next(
        c for c in candidate_records() if c["capabilityId"] == "product.where_used"
    )
    md = where["argumentConstraints"]["argumentLimits"]["max_depth"]
    assert md["maximum"] == where["limits"]["modelVisibleNestingLevels"] == 4
    assert md["default"] == 4
    assert md["maximum"] <= where["limits"]["modelVisibleNestingLevels"]
    blob = f"{where['completeness']} {where['limits']['note']}".lower()
    assert "max_depth is 4" in blob or "maximum depth (4)" in blob
    assert "may be 8" not in blob
    assert "hidden level" in blob or "requested depth" in blob
    # no stale 8-vs-4 contract
    assert "while max_depth may be 8" not in where.get("openGaps", [])


def test_routing_max_depth_remains_eight() -> None:
    routing = next(
        c for c in candidate_records() if c["capabilityId"] == "product.routing.guide"
    )
    md = routing["argumentConstraints"]["argumentLimits"]["max_depth"]
    assert md["maximum"] == 8
    assert md["default"] == 8
    assert routing["limits"]["maxDepth"] == 8


def test_shortages_cannot_freeze_without_computation_bound() -> None:
    shortages = next(
        c
        for c in candidate_records()
        if c["capabilityId"] == "product.raw_material.set_shortages"
    )
    assert shortages["status"] == "DEFER"
    assert shortages["approvedResponseFields"] == []
    assert shortages["backendComputationBound"] == "NOT_PROVEN_UNBOUNDED_RELATIVE"
    assert shortages_has_pagination() is False
    assert "deferReason" in shortages and shortages["deferReason"]
    assert shortages["capabilityId"] not in {
        c["capabilityId"] for c in frozen_records()
    }


def test_guide_and_parents_default_max_depth_risk_documented() -> None:
    """Backend UC still defaults to 999; DAVI freeze must document governed caps."""
    assert guide_uc_default_max_depth() == 999
    assert parents_uc_default_max_depth() == 999
    routing = next(
        c for c in candidate_records() if c["capabilityId"] == "product.routing.guide"
    )
    where = next(
        c for c in candidate_records() if c["capabilityId"] == "product.where_used"
    )
    assert "999" in json.dumps(routing["limits"], ensure_ascii=False)
    assert "999" in json.dumps(where["limits"], ensure_ascii=False)
    assert routing["argumentConstraints"]["argumentLimits"]["max_depth"]["default"] == 8
    assert where["argumentConstraints"]["argumentLimits"]["max_depth"]["default"] == 4


def test_routing_aliases_do_not_collide_with_structure_tokens() -> None:
    routing = next(
        c for c in candidate_records() if c["capabilityId"] == "product.routing.guide"
    )
    aliases = " ".join(routing["semanticAliasesPtBr"] + routing["semanticAliasesEn"]).lower()
    assert "estrutura" not in aliases
    assert "bom" not in aliases.split()
    assert "produção" not in routing["semanticAliasesPtBr"]  # bare token forbidden
    assert "roteiro do produto" in routing["semanticAliasesPtBr"]


def test_where_used_aliases_avoid_bare_structure_tokens() -> None:
    where = next(
        c for c in candidate_records() if c["capabilityId"] == "product.where_used"
    )
    bare_forbidden = {"estrutura", "bom", "pais", "produção", "produto"}
    for alias in where["semanticAliasesPtBr"] + where["semanticAliasesEn"]:
        assert alias.strip().lower() not in bare_forbidden
    assert "onde o produto é usado" in where["semanticAliasesPtBr"]
    assert where["validitySemantics"].startswith("CURRENT VALID")
    assert "RECURSIVE" in where["directOrRecursive"]


def test_no_wave3a_operation_became_executable() -> None:
    allow = load_external_read_allowlist()
    blocked = {
        item.get("operationId")
        for item in allow.get("explicitlyNotApproved") or []
        if isinstance(item, dict)
    }
    # Wave 3A ops are simply absent from allowlist operations (not necessarily blocked list)
    eligible = {a.operation_id for a in _actions() if a.executable}
    for op in WAVE3A_OPS:
        assert op not in eligible
        assert op not in {o["operationId"] for o in allow["operations"]}


def test_historical_wave_artifacts_untouched_by_presence() -> None:
    for rel in _HISTORICAL:
        assert (_API_ROOT / rel).exists()


def test_freeze_does_not_require_runtime_file_edits() -> None:
    """Sanity: runtime hashes readable; freeze task must not have changed them in-test."""
    before = {rel: _sha256(_API_ROOT / rel) for rel in _RUNTIME_FILES}
    _ = load_freeze()
    _ = load_inventory()
    _ = validate_source()
    after = {rel: _sha256(_API_ROOT / rel) for rel in _RUNTIME_FILES}
    assert before == after


def test_deferred_records_helper() -> None:
    deferred = deferred_records()
    assert len(deferred) == 1
    assert deferred[0]["capabilityId"] == "product.raw_material.set_shortages"
