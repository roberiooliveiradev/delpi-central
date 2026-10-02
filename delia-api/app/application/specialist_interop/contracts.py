"""Application contracts for the specialist interoperability boundary.

Context minimization is enforced by shape: requests carry only the
bounded subtask arguments plus a correlation id. There is no field for
conversation history, instructions, credentials, or unrelated context —
none can be delegated.

Remote* types are provider-neutral wire descriptions produced by the
Infrastructure adapter. Their metadata fields are untrusted remote data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from app.domain.specialist_interop.model import (
    SpecialistCapabilityDescriptor,
    SpecialistOutcome,
    SpecialistRef,
)


# DÉLIA-side invocation argument bound (context minimization + size bound).
MAX_INVOCATION_ARGUMENTS_CHARS = 4000
DEFAULT_INVOCATION_TIMEOUT_SECONDS = 15.0
MAX_INVOCATION_TIMEOUT_SECONDS = 30.0


@dataclass(frozen=True, slots=True)
class SpecialistCatalogRequest:
    """Bounded discovery request for one approved specialist."""

    specialist_id: str
    correlation_id: str
    timeout_seconds: float = DEFAULT_INVOCATION_TIMEOUT_SECONDS


@dataclass(frozen=True, slots=True)
class SpecialistInvocationRequest:
    """Bounded subtask delegation to one approved specialist capability.

    ``arguments`` are the only payload forwarded to the specialist — the
    minimum necessary, supplied by the caller. No conversation history,
    instructions, CoT, tokens, or other specialists' results exist here.
    """

    specialist_id: str
    remote_capability: str
    correlation_id: str
    arguments: Mapping[str, object] = field(default_factory=dict)
    timeout_seconds: float = DEFAULT_INVOCATION_TIMEOUT_SECONDS
    # C4-MCP-GOVERNED-READS-01: for READ-class capabilities only, the
    # DAVI-side action id already proven by DÉLIA orchestration against
    # the discovery response. It is a bounded scope marker checked
    # against GOVERNED_READ_ACTIONS — never authority by itself, never
    # accepted from user/model input.
    governed_action_id: str | None = None


@dataclass(frozen=True, slots=True)
class RemoteToolDescriptor:
    """Provider-neutral description of one remote capability on the wire.

    ``title``, ``description``, ``input_schema``, and ``annotations`` are
    untrusted remote metadata — never instructions, policy, or permission.
    ``operation_class`` carries the owner-typed ``delpi/toolClass`` value:
    trusted for semantic classification only — never for permission.
    """

    remote_name: str
    title: str | None = None
    description: str | None = None
    input_schema: Mapping[str, object] | None = None
    annotations: Mapping[str, object] | None = None
    operation_class: str | None = None


@dataclass(frozen=True, slots=True)
class RemoteToolOutcome:
    """Provider-neutral bounded outcome of one remote capability call."""

    content_text: str
    structured: Mapping[str, object] | None = None
    is_error: bool = False
    is_complete: bool = True


@dataclass(frozen=True, slots=True)
class SpecialistCatalogResult:
    """Semantic projection of the specialist-owned catalog.

    ``capabilities`` projects every advertised remote capability with
    its owner-typed operation class (UNKNOWN when absent/invalid) —
    discovery projection, not an invocation grant.
    ``blocked_remote_names`` records the advertised names not invocable
    under current DÉLIA policy (non-bound DISCOVERY, non-enabled READ,
    PREPARE/ACT, UNKNOWN) — transparency without exposure.
    """

    specialist: SpecialistRef
    capabilities: tuple[SpecialistCapabilityDescriptor, ...]
    blocked_remote_names: tuple[str, ...]
    observed_at: str


SpecialistInvocationResult = SpecialistOutcome
