"""MCP adapter behind SpecialistInteropPort — C3-MCP-INTEROP-01.

Binds the approved-specialist registry to the DELPI MCP wire profile.
Second independent fail-closed boundary: the DÉLIA allowlist is
re-checked here before any wire invocation — unknown specialist,
unconfigured/disabled profile, unknown capability, PREPARE/ACT, and
non-DISCOVERY classes are refused before any bytes are sent.

No business rules, no specialist-specific logic, no generic HTTP/MCP
proxy: connections come only from approved-specialist configuration.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from app.application.specialist_interop.contracts import (
    RemoteToolDescriptor,
    RemoteToolOutcome,
)
from app.application.specialist_interop.errors import (
    CAPABILITY_NOT_ALLOWED_IN_PHASE,
    MCP_AUTHENTICATION_FAILED,
    MCP_INVALID_RESPONSE,
    SPECIALIST_DISABLED,
    SPECIALIST_NOT_CONFIGURED,
    UNKNOWN_CAPABILITY,
    UNKNOWN_SPECIALIST,
    WRITE_CAPABILITY_BLOCKED,
    SpecialistInteropError,
)
from app.domain.specialist_interop.model import (
    SpecialistOperationClass,
    SpecialistRef,
)
from app.domain.specialist_interop.rules import (
    APPROVED_SPECIALIST_IDS,
    invocable_in_foundation,
    operation_class_for,
)
from app.infrastructure.interoperability.config import (
    SpecialistConnectionProfile,
)
from app.infrastructure.interoperability.mcp.transport import (
    DelpiMcpTransport,
)


class McpSpecialistAdapter:
    """SpecialistInteropPort implementation over the DELPI MCP profile."""

    ADAPTER_KIND = "MCP"

    def __init__(
        self,
        connections: Mapping[str, SpecialistConnectionProfile],
        *,
        transport_factory: Callable[..., Any] | None = None,
    ) -> None:
        self._connections = dict(connections)
        self._transport_factory = transport_factory or (
            lambda profile: DelpiMcpTransport(
                profile.endpoint,
                timeout_seconds=profile.timeout_seconds,
                bearer_token=profile.user_token,
            )
        )

    @property
    def adapter_kind(self) -> str:
        return self.ADAPTER_KIND

    def list_remote_tools(
        self, specialist: SpecialistRef, *, timeout_seconds: float
    ) -> tuple[RemoteToolDescriptor, ...]:
        transport = self._connect(specialist)
        tools = transport.list_tools()
        descriptors: list[RemoteToolDescriptor] = []
        for tool in tools:
            name = tool.get("name")
            if not isinstance(name, str) or not name.strip():
                continue
            descriptors.append(
                RemoteToolDescriptor(
                    remote_name=name.strip(),
                    title=(
                        tool.get("title")
                        if isinstance(tool.get("title"), str)
                        else None
                    ),
                    description=(
                        tool.get("description")
                        if isinstance(tool.get("description"), str)
                        else None
                    ),
                    input_schema=(
                        tool.get("inputSchema")
                        if isinstance(tool.get("inputSchema"), Mapping)
                        else None
                    ),
                    annotations=(
                        tool.get("annotations")
                        if isinstance(tool.get("annotations"), Mapping)
                        else None
                    ),
                )
            )
        return tuple(descriptors)

    def call_remote_tool(
        self,
        specialist: SpecialistRef,
        remote_name: str,
        arguments: Mapping[str, object],
        *,
        correlation_id: str,
        timeout_seconds: float,
    ) -> RemoteToolOutcome:
        self._require_invocable(specialist, remote_name)
        transport = self._connect(specialist)
        result = transport.call_tool(remote_name, arguments)
        return self._map_outcome(result)

    def _connect(self, specialist: SpecialistRef) -> Any:
        profile = self._profile(specialist.specialist_id)
        if not profile.user_token:
            # No user-delegated credential for the specialist resource —
            # deterministic fail-closed before any wire activity. DÉLIA
            # has no service-token path to the specialist MCPs.
            raise SpecialistInteropError(
                MCP_AUTHENTICATION_FAILED,
                "no user-delegated credential for specialist",
            )
        transport = self._transport_factory(profile)
        transport.initialize()
        return transport

    def _profile(self, specialist_id: str) -> SpecialistConnectionProfile:
        if specialist_id not in APPROVED_SPECIALIST_IDS:
            raise SpecialistInteropError(
                UNKNOWN_SPECIALIST,
                "specialist is not in the approved allowlist",
            )
        profile = self._connections.get(specialist_id)
        if profile is None or not profile.endpoint:
            raise SpecialistInteropError(
                SPECIALIST_NOT_CONFIGURED,
                "specialist endpoint is not configured",
            )
        if not profile.enabled:
            raise SpecialistInteropError(
                SPECIALIST_DISABLED, "specialist connection is disabled"
            )
        return profile

    @staticmethod
    def _require_invocable(
        specialist: SpecialistRef, remote_name: str
    ) -> None:
        operation_class = operation_class_for(
            specialist.specialist_id, remote_name
        )
        if operation_class is None:
            raise SpecialistInteropError(
                UNKNOWN_CAPABILITY,
                "remote capability is not in the approved registry",
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
                "capability requires the C4 authorization gate",
            )

    @staticmethod
    def _map_outcome(result: Mapping[str, Any]) -> RemoteToolOutcome:
        is_error = result.get("isError") is True
        content = result.get("content")
        text_parts: list[str] = []
        if isinstance(content, list):
            for item in content:
                if (
                    isinstance(item, Mapping)
                    and item.get("type") == "text"
                    and isinstance(item.get("text"), str)
                ):
                    text_parts.append(item["text"])
        structured = result.get("structuredContent")
        return RemoteToolOutcome(
            content_text="\n".join(text_parts),
            structured=structured if isinstance(structured, Mapping) else None,
            is_error=is_error,
            is_complete=True,
        )
