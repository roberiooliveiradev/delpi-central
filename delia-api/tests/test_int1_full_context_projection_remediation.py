"""INT-1 FULL CONTEXT — RED/GREEN for silent truncation remediation.

Covers catalog description/schema preservation, observation projection
without arbitrary ``[:2000]``, and ``_bounded_json`` essential-field
overflow (pagination / limitations / continuity must survive).
"""

from __future__ import annotations

import json
from pathlib import Path

from app.application.capability_provision.contracts import (
    CapabilityGroup,
    ProviderCapability,
)
from app.application.capability_provision.governed_capability_orchestrator import (
    OperationalCapabilityOrchestrator,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityAttempt,
    GovernedCapabilityStatus,
)
from app.application.interaction.contracts import LIMITATION_RESULT_TRUNCATED
from app.application.interaction.turn_budget import TurnDeadline
from app.domain.evidence.model import SourceRef
from app.domain.specialist_interop.model import (
    InteropProtocol,
    SpecialistOperationClass,
    SpecialistOutcome,
    SpecialistResultProvenance,
    SpecialistResultStatus,
)
from app.infrastructure.config.pydantic_ai_runtime_config import (
    load_pydantic_ai_runtime_config,
)
from app.infrastructure.orchestration.pydantic_ai_investigation import (
    _attempt_projection,
    _bounded_json,
)


_CONFIG_PATH = (
    Path(__file__).resolve().parents[1]
    / "config"
    / "pydantic_ai.runtime.delpi.json"
)


def test_openrouter_qwen_context_matches_provider_capacity():
    config = load_pydantic_ai_runtime_config(
        _CONFIG_PATH, profile_selector="openrouter_qwen"
    )
    profile = config.profile
    assert profile.model.model_name == "qwen/qwen3-14b"
    # OpenRouter published context for qwen/qwen3-14b is 40960.
    assert profile.context.effective_context_window_tokens == 40960
    assert profile.generation.max_output_tokens == 8192
    assert profile.context.prior_turns_limit >= 16
    assert profile.tool_results.max_projection_chars >= 6000


def test_bounded_json_overflow_preserves_pagination_and_limitations():
    payload = {
        "status": "SUCCESS",
        "error_code": None,
        "limitations": [LIMITATION_RESULT_TRUNCATED, "owner_page_incomplete"],
        "investigation_progress": "PARTIAL",
        "pagination": {
            "page": 1,
            "page_size": 40,
            "has_more": True,
            "total_count": 120,
            "items_in_page": 40,
        },
        "continuation_note": (
            "Owner result is truncated or an incomplete page. Continue "
            "with next page parameters — do not treat a single page as "
            "the full population."
        ),
        "evidence_handle": "obs:0",
        "observation_index": 0,
        "authoritative_root_code": "90260921",
        "provenance_specialist": "teo",
        "provenance_capability": "read",
        "content": "PROCESS_ROW_" + ("X" * 8000),
        "bulky": {
            "rows": [
                {"id": f"r{i}", "blob": "Z" * 200} for i in range(80)
            ]
        },
    }
    raw = _bounded_json(payload, limit=2500)
    parsed = json.loads(raw)
    assert parsed.get("truncated") is True
    assert LIMITATION_RESULT_TRUNCATED in (parsed.get("limitations") or [])
    pagination = parsed.get("pagination")
    assert isinstance(pagination, dict)
    assert pagination.get("has_more") is True
    assert pagination.get("page") == 1
    note = (parsed.get("continuation_note") or "").casefold()
    assert "page" in note or "population" in note
    assert parsed.get("authoritative_root_code") == "90260921"
    coverage = (
        parsed.get("coverage_note") or parsed.get("note") or ""
    ).casefold()
    assert (
        "budget" in coverage
        or "truncat" in coverage
        or "complete" in coverage
    )


def test_bounded_json_small_payload_unchanged():
    payload = {"status": "SUCCESS", "content": "ok", "limitations": []}
    assert json.loads(_bounded_json(payload, limit=6000)) == payload


def test_attempt_projection_preserves_long_content_before_budget():
    long_content = "BOM_NODE:" + ("N" * 4500)
    outcome = SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        content_text=long_content,
        structured={
            "data": {"root": {"code": "90260921"}},
            "items": [{"id": f"c{i}"} for i in range(5)],
            "page": 1,
            "page_size": 5,
            "has_more": True,
            "total_count": 40,
        },
        provenance=SpecialistResultProvenance(
            specialist_id="davi",
            remote_name="read",
            protocol=InteropProtocol.MCP,
            correlation_id="full-ctx",
            observed_at="2026-01-01T00:00:00Z",
        ),
        is_complete=False,
    )
    attempt = GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SUCCESS,
        correlation_id="full-ctx",
        content=long_content,
        limitations=(LIMITATION_RESULT_TRUNCATED,),
        outcome=outcome,
    )
    projection = _attempt_projection(attempt, observation_index=0)
    assert projection.get("content") == long_content
    assert len(str(projection.get("content") or "")) > 2000
    assert LIMITATION_RESULT_TRUNCATED in projection["limitations"]
    assert projection.get("pagination", {}).get("has_more") is True


def _project_catalog(groups: dict[str, CapabilityGroup]):
    class _Host:
        def _groups(self, correlation, deadline):  # noqa: ANN001
            return groups, ()

    return OperationalCapabilityOrchestrator._project_semantic_tool_catalog(
        _Host(),  # type: ignore[arg-type]
        correlation="full-ctx-cat",
        deadline=TurnDeadline.start(30.0),
        actor_user_id="user-eval",
    )


def test_catalog_projection_preserves_long_owner_description():
    """Catalog DTO must not silently slice owner MCP descriptions at 320."""
    marker = "OWNER_TAIL:decomposition_tree_is_process_wbs_not_product_bom"
    long_desc = (
        "Semantic read — never writes. entity + typed action + params. "
        + ("y" * 400)
        + " "
        + marker
    )
    assert len(long_desc) > 320
    group = CapabilityGroup(
        provider_id="teo",
        group_id="teo",
        owner_ref="teo",
        display_name="TEO",
        capabilities=(
            ProviderCapability(
                capability_id="teo.read",
                group_id="teo",
                provider_id="teo",
                remote_name="read",
                owner="teo",
                operation_class=SpecialistOperationClass.READ,
                description=long_desc,
                input_schema={
                    "type": "object",
                    "properties": {
                        "entity": {
                            "type": "string",
                            "description": (
                                "Domain entity including "
                                "decomposition_tree (process WBS) — "
                                "not product BOM."
                            ),
                            "enum": [
                                "process",
                                "decomposition_tree",
                                "process_diagram",
                            ],
                        },
                        "action": {"type": "string"},
                        "params": {"type": "object"},
                    },
                    "required": ["entity"],
                },
                binding={"remote_name": "read"},
            ),
        ),
        source=SourceRef(
            source_id="teo",
            source_system="teo",
            provider_name="TEO",
        ),
    )
    catalog = _project_catalog({"teo": group})
    assert len(catalog) == 1
    entry = catalog[0]
    assert entry["description"] == long_desc
    assert marker in entry["description"]
    entity = entry["input_schema"]["properties"]["entity"]
    assert "decomposition_tree" in (entity.get("enum") or [])
    assert "process WBS" in (entity.get("description") or "")
    assert entry["input_schema"]["required"] == ["entity"]


def test_catalog_projection_does_not_hard_cap_at_eighty():
    caps = tuple(
        ProviderCapability(
            capability_id=f"owner.tool_{i}",
            group_id="owner",
            provider_id="owner",
            remote_name=f"tool_{i}",
            owner="owner",
            operation_class=SpecialistOperationClass.READ,
            description=f"tool {i} full description",
            input_schema={"type": "object", "properties": {}},
            binding={"remote_name": f"tool_{i}"},
        )
        for i in range(90)
    )
    group = CapabilityGroup(
        provider_id="owner",
        group_id="owner",
        owner_ref="owner",
        display_name="OWNER",
        capabilities=caps,
        source=SourceRef(
            source_id="owner",
            source_system="owner",
            provider_name="OWNER",
        ),
    )
    catalog = _project_catalog({"owner": group})
    assert len(catalog) == 90
