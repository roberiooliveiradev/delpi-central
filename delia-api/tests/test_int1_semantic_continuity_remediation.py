"""INT-1 — semantic object match + investigation continuity remediation.

RED/GREEN for defects proven in Doc 307 live M1:

1. Owner-declared GUIDANCE_NOT_DOMAIN_TRUTH must not be citable
   business evidence (continuity trap toward guidance catalogs).
2. NO_PROGRESS with open identifiers surfaces a continuity note.
3. Default instruction evolves to v2-1 object-continuity; historical
   v2 fingerprint remains intact for rollback.
"""

from __future__ import annotations

import hashlib

from app.application.capability_provision.semantic_capability_support import (
    INVESTIGATION_PROGRESS_NONE,
    _is_business_evidence_attempt,
    _owner_declares_guidance_only,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityAttempt,
    GovernedCapabilityStatus,
)
from app.application.interaction.contracts import (
    GovernedCapabilityProvenance,
)
from app.domain.evidence.model import SourceRef
from app.domain.specialist_interop.model import (
    InteropProtocol,
    SpecialistOutcome,
    SpecialistResultProvenance,
    SpecialistResultStatus,
)
from app.infrastructure.orchestration import pydantic_ai_investigation as pai
from app.infrastructure.orchestration.pydantic_ai_investigation import (
    _attempt_projection,
)


def _prov() -> GovernedCapabilityProvenance:
    return GovernedCapabilityProvenance(
        source_refs=(
            SourceRef(
                source_id="owner",
                source_system="owner",
                provider_name="owner",
                observed_at="2026-01-01T00:00:00Z",
            ),
        ),
        specialist_id="owner",
        remote_capability="read",
        action_id="read",
        protocol=InteropProtocol.MCP.value,
        observed_at="2026-01-01T00:00:00Z",
        correlation_id="c1",
        is_complete=True,
    )


def _attempt(*, content: str, structured: dict) -> GovernedCapabilityAttempt:
    outcome = SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        content_text=content,
        structured=structured,
        provenance=SpecialistResultProvenance(
            specialist_id="owner",
            remote_name="read",
            protocol=InteropProtocol.MCP,
            correlation_id="c1",
            observed_at="2026-01-01T00:00:00Z",
        ),
        is_complete=True,
    )
    return GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SUCCESS,
        correlation_id="c1",
        content=content,
        limitations=(),
        outcome=outcome,
        provenance=_prov(),
    )


def test_guidance_authority_is_not_business_evidence():
    structured = {
        "status": "success",
        "data": {
            "schema": "product_guide_index_v1",
            "authority": "GUIDANCE_NOT_DOMAIN_TRUTH",
            "sections": ["overview"],
        },
    }
    assert _owner_declares_guidance_only(structured) is True
    attempt = _attempt(content="guide index", structured=structured)
    assert _is_business_evidence_attempt(attempt) is False


def test_operational_structure_payload_remains_business_evidence():
    structured = {
        "capability": "structure_read",
        "status": "ok",
        "data": {
            "root": {"code": "ABC"},
            "components": [{"code": "X", "qty": 1}],
        },
    }
    assert _owner_declares_guidance_only(structured) is False
    attempt = _attempt(content="structure ok", structured=structured)
    assert _is_business_evidence_attempt(attempt) is True


def test_no_progress_projection_emits_continuity_coverage_note():
    attempt = GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SOURCE_UNAVAILABLE,
        correlation_id="c1",
        content="not found",
        limitations=(),
        outcome=None,
        error_code="owner_not_found",
    )
    projection = _attempt_projection(
        attempt,
        observation_index=0,
        uncovered_after=("ABC123",),
    )
    assert projection["investigation_progress"] == INVESTIGATION_PROGRESS_NONE
    assert projection.get("uncovered_user_identifiers") == ["ABC123"]
    note = projection.get("coverage_note") or ""
    assert "No objective progress" in note or "open identifiers" in note.casefold()
    assert "90260921" not in note
    assert "davi" not in note.lower()
    assert "teo" not in note.lower()


def test_default_instruction_is_v2_4_typed_objective():
    selected = pai.load_selected_investigation_instructions()
    assert (
        selected.instruction_version
        == "generalist-semantic-v2-4-typed-objective"
    )
    assert selected.text_fingerprint == "9737ae1d9d281974"
    # v2-3 and v2-2 remain selectable for rollback (preserved
    # fingerprints).
    v23 = pai.load_selected_investigation_instructions(
        instruction_version="generalist-semantic-v2-3-enumeration-intent"
    )
    assert v23.text_fingerprint == "95e265ee18cd5d66"
    v22 = pai.load_selected_investigation_instructions(
        instruction_version="generalist-semantic-v2-2-object-authz-continuity"
    )
    assert v22.text_fingerprint == "3692299dac74c26e"
    text = selected.text
    assert "Linguistic similarity alone is not enough" in text
    assert "Shared hierarchical vocabulary" in text
    assert "AUTHZ_DENIED" in text
    assert "GUIDANCE_NOT_DOMAIN_TRUTH" in text
    for banned in (
        "90260921",
        "DAVI",
        "TEO",
        "VISTA",
        "get_product_structure",
        "decomposition_tree",
    ):
        assert banned not in text


def test_historical_v2_and_v2_1_fingerprints_preserved_for_rollback():
    v2 = pai.load_selected_investigation_instructions(
        instruction_version="generalist-semantic-v2"
    )
    assert v2.text_fingerprint == "7dbc94c5035b0f19"
    assert (
        hashlib.sha256(v2.text.encode()).hexdigest()[:16]
        == "7dbc94c5035b0f19"
    )
    v21 = pai.load_selected_investigation_instructions(
        instruction_version="generalist-semantic-v2-1-object-continuity"
    )
    assert v21.text_fingerprint == "4ebd5260b6cf9ba9"
