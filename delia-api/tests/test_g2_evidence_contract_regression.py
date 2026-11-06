"""G2 bounded rework — evidence-contract negative regression (doc 257).

The retired semantic assessors are gone for good. These tests pin the
invariants that still matter on the ACTIVE code path — the deterministic
owner-payload projection in ``generic_evidence_renderer`` and the
governed-attempt evidence gates in ``orchestration``:

* DISCOVERY metadata never becomes business evidence.
* A partial page never becomes an authoritative total.
* SourceRefs / owner outcomes still bound real evidence.
* Sensitive fields stay redacted; control-plane keys never render.
* Malformed or fabricated pagination is never promoted to a fact.
* Count wording only asserts what the owner actually proved.
"""

from __future__ import annotations

from app.application.capability_provision.generic_evidence_renderer import (
    REDACTION_MARKER,
    CountResolutionKind,
    PageAggregationResult,
    PaginationEnvelope,
    _mapping_items_excluding_control,
    _redact_text,
    _sanitize_renderable,
    aggregate_paginated_pages,
    extract_pagination_envelope,
    resolve_count_semantics,
)
from app.application.capability_provision.governed_capability_orchestrator import (
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

# ------------------------------------------------------------------
# helpers
# ------------------------------------------------------------------


def _outcome(
    structured=None,
    *,
    text="owner content",
    complete=True,
) -> SpecialistOutcome:
    return SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        provenance=SpecialistResultProvenance(
            specialist_id="pa",
            remote_name="search_items",
            protocol=InteropProtocol.MCP,
            correlation_id="c1",
            observed_at="2026-01-01T00:00:00Z",
        ),
        content_text=text,
        is_complete=complete,
        structured=structured,
    )


def _attempt(
    outcome: SpecialistOutcome | None,
    *,
    limitations: tuple[str, ...] = (),
    content: str | None = "rendered",
    prov_complete: bool = True,
) -> GovernedCapabilityAttempt:
    return GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SUCCESS,
        correlation_id="c1",
        outcome=outcome,
        provenance=GovernedCapabilityProvenance(
            source_refs=(
                SourceRef(
                    source_id="pa",
                    source_system="pa",
                    provider_name="pa",
                    observed_at="2026-01-01T00:00:00Z",
                ),
            ),
            specialist_id="pa",
            remote_capability="search_items",
            action_id="search_items",
            protocol=InteropProtocol.MCP.value,
            observed_at="2026-01-01T00:00:00Z",
            correlation_id="c1",
            is_complete=prov_complete,
        ),
        content=content,
        limitations=limitations,
    )


def _page(*, page=1, items=(), has_more=None, total=None):
    out: dict[str, object] = {"items": list(items), "page": page}
    if has_more is not None:
        out["has_more"] = has_more
    if total is not None:
        out["total_count"] = total
    return out


# ------------------------------------------------------------------
# DISCOVERY metadata never becomes business evidence
# ------------------------------------------------------------------


def test_discovery_metadata_limitation_is_never_business_evidence():
    outcome = _outcome(structured={"capabilities": [{"name": "x"}]})
    attempt = _attempt(
        outcome, limitations=("discovery_metadata_observation",)
    )
    assert _is_business_evidence_attempt(attempt) is False


def test_attempt_without_provenance_is_never_business_evidence():
    attempt = _attempt(_outcome())
    attempt = GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SUCCESS,
        correlation_id="c1",
        outcome=attempt.outcome,
        provenance=None,
        content="rendered",
    )
    assert _is_business_evidence_attempt(attempt) is False


def test_incomplete_outcome_is_never_business_evidence():
    attempt = _attempt(_outcome(complete=False))
    assert _is_business_evidence_attempt(attempt) is False


def test_real_owner_result_still_counts_as_business_evidence():
    outcome = _outcome(structured={"items": [{"id": "1"}]})
    assert _is_business_evidence_attempt(_attempt(outcome)) is True


# ------------------------------------------------------------------
# partial page never becomes an authoritative total
# ------------------------------------------------------------------


def test_page_slice_without_total_never_resolves_to_total():
    structured = _page(page=1, items=[{"id": i} for i in range(10)],
                       has_more=True)
    envelope = extract_pagination_envelope(structured)
    assert envelope is not None and envelope.has_more is True
    resolution = resolve_count_semantics(envelope)
    assert resolution.total is None
    assert resolution.kind is not CountResolutionKind.AUTHORITATIVE_TOTAL
    assert resolution.kind is not CountResolutionKind.COMPLETE_AGGREGATE


def test_incomplete_aggregation_never_fabricates_total():
    agg = PageAggregationResult(
        items=({"id": "1"}, {"id": "2"}),
        pages_fetched=1,
        complete=False,
        duplicate_ids=(),
        failed=False,
        failure_reason=None,
        authoritative_total=None,
    )
    resolution = resolve_count_semantics(None, aggregation=agg)
    assert resolution.total is None


def test_failed_aggregation_never_fabricates_total():
    agg = PageAggregationResult(
        items=({"id": "1"},),
        pages_fetched=1,
        complete=False,
        duplicate_ids=(),
        failed=True,
        failure_reason="owner_error",
        authoritative_total=None,
    )
    assert resolve_count_semantics(None, aggregation=agg).total is None


def test_owner_declared_total_is_the_only_authoritative_total():
    structured = _page(page=1, items=[{"id": "1"}], has_more=True,
                       total=42)
    envelope = extract_pagination_envelope(structured)
    resolution = resolve_count_semantics(envelope)
    assert resolution.total == 42
    assert resolution.kind is CountResolutionKind.AUTHORITATIVE_TOTAL


def test_count_message_never_claims_unproven_total():
    structured = _page(page=1, items=[{"id": i} for i in range(5)],
                       has_more=True)
    envelope = extract_pagination_envelope(structured)
    resolution = resolve_count_semantics(envelope)
    # the visible-page count may be stated as a *page* count, never as
    # the total — total must stay unproven.
    assert resolution.total is None
    assert "5" not in (resolution.message or "").split(" total")


# ------------------------------------------------------------------
# sensitive fields stay redacted / control-plane keys never render
# ------------------------------------------------------------------


def test_sensitive_values_redacted_in_projection():
    node = {
        "token": "secret-bearer-value",
        "password": "hunter2",
        "api_key": "sk-abc123",
        "name": "public value",
    }
    projected = _sanitize_renderable(node)
    rendered = repr(projected)
    assert "secret-bearer-value" not in rendered
    assert "hunter2" not in rendered
    assert "sk-abc123" not in rendered
    assert "public value" in rendered


def test_bearer_tokens_redacted_in_text():
    text = "Authorization: Bearer eyJhbGciOiJIUzI1Ni real-payload"
    out = _redact_text(text)
    assert "real-payload" not in out


def test_control_plane_keys_excluded_from_mapping_items():
    node = {
        "name": "x",
        "agent_directives": "hidden-control",
        "capabilitySurface": "hidden",
        "total_count": 3,
    }
    items = list(_mapping_items_excluding_control(node))
    keys = {k for k, _ in items}
    assert "name" in keys
    assert "agent_directives" not in keys
    assert "capabilitySurface" not in keys
    assert "total_count" in keys


# ------------------------------------------------------------------
# malformed/failed evidence never promoted
# ------------------------------------------------------------------


def test_no_content_attempt_is_not_business_evidence():
    attempt = _attempt(_outcome(), content="  ")
    assert _is_business_evidence_attempt(attempt) is False


def test_incomplete_provenance_is_not_business_evidence():
    attempt = _attempt(_outcome(), prov_complete=False)
    assert _is_business_evidence_attempt(attempt) is False


def test_page_items_are_never_promoted_to_total():
    """Owner page of 10 visible items + has_more=true is evidence of
    page content only — never of a 10-item total."""
    structured = _page(page=1, items=[{"id": i} for i in range(10)],
                       has_more=True)
    envelope = extract_pagination_envelope(structured)
    assert envelope.returned_count == 10
    assert resolve_count_semantics(envelope).total is None
