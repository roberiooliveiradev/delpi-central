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
from collections.abc import Callable
from concurrent.futures import (
    ThreadPoolExecutor,
    wait as _futures_wait,
)
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
    SpecialistToolsetConfig,
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
class McpCapabilityProvider:
    """Provider adapter over the approved MCP specialists."""

    provider_id = "mcp"

    # Structural bound for the EXPERIMENTAL parallel discovery mode
    # (DELIA-C3-T2-PARALLEL-MCP-DISCOVERY-GUARDED-EXPERIMENT-01):
    # workers are capped regardless of how many specialists onboard —
    # the fan-out can never widen with owner growth.
    _PARALLEL_MAX_WORKERS = 4

    def __init__(
        self,
        interop: SpecialistInterop,
        specialist_ids: Sequence[str],
        *,
        parallel_discovery: bool = False,
        subject_bearer_getter: Callable[[], str | None] | None = None,
        bind_bearer: Callable[[str], object] | None = None,
        unbind_bearer: Callable[[object], None] | None = None,
    ) -> None:
        self._interop = interop
        # R1-RW04: admit any Core/settings-enabled specialist id passed
        # by composition — filtering by the static seven would discard
        # governed onboarding.
        self._specialist_ids = tuple(
            str(sid).strip().lower()
            for sid in specialist_ids
            if str(sid or "").strip()
        )
        # Flag-gated EXPERIMENT ONLY — sequential remains the canonical
        # default; production composition must never pass True.
        self._parallel_discovery = bool(parallel_discovery)
        # Identity seam injected by composition (application never
        # imports infrastructure): the request-scoped bearer accessor
        # plus the existing bind/unbind worker seam — the same one the
        # NDJSON transport uses. Workers never infer identity.
        self._subject_bearer_getter = subject_bearer_getter
        self._bind_bearer = bind_bearer
        self._unbind_bearer = unbind_bearer

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
        if self._parallel_discovery and len(self._specialist_ids) > 1:
            return self._list_groups_parallel(
                correlation_id=correlation_id,
                timeout_seconds=timeout_seconds,
                started=started,
            )
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
            groups.append(
                self._group_from_catalog(specialist_id, catalog)
            )
        return ProviderSurface(groups=tuple(groups), failures=tuple(failures))

    def _group_from_catalog(
        self,
        specialist_id: str,
        catalog,
    ) -> CapabilityGroup:
        specialist = catalog.specialist
        return CapabilityGroup(
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

    def _list_groups_parallel(
        self,
        *,
        correlation_id: str,
        timeout_seconds: float | None,
        started: float,
    ) -> ProviderSurface:
        """EXPERIMENTAL flag-gated bounded per-specialist fan-out.

        DELIA-C3-T2-PARALLEL-MCP-DISCOVERY-GUARDED-EXPERIMENT-01 —
        coordination-authorized isolated experiment only. The sync
        ``requests`` path means workers are threads (never asyncio);
        every governed invariant is preserved verbatim:

        * identity — the subject bearer is captured on the CALLER
          thread once and bound inside each worker via the existing
          seam, unbound in ``finally``; a worker never infers or
          fabricates identity and no credential crosses contexts;
        * deadline — the SAME absolute bound (``started`` +
          ``timeout_seconds``) is passed to every task; each worker's
          governed transport dies at that deadline in its own thread —
          never a per-specialist fresh window, never an orphaned
          unbounded worker;
        * late results — futures not done at the join deadline are
          cancelled-when-queued and their results DISCARDED, reported
          as truthful ``mcp_timeout`` failures, never adopted;
        * ordering — groups and failures merge in specialist
          submission order, never completion order;
        * failure — one specialist's exception is its own failure
          marker, never a capability-absence claim;
        * bounds — ``min(n_specialists, _PARALLEL_MAX_WORKERS)``
          threads, created and released inside this call.
        """
        bearer = (
            self._subject_bearer_getter()
            if self._subject_bearer_getter is not None
            else None
        )

        def _discover(specialist_id: str):
            binding = (
                self._bind_bearer(bearer)
                if bearer and self._bind_bearer is not None
                else None
            )
            try:
                remaining = remaining_budget(started, timeout_seconds)
                if remaining is not None and remaining <= 0:
                    raise SpecialistInteropError(
                        MCP_TIMEOUT,
                        "specialist discovery budget exhausted",
                    )
                return self._interop.discover_catalog(
                    SpecialistCatalogRequest(
                        specialist_id=specialist_id,
                        correlation_id=correlation_id,
                        timeout_seconds=self._effective_timeout(remaining),
                    )
                )
            finally:
                # Bearer never outlives the worker task — restored in
                # finally even on exception (NDJSON-worker precedent).
                if binding is not None and self._unbind_bearer is not None:
                    self._unbind_bearer(binding)

        groups: list[CapabilityGroup] = []
        failures: list[str] = []
        join_budget = remaining_budget(started, timeout_seconds)
        executor = ThreadPoolExecutor(
            max_workers=min(
                len(self._specialist_ids), self._PARALLEL_MAX_WORKERS
            ),
            thread_name_prefix="delia-mcp-disc",
        )
        try:
            futures = [
                executor.submit(_discover, sid)
                for sid in self._specialist_ids
            ]
            done, _pending = _futures_wait(
                futures,
                timeout=(
                    join_budget
                    if join_budget is not None
                    else None
                ),
            )
            for future, specialist_id in zip(
                futures, self._specialist_ids
            ):
                if future not in done:
                    # Queued-not-started is cancelled; an in-flight
                    # worker finishes bounded by its own deadline —
                    # its late result is discarded, never adopted.
                    future.cancel()
                    failures.append(MCP_TIMEOUT)
                    continue
                try:
                    catalog = future.result()
                except SpecialistInteropError as exc:
                    failures.append(exc.code)
                    continue
                groups.append(
                    self._group_from_catalog(specialist_id, catalog)
                )
        finally:
            # Queued jobs cancelled; running workers are bounded by
            # their own transport deadline — never waited on here.
            executor.shutdown(wait=False, cancel_futures=True)
        return ProviderSurface(
            groups=tuple(groups), failures=tuple(failures)
        )

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

    def native_toolset_config(
        self,
        group_id: str,
        *,
        timeout_seconds: float | None = None,
    ) -> SpecialistToolsetConfig:
        """Native-discovery config for one specialist group.

        Delegates to the interop boundary — the adapter remains the
        sole owner of profiles and delegated credentials.
        """
        return self._interop.native_toolset_config(
            group_id,
            timeout_seconds=timeout_seconds,
        )

    @staticmethod
    def _effective_timeout(timeout_seconds: float | None) -> float:
        """Reduction-only clamp: caller bounds shorten — never
        lengthen — the configured stage max."""
        if timeout_seconds is None:
            return DEFAULT_INVOCATION_TIMEOUT_SECONDS
        return min(
            float(timeout_seconds), DEFAULT_INVOCATION_TIMEOUT_SECONDS
        )
