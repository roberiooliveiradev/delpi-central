"""S02/R07 — partial owner completeness must remain citable when transport is complete.

Owner business payload may declare data.is_complete=false (partial tree)
while the MCP transport outcome remains complete. That limitation must be
preserved for the user, but must not erase citability of the authoritative
root already returned.
"""

from __future__ import annotations

from app.application.capability_provision.semantic_capability_support import (
    _authoritative_structure_root,
    _is_business_evidence_attempt,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityAttempt,
    GovernedCapabilityProvenance,
    GovernedCapabilityStatus,
    SourceRef,
)
from app.domain.specialist_interop.model import (
    InteropProtocol,
    SpecialistOutcome,
    SpecialistResultProvenance,
    SpecialistResultStatus,
)


def test_s02_partial_tree_preserves_authoritative_root_citability() -> None:
    structured = {
        "status": "ok",
        "data": {
            "root": {
                "code": "90260921",
                "description": "21010421 CHICOTE DE LIGACAO",
                "type": "PA",
                "unit": "MI",
            },
            "components": [{"code": "10020003", "quantity": 175}],
            "is_complete": False,
        },
    }
    content = (
        "Produto 90260921 — 21010421 CHICOTE DE LIGACAO (PA).\n"
        "Componente 10020003 qty=175.\n"
        "is_complete=false"
    )
    outcome = SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        provenance=SpecialistResultProvenance(
            specialist_id="davi",
            remote_name="read",
            protocol=InteropProtocol.MCP,
            correlation_id="c-partial",
            observed_at="2026-01-01T00:00:00Z",
        ),
        content_text=content,
        is_complete=True,
        structured=structured,
        limitations=("owner declared is_complete=false",),
    )
    attempt = GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SUCCESS,
        correlation_id="c-partial",
        outcome=outcome,
        provenance=GovernedCapabilityProvenance(
            source_refs=(
                SourceRef(
                    source_id="davi",
                    source_system="davi",
                    provider_name="davi",
                    observed_at="2026-01-01T00:00:00Z",
                ),
            ),
            specialist_id="davi",
            remote_capability="read",
            action_id="get_product_structure",
            protocol=InteropProtocol.MCP.value,
            observed_at="2026-01-01T00:00:00Z",
            correlation_id="c-partial",
            is_complete=True,
        ),
        content=content,
        limitations=("owner declared is_complete=false",),
    )
    assert _is_business_evidence_attempt(attempt) is True
    assert _authoritative_structure_root(attempt) == "90260921"
    assert "is_complete=false" in (attempt.content or "")


def test_structured_owner_incomplete_detects_data_flag() -> None:
    from app.application.capability_provision.semantic_capability_support import (
        _structured_owner_incomplete,
    )
    from app.domain.specialist_interop.model import (
        InteropProtocol,
        SpecialistOutcome,
        SpecialistResultProvenance,
        SpecialistResultStatus,
    )

    complete = SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        provenance=SpecialistResultProvenance(
            specialist_id="davi",
            remote_name="read",
            protocol=InteropProtocol.MCP,
            correlation_id="c1",
            observed_at="2026-01-01T00:00:00Z",
        ),
        content_text="ok",
        is_complete=True,
        structured={"data": {"root": {"code": "1"}, "is_complete": True}},
    )
    partial = SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        provenance=complete.provenance,
        content_text="ok",
        is_complete=True,
        structured={"data": {"root": {"code": "1"}, "is_complete": False}},
    )
    assert _structured_owner_incomplete(complete) is False
    assert _structured_owner_incomplete(partial) is True


def test_s02_rendered_content_preserves_root_and_partial_flag() -> None:
    from app.application.capability_provision.conversational_response import (
        _business_lines,
    )

    lines = _business_lines(
        {
            "status": "ok",
            "data": {
                "root": {
                    "code": "90260921",
                    "description": "21010421 CHICOTE DE LIGACAO",
                    "type": "PA",
                    "unit": "MI",
                },
                "items": [{"code": "10020003", "quantity": 175}],
                "is_complete": False,
            },
        }
    )
    blob = "\n".join(lines or [])
    assert "90260921" in blob
    assert "10020003" in blob
    assert "is_complete: false" in blob


def test_s03_discovery_metadata_is_not_business_evidence() -> None:
    outcome = SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        provenance=SpecialistResultProvenance(
            specialist_id="davi",
            remote_name="get_context",
            protocol=InteropProtocol.MCP,
            correlation_id="c-disc",
            observed_at="2026-01-01T00:00:00Z",
        ),
        content_text="catalog listed",
        is_complete=True,
        structured={"capabilities": [{"id": "get_product_structure"}]},
    )
    attempt = GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SUCCESS,
        correlation_id="c-disc",
        outcome=outcome,
        provenance=GovernedCapabilityProvenance(
            source_refs=(
                SourceRef(
                    source_id="davi",
                    source_system="davi",
                    provider_name="davi",
                    observed_at="2026-01-01T00:00:00Z",
                ),
            ),
            specialist_id="davi",
            remote_capability="get_context",
            action_id="get_context",
            protocol=InteropProtocol.MCP.value,
            observed_at="2026-01-01T00:00:00Z",
            correlation_id="c-disc",
            is_complete=True,
        ),
        content="catalog listed",
        limitations=("discovery_metadata_observation",),
    )
    assert _is_business_evidence_attempt(attempt) is False
