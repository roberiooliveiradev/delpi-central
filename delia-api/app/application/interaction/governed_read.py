"""Capability-neutral governed READ semantics — shared skeleton.

Consumer: specialist_owned_read.py — the live specialist-owned
capability read (ARCH-DRIFT-MCP-CAPABILITY-AUTHORITY-02, ledger §6.118).
Only the genuinely common semantic skeleton lives here:

  governed read attempt
    -> GovernedReadStatus (SUCCESS | NOT_APPLICABLE | SOURCE_UNAVAILABLE
       | AUTHZ_DENIED)
    -> bounded provenance projection (source != specialist)
    -> deterministic bounded rendering carried on the attempt

The earlier static bound-read orchestration (BoundDirectRead /
GovernedRead) and the per-capability C4 bindings are SUPERSEDED —
capability availability is specialist-owned via live tools/list.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Protocol

from app.application.interaction.contracts import GovernedReadProvenance
from app.application.specialist_interop.errors import (
    MCP_AUTHENTICATION_FAILED,
    MCP_AUTHORIZATION_DENIED,
    SpecialistInteropError,
)
from app.domain.evidence.model import SourceRef
from app.domain.specialist_interop.model import SpecialistOutcome


class GovernedReadStatus(str, Enum):
    """Truthful outcome classification for one governed read attempt."""

    SUCCESS = "SUCCESS"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    AUTHZ_DENIED = "AUTHZ_DENIED"


@dataclass(frozen=True, slots=True)
class GovernedReadAttempt:
    """Bounded result of attempting an authorized governed read.

    On SUCCESS ``content``/``limitations`` carry the deterministic
    bounded rendering of the authoritative result produced at the
    binding edge — the interaction handler stays specialist-neutral.
    """

    status: GovernedReadStatus
    correlation_id: str
    outcome: SpecialistOutcome | None = None
    provenance: GovernedReadProvenance | None = None
    error_code: str | None = None
    content: str | None = None
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class GovernedReadBinding:
    """DÉLIA-owned static identity of one authorized governed READ.

    The binding names the approved specialist/capability pair and the
    business source the result is grounded in. Naming a binding grants
    nothing — every invocation still passes both enforcement
    boundaries and the owner-side authorization.
    """

    binding_id: str
    specialist_id: str
    remote_capability: str
    action_id: str
    source: SourceRef


def _success_attempt(
    *,
    correlation_id: str,
    binding: GovernedReadBinding,
    outcome: SpecialistOutcome,
    render: Callable[[SpecialistOutcome], tuple[str, tuple[str, ...]]],
) -> GovernedReadAttempt:
    """Assemble a SUCCESS attempt: OBSERVATION outcome + provenance.

    The specialist is interoperability plumbing; the SourceRef is the
    authoritative business source. Epistemic class is never elevated —
    grounding marks provenance, not FACT.
    """
    content, limitations = render(outcome)
    return GovernedReadAttempt(
        status=GovernedReadStatus.SUCCESS,
        correlation_id=correlation_id,
        outcome=outcome,
        provenance=GovernedReadProvenance(
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
) -> GovernedReadAttempt:
    """Frozen failure semantics: distinct unavailable vs denied."""
    status = (
        GovernedReadStatus.AUTHZ_DENIED
        if exc.code in (MCP_AUTHENTICATION_FAILED, MCP_AUTHORIZATION_DENIED)
        else GovernedReadStatus.SOURCE_UNAVAILABLE
    )
    return GovernedReadAttempt(
        status=status, correlation_id=correlation_id, error_code=exc.code
    )


class SupportsGovernedReadAttempt(Protocol):
    """Structural contract the interaction handler consumes.

    The specialist-owned live read (specialist_owned_read.py) is the
    runtime implementation; any governed-read attempt producer must
    return a GovernedReadAttempt.
    """

    def attempt(
        self, input_text: str, *, correlation_id: str | None = None
    ) -> GovernedReadAttempt: ...
