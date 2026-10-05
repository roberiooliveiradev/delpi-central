"""Capability provider port — the provider-neutral adapter boundary.

ARCH-DRIFT-DELIA-PROVIDER-NEUTRAL-ORCHESTRATION-01 (ledger §6.130):
the central orchestrator depends only on this port. Each provider
family (MCP, OpenAPI, media/screen, future A2A/Automation) implements
it in its own adapter, which owns all wire mechanics: transports,
protocols, authentication delegation, schema details.

The surface is always re-read live per turn — providers must never
return cached authority, and the orchestrator must never persist these
views as a local catalog.
"""

from __future__ import annotations

from typing import Mapping, Protocol

from app.application.capability_provision.contracts import (
    ProviderCapability,
    ProviderSurface,
)
from app.domain.specialist_interop.model import SpecialistOutcome


class CapabilityProviderPort(Protocol):
    """One capability provider family.

    Implementations must raise ``CapabilityProviderError`` (never a
    transport-specific exception) for consult/invoke failures so the
    orchestrator can classify unavailable vs denied generically.
    """

    provider_id: str

    def list_groups(
        self,
        *,
        correlation_id: str,
        timeout_seconds: float | None = None,
    ) -> ProviderSurface:
        """Project this provider's live capability groups."""
        ...

    def invoke(
        self,
        capability: ProviderCapability,
        arguments: Mapping[str, object],
        *,
        correlation_id: str,
        timeout_seconds: float | None = None,
    ) -> SpecialistOutcome:
        """Invoke one capability through the provider's own mechanics."""
        ...
