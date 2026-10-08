"""MCP capability provider adapter.

ARCH-DRIFT-DELIA-PROVIDER-NEUTRAL-ORCHESTRATION-01 (ledger §6.130):
MCP is ONE provider family. This adapter wraps the existing
SpecialistInterop boundary and projects each approved specialist's
live authenticated ``tools/list`` into provider-neutral capability
groups. All MCP mechanics (specialist resolution, owner-typed class
projection, live revalidation, delegated credentials) stay inside
SpecialistInterop — unchanged.

Invariants preserved:
- SPECIALIST_CAPABILITY_CATALOG_OWNER = SPECIALIST
- DELIA_LOCAL_MCP_CAPABILITY_CATALOG = FORBIDDEN (surfaces are live,
  request-scoped projections only)
- UNKNOWN-class capabilities stay discoverable but never invocable
- writes keep the governed PREPARE/ACT chain upstream
"""

from __future__ import annotations

import time
from typing import Mapping, Sequence

from app.application.capability_provision.contracts import (
    CapabilityGroup,
    CapabilityProviderError,
    ProviderCapability,
    ProviderSurface,
)
from app.application.interaction.turn_budget import remaining_budget
from app.application.specialist_interop.contracts import (
    DEFAULT_INVOCATION_TIMEOUT_SECONDS,
    SpecialistCatalogRequest,
    SpecialistInvocationRequest,
)
from app.application.specialist_interop.errors import (
    MCP_TIMEOUT,
    SpecialistInteropError,
)
from app.application.specialist_interop.specialist_interop import (
    SpecialistInterop,
)
from app.domain.evidence.model import SourceRef
from app.domain.specialist_interop.model import SpecialistOutcome
from app.domain.specialist_interop.rules import APPROVED_SPECIALIST_IDS


class McpCapabilityProvider:
    """Provider adapter over the approved MCP specialists."""

    provider_id = "mcp"

    def __init__(
        self,
        interop: SpecialistInterop,
        specialist_ids: Sequence[str],
    ) -> None:
        self._interop = interop
        self._specialist_ids = tuple(
            sid for sid in specialist_ids if sid in APPROVED_SPECIALIST_IDS
        )

    def list_groups(
        self,
        *,
        correlation_id: str,
        timeout_seconds: float | None = None,
    ) -> ProviderSurface:
        groups: list[CapabilityGroup] = []
        failures: list[str] = []
        # LOOP-03R2A-R1: ``timeout_seconds`` bounds the WHOLE fan-out —
        # each specialist consult receives only the remaining budget,
        # reduction-clamped to the configured stage max, so the
        # listing can never outlive the caller's bound.
        started = time.monotonic()
        for specialist_id in self._specialist_ids:
            remaining = remaining_budget(started, timeout_seconds)
            if remaining is not None and remaining <= 0:
                failures.append(MCP_TIMEOUT)
                break
            try:
                catalog = self._interop.discover_catalog(
                    SpecialistCatalogRequest(
                        specialist_id=specialist_id,
                        correlation_id=correlation_id,
                        timeout_seconds=self._effective_timeout(
                            remaining
                        ),
                    )
                )
            except SpecialistInteropError as exc:
                failures.append(exc.code)
                continue
            specialist = catalog.specialist
            groups.append(
                CapabilityGroup(
                    provider_id=self.provider_id,
                    group_id=specialist_id,
                    owner_ref=specialist.owner_ref,
                    display_name=specialist.display_name,
                    capabilities=tuple(
                        ProviderCapability(
                            capability_id=cap.capability_id,
                            group_id=specialist_id,
                            provider_id=self.provider_id,
                            remote_name=cap.remote_name,
                            owner=specialist.owner_ref,
                            operation_class=cap.operation_class,
                            description=cap.description,
                            input_schema=cap.input_schema,
                            binding={
                                "specialist_id": specialist_id,
                                "remote_name": cap.remote_name,
                            },
                        )
                        for cap in catalog.capabilities
                    ),
                    source=SourceRef(
                        source_id=specialist.owner_ref,
                        source_system=specialist.owner_ref,
                        provider_name=specialist.display_name,
                    ),
                )
            )
        return ProviderSurface(groups=tuple(groups), failures=tuple(failures))

    def invoke(
        self,
        capability: ProviderCapability,
        arguments: Mapping[str, object],
        *,
        correlation_id: str,
        timeout_seconds: float | None = None,
    ) -> SpecialistOutcome:
        binding = capability.binding
        try:
            return self._interop.invoke(
                SpecialistInvocationRequest(
                    specialist_id=str(binding["specialist_id"]),
                    remote_capability=str(binding["remote_name"]),
                    correlation_id=correlation_id,
                    arguments=dict(arguments),
                    timeout_seconds=self._effective_timeout(
                        timeout_seconds
                    ),
                )
            )
        except SpecialistInteropError as exc:
            raise CapabilityProviderError(
                exc.code,
                str(exc),
                owner_hint=getattr(exc, "owner_hint", None),
            ) from exc

    @staticmethod
    def _effective_timeout(timeout_seconds: float | None) -> float:
        """Reduction-only clamp: caller bounds shorten — never
        lengthen — the configured stage max."""
        if timeout_seconds is None:
            return DEFAULT_INVOCATION_TIMEOUT_SECONDS
        return min(
            float(timeout_seconds), DEFAULT_INVOCATION_TIMEOUT_SECONDS
        )
