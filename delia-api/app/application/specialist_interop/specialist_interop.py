"""SpecialistInterop — C3-MCP-INTEROP-01 use case.

Bounded discovery + bounded subtask delegation to approved specialists
through the provider-neutral SpecialistInteropPort. Two independent
fail-closed boundaries:

1. here: the owner-typed ``delpi/toolClass`` classifies every
   advertised remote capability — every owner-typed known class is
   governed-invocable (DISCOVERY/READ/ANALYSIS/PREPARE/ACT);
   UNKNOWN-class and unadvertised names fail closed;
2. the adapter re-checks owner class + DÉLIA policy against a fresh
   tools/list before any wire invocation.

ARCH-DRIFT-MCP-FULL-CAPABILITY-ORCHESTRATION-03 (ledger §6.126): the
READ-only class gate is superseded — DÉLIA is the orchestrator of the
full advertised owner surface. Class eligibility is orchestration
eligibility, never permission: write-class invocations still pass the
generic governed-write chain (confirmation, idempotency, live AuthZ,
owner/domain authority, postcondition) orchestrated upstream, and live
Core/Domain AuthZ is enforced by the owner at ACT time.

Discovery != approval != permission. The remote specialist owns its
catalog; DÉLIA keeps no tool-name mirror. A catalog result never grants
anything; a specialist outcome is untrusted OBSERVATION data.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Mapping

from app.application.interaction.turn_budget import remaining_budget
from app.application.ports.specialist_interop_port import SpecialistInteropPort
from app.application.specialist_interop.contracts import (
    MAX_INVOCATION_ARGUMENTS_CHARS,
    MAX_INVOCATION_TIMEOUT_SECONDS,
    RemoteToolOutcome,
    SpecialistCatalogRequest,
    SpecialistCatalogResult,
    SpecialistInvocationRequest,
)
from app.application.specialist_interop.errors import (
    CAPABILITY_NOT_ALLOWED_IN_PHASE,
    MCP_INVALID_RESPONSE,
    MCP_PROTOCOL_ERROR,
    MCP_TIMEOUT,
    UNKNOWN_CAPABILITY,
    UNKNOWN_SPECIALIST,
    SpecialistInteropError,
)
from app.domain.specialist_interop.model import (
    SpecialistCapabilityDescriptor,
    SpecialistOperationClass,
    SpecialistOutcome,
    SpecialistRef,
    SpecialistResultProvenance,
    SpecialistResultStatus,
    InteropProtocol,
)
from app.domain.specialist_interop.rules import (
    invocable_in_interactive_phase,
    operation_class_from_owner,
    specialist_ref_or_none,
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


class SpecialistInterop:
    """One provider-neutral boundary for approved specialist interaction."""

    def __init__(self, port: SpecialistInteropPort) -> None:
        self._port = port

    def discover_catalog(
        self, request: SpecialistCatalogRequest
    ) -> SpecialistCatalogResult:
        """Project an approved specialist's advertised surface, fail closed.

        The remote specialist owns the catalog: classification comes
        from the owner-typed ``delpi/toolClass``, never from DÉLIA-local
        name tables or untrusted annotations/descriptions. Discovery
        grants nothing — invocation still requires the matching DÉLIA
        policy binding.
        """
        specialist = self._require_specialist(request.specialist_id)
        observed_at = _now_utc()
        remote_tools = self._port.list_remote_tools(
            specialist,
            timeout_seconds=self._clamp_timeout(request.timeout_seconds),
        )
        capabilities: list[SpecialistCapabilityDescriptor] = []
        blocked: list[str] = []
        for tool in remote_tools:
            operation_class = operation_class_from_owner(
                tool.operation_class
            )
            capabilities.append(
                SpecialistCapabilityDescriptor(
                    capability_id=f"{specialist.specialist_id}.{tool.remote_name}",
                    specialist_id=specialist.specialist_id,
                    remote_name=tool.remote_name,
                    operation_class=operation_class,
                    protocol=specialist.protocol,
                    observed_at=observed_at,
                    description=tool.description,
                    input_schema=tool.input_schema,
                )
            )
            if not self._policy_invocable(
                specialist.specialist_id, tool.remote_name, operation_class
            ):
                blocked.append(tool.remote_name)
        return SpecialistCatalogResult(
            specialist=specialist,
            capabilities=tuple(capabilities),
            blocked_remote_names=tuple(sorted(blocked)),
            observed_at=observed_at,
        )

    def invoke(self, request: SpecialistInvocationRequest) -> SpecialistOutcome:
        """Delegate one bounded subtask through the governance gate.

        The owner class is re-read from a fresh ``tools/list`` — a
        reclassified or removed remote capability is honored
        immediately, never from a stale local mirror.
        """
        specialist = self._require_specialist(request.specialist_id)
        remote_name = str(request.remote_capability or "").strip()
        # LOOP-03R2A-R1: ``request.timeout_seconds`` bounds the WHOLE
        # invocation (revalidation list + call) — the second leg
        # receives only what the first leg left.
        invoke_started = time.monotonic()
        remote_tools = self._port.list_remote_tools(
            specialist,
            timeout_seconds=self._clamp_timeout(request.timeout_seconds),
        )
        tool = next(
            (t for t in remote_tools if t.remote_name == remote_name),
            None,
        )
        if tool is None:
            raise SpecialistInteropError(
                UNKNOWN_CAPABILITY,
                "remote capability is not advertised by the specialist",
            )
        operation_class = operation_class_from_owner(tool.operation_class)
        if not invocable_in_interactive_phase(operation_class):
            raise SpecialistInteropError(
                CAPABILITY_NOT_ALLOWED_IN_PHASE,
                "capability is not allowed in this phase",
            )
        arguments = self._validate_arguments(request.arguments)
        remaining = remaining_budget(
            invoke_started, request.timeout_seconds
        )
        if remaining is not None and remaining <= 0:
            raise SpecialistInteropError(
                MCP_TIMEOUT,
                "specialist invocation budget exhausted",
            )
        outcome = self._port.call_remote_tool(
            specialist,
            remote_name,
            arguments,
            correlation_id=request.correlation_id,
            timeout_seconds=self._clamp_timeout(remaining),
        )
        return self._normalize_outcome(
            specialist, remote_name, request.correlation_id, outcome
        )

    def _require_specialist(self, specialist_id: str) -> SpecialistRef:
        specialist = specialist_ref_or_none(specialist_id)
        if specialist is None:
            raise SpecialistInteropError(
                UNKNOWN_SPECIALIST,
                "specialist is not in the approved allowlist",
            )
        return specialist

    def _policy_invocable(
        self,
        specialist_id: str,
        remote_name: str,
        operation_class: SpecialistOperationClass,
    ) -> bool:
        """Catalog-level eligibility under current DÉLIA policy.

        The class is specialist-owned and live: every owner-typed known
        class is eligible for orchestration (writes still pass the
        generic governed-write chain upstream); UNKNOWN is discoverable
        but never invocable.
        """
        return invocable_in_interactive_phase(operation_class)

    @staticmethod
    def _clamp_timeout(timeout_seconds: float) -> float:
        try:
            value = float(timeout_seconds)
        except (TypeError, ValueError):
            value = MAX_INVOCATION_TIMEOUT_SECONDS
        if value <= 0:
            return MAX_INVOCATION_TIMEOUT_SECONDS
        return min(value, MAX_INVOCATION_TIMEOUT_SECONDS)

    @staticmethod
    def _validate_arguments(
        arguments: Mapping[str, object],
    ) -> Mapping[str, object]:
        if not isinstance(arguments, Mapping):
            raise SpecialistInteropError(
                MCP_INVALID_RESPONSE, "invocation arguments must be a mapping"
            )
        try:
            size = len(json.dumps(arguments, default=str))
        except (TypeError, ValueError) as exc:
            raise SpecialistInteropError(
                MCP_INVALID_RESPONSE, "invocation arguments are not serializable"
            ) from exc
        if size > MAX_INVOCATION_ARGUMENTS_CHARS:
            raise SpecialistInteropError(
                MCP_INVALID_RESPONSE,
                "invocation arguments exceed the bounded subtask size",
            )
        return dict(arguments)

    @staticmethod
    def _normalize_outcome(
        specialist: SpecialistRef,
        remote_name: str,
        correlation_id: str,
        outcome: RemoteToolOutcome,
    ) -> SpecialistOutcome:
        if outcome.is_error:
            detail = "".join(
                ch if ch.isprintable() else " "
                for ch in outcome.content_text[:240]
            ).strip()
            raise SpecialistInteropError(
                MCP_PROTOCOL_ERROR,
                "specialist reported a remote capability error"
                + (f": {detail}" if detail else ""),
            )
        return SpecialistOutcome(
            status=(
                SpecialistResultStatus.COMPLETED
                if outcome.is_complete
                else SpecialistResultStatus.PARTIAL
            ),
            provenance=SpecialistResultProvenance(
                specialist_id=specialist.specialist_id,
                remote_name=remote_name,
                protocol=InteropProtocol.MCP,
                correlation_id=correlation_id,
                observed_at=_now_utc(),
            ),
            content_text=outcome.content_text,
            is_complete=outcome.is_complete,
            structured=outcome.structured,
            limitations=(
                () if outcome.is_complete else ("remote result is partial",)
            ),
        )
