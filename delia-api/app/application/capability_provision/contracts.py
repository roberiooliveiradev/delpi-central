"""Provider-neutral capability surface contracts.

ARCH-DRIFT-DELIA-PROVIDER-NEUTRAL-ORCHESTRATION-01 (ledger §6.130):
DÉLIA is the OPERATIONAL_CAPABILITY_ORCHESTRATOR. Capability providers
(MCP, OpenAPI, media/screen, future A2A/Automation) project their live
surfaces into these provider-neutral runtime views; the central
orchestrator consumes only these contracts.

Authority rules (binding):
- A ``ProviderCapability`` is a runtime projection — it never grants
  authorization, source access, or execution.
- ``binding`` is opaque provider-owned invocation identity (e.g. an MCP
  specialist id + remote tool name, or an OpenAPI operation binding).
  The orchestrator must never inspect it; only the owning provider
  adapter interprets it at invoke time.
- ``provider_id`` is provenance metadata — never a routing table entry.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from app.domain.evidence.model import SourceRef
from app.domain.specialist_interop.model import (
    SpecialistOperationClass,
    SpecialistOutcome,
)

# The owner-typed operation-class vocabulary is the canonical semantic
# classification; provider-neutral code aliases it so new modules read
# in capability terms.
CapabilityOperationClass = SpecialistOperationClass

# Provider-neutral alias: an invocation outcome is a bounded, untrusted
# OBSERVATION-class result regardless of the producing provider.
ProviderOutcome = SpecialistOutcome


class CapabilityProviderError(Exception):
    """Bounded provider failure surfaced to the orchestrator.

    ``code`` is a stable machine-readable classification; provider
    adapters translate their transport errors into these codes so the
    orchestrator never sees protocol internals.
    """

    def __init__(
        self,
        code: str,
        message: str = "",
        owner_hint: str | None = None,
    ) -> None:
        super().__init__(message or code)
        self.code = code
        self.message = message or code
        self.owner_hint = owner_hint


@dataclass(frozen=True, slots=True)
class ProviderCapability:
    """One semantic capability on a live provider surface.

    ``remote_name`` is the owner-declared capability name in the
    provider's own vocabulary. ``binding`` carries the provider-owned
    invocation identity and is opaque to the orchestrator.
    """

    capability_id: str
    group_id: str
    provider_id: str
    remote_name: str
    owner: str
    operation_class: SpecialistOperationClass
    description: str | None = None
    input_schema: Mapping[str, Any] | None = None
    binding: Mapping[str, Any] = field(default_factory=dict)

    def grants_authorization(self) -> bool:
        return False

    def grants_source_access(self) -> bool:
        return False

    def grants_execution(self) -> bool:
        return False

    def authorizes_act(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class CapabilityGroup:
    """One provider-owned capability surface (e.g. one MCP specialist,
    one OpenAPI source, one media/screen provider)."""

    provider_id: str
    group_id: str
    owner_ref: str
    display_name: str
    capabilities: tuple[ProviderCapability, ...]
    source: SourceRef | None = None


@dataclass(frozen=True, slots=True)
class ProviderSurface:
    """Live groups projected by one provider plus failure codes for
    groups that could not be consulted (truthful unavailability)."""

    groups: tuple[CapabilityGroup, ...] = ()
    failures: tuple[str, ...] = ()
