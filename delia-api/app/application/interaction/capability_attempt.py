"""Capability-neutral governed attempt semantics — shared skeleton.

Consumer: capability_provision/orchestration.py — the provider-neutral
operational capability orchestration
(ARCH-DRIFT-DELIA-PROVIDER-NEUTRAL-ORCHESTRATION-01, ledger §6.130;
previously MCP-specialist orchestration, §6.126/§6.118). Only the
genuinely common semantic skeleton lives here:

  governed capability attempt
    -> GovernedCapabilityStatus (SUCCESS | NOT_APPLICABLE
       | SOURCE_UNAVAILABLE | AUTHZ_DENIED | CONFIRMATION_REQUIRED
       | WRITE_REJECTED | CLARIFICATION_REQUIRED
       | PROCESSING_TIMEOUT)
    -> bounded provenance projection (source != capability group)
    -> deterministic bounded rendering carried on the attempt

The earlier static bound-read orchestration (BoundDirectRead /
GovernedRead) and the per-capability C4 bindings are SUPERSEDED —
capability availability is owner-owned via the live provider surface.
The static write-binding registry (GOVERNED_WRITE_BINDINGS /
write_binding_for) is equally SUPERSEDED (§6.126).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Mapping, Protocol

from app.application.capability_provision.contracts import (
    CapabilityProviderError,
)
from app.application.interaction.contracts import GovernedCapabilityProvenance
from app.application.interaction.turn_budget import TurnDeadline
from app.application.interaction.workspace_context import WorkspaceContext
from app.application.specialist_interop.errors import (
    MCP_AUTHENTICATION_FAILED,
    MCP_AUTHORIZATION_DENIED,
)
from app.domain.evidence.model import SourceRef
from app.domain.specialist_interop.model import SpecialistOutcome


# Set only when typed admission returns before owner listing.
# Absence of this marker is not conversational admission.
EARLY_CONVERSATIONAL_ADMISSION = "early_conversational_admission"

# DELIA-C3-SELF-AWARENESS (S1): typed admission classified the turn as
# a question about the governed capability surface itself. The attempt
# carries a deterministic projection of the LIVE provider surface in
# ``content`` — observed this turn, never model-authored, never an
# invocation. Listing a surface never grants authorization.
SURFACE_INQUIRY_ADMISSION = "surface_inquiry_admission"

# DELIA-C3-S5-REWORK (D8): admission declared an owner-surface need
# but the governed path ended NOT_APPLICABLE (no capability bound,
# intent/foreign inputs unresolvable, or a bound query that returned
# nothing). The attempt stays NOT_APPLICABLE; this marker lets the
# interaction layer answer with deterministic insufficiency instead
# of free-form model prose that could narrate internals it cannot
# verify. Group-level applicable=false stays unmarked — that remains
# the conversational-recovery path.
OWNER_PATH_UNBOUND = "owner_path_unbound"


class GovernedCapabilityStatus(str, Enum):
    """Truthful outcome classification for one governed capability
    attempt."""

    SUCCESS = "SUCCESS"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    AUTHZ_DENIED = "AUTHZ_DENIED"
    # Write-class lifecycle states (§6.126): a READY proposal awaiting a
    # structured confirmation, and a write refused by a governance gate
    # or by the owner/domain authority (truthful denial, no bypass).
    CONFIRMATION_REQUIRED = "CONFIRMATION_REQUIRED"
    WRITE_REJECTED = "WRITE_REJECTED"
    # Applicable request whose owner-required input cannot be satisfied
    # from the turn (§6.131): the capability path exists but the bounded
    # argument projection cannot fill mandatory owner inputs. Truthful
    # ask-back instead of a generic refusal or an invented value.
    CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"
    # Doc 88 CP2: a model-stage deadline or the shared turn budget was
    # exhausted — an internal processing failure that never reached or
    # finished the owner path. Distinct from SOURCE_UNAVAILABLE: the
    # authoritative source must not be blamed when it was never
    # consulted; ``error_code`` preserves the observed cause
    # (model_timeout | turn_budget_exhausted).
    PROCESSING_TIMEOUT = "PROCESSING_TIMEOUT"


@dataclass(frozen=True, slots=True)
class GovernedCapabilityAttempt:
    """Bounded result of attempting a governed capability invocation.

    On SUCCESS ``content``/``limitations`` carry the deterministic
    bounded rendering of the authoritative result produced at the
    boundary — the interaction handler stays specialist-neutral. On
    CONFIRMATION_REQUIRED, ``confirmation_context`` carries the bounded
    confirmation surface (digests only — never the raw proposal
    handle) and ``content`` carries the preview rendering.
    """

    status: GovernedCapabilityStatus
    correlation_id: str
    outcome: SpecialistOutcome | None = None
    provenance: GovernedCapabilityProvenance | None = None
    error_code: str | None = None
    owner_hint: str | None = None
    content: str | None = None
    limitations: tuple[str, ...] = ()
    # presentation.v2 (G3): deterministic ``markdown_safe`` projection
    # of the SAME admitted structured payload — set only when governed
    # structured data legitimately drove the projection. Never present
    # on owner free text, model prose, empty results or failures.
    markdown_content: str | None = None
    confirmation_context: Mapping[str, Any] | None = None
    # Typed admission outcome. Only early conversational admission
    # sets this. Later NOT_APPLICABLE leaves it empty.
    admission_outcome: str | None = None
    # Prompt 5 observability projection inputs — presentation-only
    # signals, never authority:
    #   composition_mode: effective answer composition observed at
    #     the canonical result seam ("cri" when the CRI composer
    #     produced the content, absent → deterministic/baseline);
    #   governed_attempts: total governed attempts the turn needed
    #     (1 unless bounded resume re-entered).
    composition_mode: str | None = None
    governed_attempts: int | None = None


@dataclass(frozen=True, slots=True)
class GovernedCapabilityBinding:
    """DÉLIA-owned invocation context of one governed capability call.

    Correlation identity only: names the capability group/capability
    invoked and the business source the result is grounded in. Naming
    a capability grants nothing — every invocation passes both
    enforcement boundaries and the owner-side authorization.
    """

    binding_id: str
    group_key: str
    remote_capability: str
    action_id: str
    source: SourceRef
    provider_id: str | None = None
    capability_group_id: str | None = None


class _SupportsRenderedOutcome(Protocol):
    """Structural contract of the governed render result — the
    capability_provision ``RenderedSpecialistOutcome`` satisfies it
    without this shared module importing the orchestration layer."""

    content: str
    limitations: tuple[str, ...]
    markdown: str | None


def _success_attempt(
    *,
    correlation_id: str,
    binding: GovernedCapabilityBinding,
    outcome: SpecialistOutcome,
    render: Callable[[SpecialistOutcome], _SupportsRenderedOutcome],
) -> GovernedCapabilityAttempt:
    """Assemble a SUCCESS attempt: OBSERVATION outcome + provenance.

    The specialist is interoperability plumbing; the SourceRef is the
    authoritative business source. Epistemic class is never elevated —
    grounding marks provenance, not FACT.
    """
    rendered = render(outcome)
    return GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SUCCESS,
        correlation_id=correlation_id,
        outcome=outcome,
        provenance=GovernedCapabilityProvenance(
            source_refs=(
                SourceRef(
                    source_id=binding.source.source_id,
                    source_system=binding.source.source_system,
                    provider_name=binding.source.provider_name,
                    observed_at=outcome.provenance.observed_at,
                ),
            ),
            specialist_id=outcome.provenance.specialist_id,
            remote_capability=outcome.provenance.remote_name,
            action_id=binding.action_id,
            protocol=outcome.provenance.protocol.value,
            observed_at=outcome.provenance.observed_at,
            correlation_id=outcome.provenance.correlation_id,
            is_complete=outcome.is_complete,
            provider_id=binding.provider_id,
            capability_group_id=binding.capability_group_id,
        ),
        content=rendered.content,
        limitations=rendered.limitations,
        markdown_content=rendered.markdown,
    )


def _error_attempt(
    correlation_id: str, exc: CapabilityProviderError
) -> GovernedCapabilityAttempt:
    """Frozen failure semantics: distinct unavailable vs denied."""
    status = (
        GovernedCapabilityStatus.AUTHZ_DENIED
        if exc.code in (MCP_AUTHENTICATION_FAILED, MCP_AUTHORIZATION_DENIED)
        else GovernedCapabilityStatus.SOURCE_UNAVAILABLE
    )
    return GovernedCapabilityAttempt(
        status=status,
        correlation_id=correlation_id,
        error_code=exc.code,
        owner_hint=getattr(exc, "owner_hint", None),
    )


class SupportsGovernedCapabilityAttempt(Protocol):
    """Structural contract the interaction handler consumes.

    The provider-neutral operational orchestration
    (capability_provision/orchestration.py) is the runtime
    implementation; any governed-attempt producer must return a
    GovernedCapabilityAttempt.
    """

    def attempt(
        self,
        input_text: str,
        *,
        correlation_id: str | None = None,
        actor_user_id: str | None = None,
        session_id: str | None = None,
        confirmation: Mapping[str, Any] | None = None,
        workspace_context: WorkspaceContext | None = None,
        max_execution_stage: str | None = None,
        turn_deadline: TurnDeadline | None = None,
        prior_turns: tuple = (),
        activity_sink: Any | None = None,
    ) -> GovernedCapabilityAttempt: ...
