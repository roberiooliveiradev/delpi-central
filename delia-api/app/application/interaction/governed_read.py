"""Capability-neutral governed READ semantics — C4-MCP-GOVERNED-READS-02.

Two concrete consumers justify this module: the DAVI Product Master
read (governed_product_read.py, candidate-token flow) and the TÉO
dashboard read (governed_teo_analyze.py, direct tools/call flow). Only
the genuinely common semantic skeleton lives here:

  bound read attempt
    -> GovernedReadStatus (SUCCESS | NOT_APPLICABLE | SOURCE_UNAVAILABLE
       | AUTHZ_DENIED)
    -> bounded provenance projection (source != specialist)
    -> deterministic bounded rendering carried on the attempt

There is no registry, router, engine, or provider abstraction. Bound
reads are statically constructed at composition; ordering is fixed and
specialist-specific invocation mechanics stay at the binding edge.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Mapping

from app.application.interaction.contracts import GovernedReadProvenance
from app.application.specialist_interop.contracts import (
    SpecialistInvocationRequest,
)
from app.application.specialist_interop.errors import (
    MCP_AUTHENTICATION_FAILED,
    MCP_AUTHORIZATION_DENIED,
    SpecialistInteropError,
)
from app.application.specialist_interop.specialist_interop import (
    SpecialistInterop,
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
    governed_action_id: str
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
            action_id=binding.governed_action_id,
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


class BoundDirectRead:
    """One direct-invocation governed read bound to a static binding.

    For specialists whose approved capability is itself the read
    (no remote discover/candidate_token flow). ``build_arguments``
    decides applicability and produces the bounded wire arguments —
    returning ``None`` means NOT_APPLICABLE and no call is made.
    ``render`` deterministically bounds the authoritative result.
    """

    def __init__(
        self,
        interop: SpecialistInterop,
        binding: GovernedReadBinding,
        *,
        build_arguments: Callable[[str], Mapping[str, Any] | None],
        render: Callable[[SpecialistOutcome], tuple[str, tuple[str, ...]]],
    ) -> None:
        self._interop = interop
        self._binding = binding
        self._build_arguments = build_arguments
        self._render = render

    def attempt(
        self, input_text: str, *, correlation_id: str | None = None
    ) -> GovernedReadAttempt:
        correlation = correlation_id or str(uuid.uuid4())
        arguments = self._build_arguments(input_text)
        if arguments is None:
            return GovernedReadAttempt(
                status=GovernedReadStatus.NOT_APPLICABLE,
                correlation_id=correlation,
            )
        try:
            outcome = self._interop.invoke(
                SpecialistInvocationRequest(
                    specialist_id=self._binding.specialist_id,
                    remote_capability=self._binding.remote_capability,
                    correlation_id=correlation,
                    governed_action_id=self._binding.governed_action_id,
                    arguments=arguments,
                )
            )
        except SpecialistInteropError as exc:
            # For a direct call there is a single consult: an
            # authentication/transport failure means the source was
            # never reached (SOURCE_UNAVAILABLE); only an explicit
            # downstream authorization denial is AUTHZ_DENIED.
            status = (
                GovernedReadStatus.AUTHZ_DENIED
                if exc.code == MCP_AUTHORIZATION_DENIED
                else GovernedReadStatus.SOURCE_UNAVAILABLE
            )
            return GovernedReadAttempt(
                status=status,
                correlation_id=correlation,
                error_code=exc.code,
            )
        return _success_attempt(
            correlation_id=correlation,
            binding=self._binding,
            outcome=outcome,
            render=self._render,
        )


class GovernedRead:
    """Orchestrates the statically-bound governed reads, fail closed.

    Fixed binding order — there is no free-form tool choice and no
    fan-out: a bound read that does not apply to the input must not
    consult its source. SOURCE_UNAVAILABLE survives a later
    NOT_APPLICABLE so a selected-but-unreachable source is always
    disclosed; SUCCESS/AUTHZ_DENIED short-circuit.
    """

    def __init__(self, bound_reads) -> None:
        self._bound_reads = tuple(bound_reads)

    def attempt(
        self, input_text: str, *, correlation_id: str | None = None
    ) -> GovernedReadAttempt:
        correlation = correlation_id or str(uuid.uuid4())
        unavailable: GovernedReadAttempt | None = None
        for bound_read in self._bound_reads:
            attempt = bound_read.attempt(
                input_text, correlation_id=correlation
            )
            if attempt.status in (
                GovernedReadStatus.SUCCESS,
                GovernedReadStatus.AUTHZ_DENIED,
            ):
                return attempt
            if (
                attempt.status is GovernedReadStatus.SOURCE_UNAVAILABLE
                and unavailable is None
            ):
                unavailable = attempt
        if unavailable is not None:
            return unavailable
        return GovernedReadAttempt(
            status=GovernedReadStatus.NOT_APPLICABLE,
            correlation_id=correlation,
        )
