"""SpecialistInterop — C3-MCP-INTEROP-01 use case.

Bounded discovery + bounded subtask delegation to approved specialists
through the provider-neutral SpecialistInteropPort. Two independent
fail-closed boundaries:

1. here: the owner-typed ``delpi/toolClass`` classifies every
   advertised remote capability — only capabilities with a matching
   DÉLIA governance binding are invocable (DISCOVERY bindings, or the
   exact enabled READ tuples); everything else is recorded as blocked;
2. the adapter re-checks owner class + DÉLIA policy against a fresh
   tools/list before any wire invocation.

Discovery != approval != permission. The remote specialist owns its
catalog; DÉLIA keeps no tool-name mirror. A catalog result never grants
anything; a specialist outcome is untrusted OBSERVATION data.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Mapping

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
    UNKNOWN_CAPABILITY,
    UNKNOWN_SPECIALIST,
    WRITE_CAPABILITY_BLOCKED,
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
    discovery_binding_allowed,
    governed_read_action_allowed,
    operation_class_from_owner,
    specialist_ref_or_none,
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


class SpecialistInterop:
    """One provider-neutral boundary for approved specialist interaction."""

    def __init__(
        self,
        port: SpecialistInteropPort,
        *,
        enabled_governed_reads: frozenset[tuple[str, str, str]]
        | None = None,
    ) -> None:
        self._port = port
        # C4-MCP-GOVERNED-READS-01/02: the exact authorized READ tuples
        # enabled by trusted server configuration. Without an entry here
        # every READ stays CAPABILITY_NOT_ALLOWED_IN_PHASE — enabling one
        # binding never enables another.
        self._enabled_governed_reads = frozenset(
            tuple(str(part).strip() for part in entry)
            for entry in (enabled_governed_reads or frozenset())
        )

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
        if operation_class in (
            SpecialistOperationClass.PREPARE,
            SpecialistOperationClass.ACT,
        ):
            raise SpecialistInteropError(
                WRITE_CAPABILITY_BLOCKED,
                "write-class capability is never invocable in this slice",
            )
        allowed = operation_class is SpecialistOperationClass.DISCOVERY
        allowed = allowed and discovery_binding_allowed(
            specialist.specialist_id, remote_name
        )
        if not allowed and operation_class is SpecialistOperationClass.READ:
            governed_tuple = (
                specialist.specialist_id,
                remote_name,
                str(request.governed_action_id or "").strip(),
            )
            allowed = (
                governed_tuple in self._enabled_governed_reads
                and governed_read_action_allowed(
                    specialist.specialist_id,
                    remote_name,
                    request.governed_action_id,
                )
            )
        if not allowed:
            raise SpecialistInteropError(
                CAPABILITY_NOT_ALLOWED_IN_PHASE,
                "capability is not allowed in this phase",
            )
        arguments = self._validate_arguments(request.arguments)
        outcome = self._port.call_remote_tool(
            specialist,
            remote_name,
            arguments,
            correlation_id=request.correlation_id,
            timeout_seconds=self._clamp_timeout(request.timeout_seconds),
            governed_action_id=request.governed_action_id,
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

        DISCOVERY requires a governed binding; READ requires an enabled
        governed tuple for the (specialist, capability) pair; PREPARE/
        ACT/UNKNOWN are never invocable in this phase.
        """
        if operation_class is SpecialistOperationClass.DISCOVERY:
            return discovery_binding_allowed(specialist_id, remote_name)
        if operation_class is SpecialistOperationClass.READ:
            return any(
                (s, n) == (specialist_id, remote_name)
                for s, n, _ in self._enabled_governed_reads
            )
        return False

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
            raise SpecialistInteropError(
                MCP_PROTOCOL_ERROR,
                "specialist reported a remote capability error",
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
