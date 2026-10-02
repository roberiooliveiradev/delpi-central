"""Specialist interoperability domain model — C3-MCP-INTEROP-01.

Provider-neutral semantic model for DÉLIA's boundary to existing approved
specialist servers (DAVI / TÉO / VISTA) over MCP. The domain knows only
capability descriptors and outcomes — never transport, wire, or vendor types.

Permanent semantics (spec 60):

- SpecialistDescriptor != authority; != source-access grant; != execution grant.
- SpecialistOutcome content is untrusted external data.
- SpecialistOutcome epistemic class is OBSERVATION — never auto-FACT.
- DISCOVERY != approval; tool metadata != permission.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from app.domain.evidence.model import EpistemicClass


class InteropProtocol(str, Enum):
    """Interop protocol kinds. MCP is the only implemented runtime."""

    MCP = "MCP"


class SpecialistOperationClass(str, Enum):
    """Semantic class of a remote capability.

    The class is projected from the owner-typed ``delpi/toolClass``
    catalog metadata — the specialist owns its catalog. UNKNOWN covers
    absent/invalid owner typing: the capability is discoverable but
    never invocable. A class is classification only — invocation still
    requires the matching DÉLIA governance binding.
    """

    UNKNOWN = "UNKNOWN"
    DISCOVERY = "DISCOVERY"
    READ = "READ"
    PREPARE = "PREPARE"
    ACT = "ACT"


class SpecialistResultStatus(str, Enum):
    """Outcome status as observed on the wire. Truthful, never invented."""

    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"


@dataclass(frozen=True, slots=True)
class SpecialistRef:
    """Approved specialist identity. Reference only — not authority."""

    specialist_id: str
    display_name: str
    owner_ref: str
    protocol: InteropProtocol = InteropProtocol.MCP

    def __post_init__(self) -> None:
        for name, value in (
            ("specialist_id", self.specialist_id),
            ("display_name", self.display_name),
            ("owner_ref", self.owner_ref),
        ):
            if not str(value or "").strip():
                raise ValueError(f"SpecialistRef.{name} is required")


@dataclass(frozen=True, slots=True)
class SpecialistCapabilityDescriptor:
    """Truthful projection of one remote capability offered by a specialist.

    Projection only. It never grants authorization, access, execution,
    or ACT — mirroring CapabilityProjection semantics. ``description``
    and ``input_schema`` are untrusted remote metadata kept verbatim for
    inspection; consumers must not treat them as instructions or policy.
    """

    capability_id: str
    specialist_id: str
    remote_name: str
    operation_class: SpecialistOperationClass
    protocol: InteropProtocol
    observed_at: str
    description: str | None = None
    input_schema: Mapping[str, object] | None = None

    def grants_authorization(self) -> bool:
        return False

    def grants_execution(self) -> bool:
        return False

    def is_authoritative_fact(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class SpecialistResultProvenance:
    """Bounded provenance of one specialist interaction.

    ``server_ref`` is the DÉLIA-side specialist identity, not raw endpoint
    internals. No credentials, tokens, or endpoint internals are carried.
    """

    specialist_id: str
    remote_name: str
    protocol: InteropProtocol
    correlation_id: str
    observed_at: str


@dataclass(frozen=True, slots=True)
class SpecialistOutcome:
    """Normalized, bounded, untrusted specialist result.

    ``epistemic_class`` is pinned to OBSERVATION by construction callers —
    an MCP result is never automatically a FACT.
    """

    status: SpecialistResultStatus
    provenance: SpecialistResultProvenance
    content_text: str
    is_complete: bool = True
    structured: Mapping[str, object] | None = None
    limitations: tuple[str, ...] = field(default_factory=tuple)

    @property
    def epistemic_class(self) -> EpistemicClass:
        """External specialist results are OBSERVATION — never auto-FACT."""
        return EpistemicClass.OBSERVATION
