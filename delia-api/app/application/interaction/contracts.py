"""Application contracts for C3-INTERACTION-RUNTIME-01.

Provider SDK objects, Flask objects, and permission snapshots are
forbidden here. The request carries the already-resolved authoritative
PlatformAccessContext plus untrusted user text only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from app.application.model_invocation.contracts import (
    ConversationContextTurn,
)
from app.application.platform_access import PlatformAccessContext
from app.domain.evidence.model import EpistemicClass, SourceRef
from app.domain.interaction.model import GroundingStatus


# C4-MCP-GOVERNED-READS-01/02: canonical limitation codes surfaced when
# a governed read returned a bounded/partial authoritative result.
LIMITATION_RESULT_TRUNCATED = "result_truncated"

# ARCH-DRIFT-MCP-FULL-CAPABILITY-ORCHESTRATION-03: canonical limitation
# surfaced while a write intent awaits a structured confirmation.
LIMITATION_CONFIRMATION_PENDING = "confirmation_pending"


@dataclass(frozen=True, slots=True)
class InteractiveTurnRequest:
    """One bounded interactive turn request.

    access_context is the Core-resolved authority projection — it carries
    identity and effective permissions, and it is never extended from
    request body fields. input_text is untrusted user data. prior_turns
    is bounded, untrusted, non-authoritative transient conversation
    context supplied by the client — never authority, memory, or FACT.
    ``confirmation`` is an untrusted structured confirmation payload —
    it carries decision + non-reversible digests only (never the raw
    owner proposal handle) and binds to backend-held pending write
    state; it authorizes nothing by itself.
    """

    access_context: PlatformAccessContext | None
    input_text: str
    prior_turns: tuple[ConversationContextTurn, ...] = field(
        default_factory=tuple
    )
    confirmation: Mapping[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class GovernedCapabilityProvenance:
    """Bounded user-facing provenance of a grounded governed
    capability result (read or owner-attested write outcome).

    Exposes the business source (never the transport endpoint), the
    interoperability specialist, and correlation metadata only. No
    candidate tokens, credentials, URLs, or wire internals.
    """

    source_refs: tuple[SourceRef, ...]
    specialist_id: str
    remote_capability: str
    action_id: str
    protocol: str
    observed_at: str
    correlation_id: str
    is_complete: bool

    def to_projection(self) -> dict:
        """Bounded HTTP-safe projection — no tokens, URLs, wire internals."""
        first = self.source_refs[0] if self.source_refs else None
        return {
            "source": (
                {
                    "source_id": first.source_id,
                    "source_system": first.source_system,
                    "observed_at": first.observed_at,
                }
                if first is not None
                else None
            ),
            "specialist_id": self.specialist_id,
            "protocol": self.protocol,
            "remote_capability": self.remote_capability,
            "action_id": self.action_id,
            "observed_at": self.observed_at,
            "correlation_id": self.correlation_id,
            "is_complete": self.is_complete,
        }


@dataclass(frozen=True, slots=True)
class InteractiveTurnResult:
    """Bounded application response for one interaction turn.

    Exposes correlation IDs and validated result content only. No raw
    provider payload, credentials, instruction body, or authority
    snapshot is ever part of this contract.

    C4-MCP-GOVERNED-READS-01: ``grounding_status`` distinguishes a
    response backed by a governed authoritative DELPI source read
    (GROUNDED) from a general model answer (NON_GROUNDED). There is no
    ambiguous default — every result carries one. ``provenance`` is the
    bounded evidence projection and is present only when GROUNDED.

    ARCH-DRIFT-MCP-FULL-CAPABILITY-ORCHESTRATION-03:
    ``confirmation_request`` is the bounded confirmation surface emitted
    when a write intent awaits a structured confirmation. It carries
    non-reversible digests only — never the raw owner proposal handle —
    and authorizes nothing by itself.
    """

    session_id: str
    user_turn_id: str
    result_turn_id: str
    content: str
    epistemic_class: EpistemicClass | None
    limitations: tuple[str, ...]
    generated_at: str
    model_invocation_id: str | None
    grounding_status: GroundingStatus = GroundingStatus.NON_GROUNDED
    provenance: GovernedCapabilityProvenance | None = None
    confirmation_request: Mapping[str, Any] | None = None

    def is_fact(self) -> bool:
        return False

    def authorizes_act(self) -> bool:
        return False
