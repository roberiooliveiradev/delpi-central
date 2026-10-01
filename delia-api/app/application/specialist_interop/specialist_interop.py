"""SpecialistInterop — C3-MCP-INTEROP-01 use case.

Bounded discovery + bounded subtask delegation to approved specialists
through the provider-neutral SpecialistInteropPort. Two independent
fail-closed boundaries:

1. here: the DÉLIA allowlist classifies every advertised remote
   capability — only DISCOVERY is projected as invocable; READ/PREPARE/
   ACT/unknown names are recorded as blocked;
2. the adapter re-checks the same allowlist before any wire invocation.

Discovery != approval != permission. A catalog result never grants
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
    invocable_in_foundation,
    operation_class_for,
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

        Remote metadata is untrusted data — it is classified by the DÉLIA
        registry, never by its own annotations/descriptions.
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
            operation_class = operation_class_for(
                specialist.specialist_id, tool.remote_name
            )
            if operation_class is not None and invocable_in_foundation(
                operation_class
            ):
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
            else:
                blocked.append(tool.remote_name)
        return SpecialistCatalogResult(
            specialist=specialist,
            capabilities=tuple(capabilities),
            blocked_remote_names=tuple(sorted(blocked)),
            observed_at=observed_at,
        )

    def invoke(self, request: SpecialistInvocationRequest) -> SpecialistOutcome:
        """Delegate one bounded subtask; C3 permits DISCOVERY class only."""
        specialist = self._require_specialist(request.specialist_id)
        remote_name = str(request.remote_capability or "").strip()
        operation_class = operation_class_for(
            specialist.specialist_id, remote_name
        )
        if operation_class is None:
            raise SpecialistInteropError(
                UNKNOWN_CAPABILITY,
                "remote capability is not in the approved specialist registry",
            )
        if not invocable_in_foundation(operation_class):
            if operation_class in (
                SpecialistOperationClass.PREPARE,
                SpecialistOperationClass.ACT,
            ):
                raise SpecialistInteropError(
                    WRITE_CAPABILITY_BLOCKED,
                    "write-class capability is never invocable in this slice",
                )
            raise SpecialistInteropError(
                CAPABILITY_NOT_ALLOWED_IN_PHASE,
                "READ capabilities require the C4 authorization gate",
            )
        arguments = self._validate_arguments(request.arguments)
        outcome = self._port.call_remote_tool(
            specialist,
            remote_name,
            arguments,
            correlation_id=request.correlation_id,
            timeout_seconds=self._clamp_timeout(request.timeout_seconds),
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
