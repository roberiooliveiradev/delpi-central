"""Structural anti-drift: catalog/MCP guidance must not teach removed V1 surfaces as current."""

from __future__ import annotations

import json

from tm_app.application.gpt_actions.improvement_package_contract import (
    OPERATIONAL_SEQUENCE,
    build_package_hints,
)
from tm_app.application.gpt_actions.openapi_builder import GPT_ACTIONS_OPERATION_IDS
from tm_app.application.gpt_actions.registration_guide import build_registration_guide
from tm_app.interface.mcp.constants import (
    MCP_LEGACY_REMOVED_TOOLS,
    MCP_SURFACE_BUDGET,
    MCP_TOOL_NAMES,
    TEO_MCP_SURFACE,
)


_REMOVED_ACTION_OPS = (
    "gpt_create_record",
    "gpt_update_record",
    "gpt_delete_record",
    "gpt_duplicate_record",
    "gpt_commit_improvement_package",
)

_CURRENT_V2_MARKERS = (
    "gpt_prepare_record_change",
    "gpt_commit_proposal",
)


def _entity_schemas_blob(guide: dict) -> str:
    return json.dumps(guide.get("entity_schemas") or {}, ensure_ascii=False)


def test_builder_visible_ops_exclude_legacy_crud():
    for op in _REMOVED_ACTION_OPS:
        assert op not in GPT_ACTIONS_OPERATION_IDS
    assert "gpt_prepare_record_change" in GPT_ACTIONS_OPERATION_IDS
    assert "gpt_commit_proposal" in GPT_ACTIONS_OPERATION_IDS
    assert len(GPT_ACTIONS_OPERATION_IDS) == 18


def test_registration_guide_teaches_v2_not_legacy_crud_as_current():
    guide = build_registration_guide()
    rules = guide["write_contract_rules"]
    assert rules["surface"] == "GOVERNED_PREPARE_COMMIT_V2"
    for marker in _CURRENT_V2_MARKERS:
        assert marker in rules["entity_write_flow"]
    # Entity notes must not instruct removed ops as the write path.
    schemas_blob = _entity_schemas_blob(guide)
    for op in _REMOVED_ACTION_OPS:
        assert op not in schemas_blob, f"entity_schemas still teaches {op}"
    assert "gpt_prepare_record_change" in schemas_blob
    assert "Always send {data:" not in json.dumps(rules, ensure_ascii=False)
    assert "changes" in rules["changes_wrapper"]


def test_package_hints_commit_via_proposal():
    hints = build_package_hints()
    assert hints["commit_operationId"] == "gpt_commit_proposal"
    assert hints["validate_operationId"] == "gpt_validate_improvement_package"
    seq = " ".join(OPERATIONAL_SEQUENCE)
    assert "gpt_commit_proposal" in seq
    assert "gpt_commit_improvement_package" in seq  # only as "not …"
    assert "not gpt_commit_improvement_package" in seq
    flow = hints["governed_document_writes"]["flow"]
    assert "COMMIT" in flow
    assert "WRITE →" not in flow


def test_mcp_surface_budget_matches_registration():
    assert TEO_MCP_SURFACE == "CAPABILITY_GOVERNED_V2"
    assert MCP_SURFACE_BUDGET["before_total"] == 33
    assert MCP_SURFACE_BUDGET["after_total"] == 20
    assert len(MCP_TOOL_NAMES) == 20
    assert "prepare_record_change" in MCP_TOOL_NAMES
    assert "commit_proposal" in MCP_TOOL_NAMES
    for name in MCP_LEGACY_REMOVED_TOOLS:
        assert name not in MCP_TOOL_NAMES


def test_process_document_guidance_is_generic_entity():
    notes = " ".join(
        build_registration_guide()["entity_schemas"]["process_document"]["notes"]
    )
    assert "ENTITY" in notes or "entity" in notes.lower()
    assert "gpt_prepare_record_change" in notes
    assert "gpt_commit_proposal" in notes
    assert "gpt_create_record" not in notes
