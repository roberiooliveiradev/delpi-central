"""Capability-neutral governed attempt semantics — shared skeleton.

Consumer: specialist_capability_orchestration.py — the live
specialist-owned capability orchestration
(ARCH-DRIFT-MCP-FULL-CAPABILITY-ORCHESTRATION-03, ledger §6.126;
previously specialist-owned READ, §6.118). Only the genuinely common
semantic skeleton lives here:

  governed capability attempt
    -> GovernedCapabilityStatus (SUCCESS | NOT_APPLICABLE
       | SOURCE_UNAVAILABLE | AUTHZ_DENIED | CONFIRMATION_REQUIRED
       | WRITE_REJECTED)
    -> bounded provenance projection (source != specialist)
    -> deterministic bounded rendering carried on the attempt

The earlier static bound-read orchestration (BoundDirectRead /
GovernedRead) and the per-capability C4 bindings are SUPERSEDED —
capability availability is specialist-owned via live tools/list. The
static write-binding registry (GOVERNED_WRITE_BINDINGS /
write_binding_for) is equally SUPERSEDED (§6.126).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Mapping, Protocol

from app.application.interaction.contracts import GovernedCapabilityProvenance
from app.application.specialist_interop.errors import (
    MCP_AUTHENTICATION_FAILED,
    MCP_AUTHORIZATION_DENIED,
    SpecialistInteropError,
)
from app.domain.evidence.model import SourceRef
from app.domain.specialist_interop.model import SpecialistOutcome


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
    content: str | None = None
    limitations: tuple[str, ...] = ()
    confirmation_context: Mapping[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class GovernedCapabilityBinding:
    """DÉLIA-owned invocation context of one governed capability call.

    Correlation identity only: names the specialist/capability invoked
    and the business source the result is grounded in. Naming a
    capability grants nothing — every invocation passes both
    enforcement boundaries and the owner-side authorization.
    """

    binding_id: str
    specialist_id: str
    remote_capability: str
    action_id: str
    source: SourceRef


def _success_attempt(
    *,
    correlation_id: str,
    binding: GovernedCapabilityBinding,
    outcome: SpecialistOutcome,
    render: Callable[[SpecialistOutcome], tuple[str, tuple[str, ...]]],
) -> GovernedCapabilityAttempt:
    """Assemble a SUCCESS attempt: OBSERVATION outcome + provenance.

    The specialist is interoperability plumbing; the SourceRef is the
    authoritative business source. Epistemic class is never elevated —
    grounding marks provenance, not FACT.
    """
    content, limitations = render(outcome)
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
        ),
        content=content,
        limitations=limitations,
    )


def _error_attempt(
    correlation_id: str, exc: SpecialistInteropError
) -> GovernedCapabilityAttempt:
    """Frozen failure semantics: distinct unavailable vs denied."""
    status = (
        GovernedCapabilityStatus.AUTHZ_DENIED
        if exc.code in (MCP_AUTHENTICATION_FAILED, MCP_AUTHORIZATION_DENIED)
        else GovernedCapabilityStatus.SOURCE_UNAVAILABLE
    )
    return GovernedCapabilityAttempt(
        status=status, correlation_id=correlation_id, error_code=exc.code
    )


class SupportsGovernedCapabilityAttempt(Protocol):
    """Structural contract the interaction handler consumes.

    The specialist-owned live orchestration
    (specialist_capability_orchestration.py) is the runtime
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
    ) -> GovernedCapabilityAttempt: ...
