"""MCP adapter behind SpecialistInteropPort — C3-MCP-INTEROP-01.

Binds the approved-specialist registry to the DELPI MCP wire profile.
Second independent fail-closed boundary: before any wire invocation the
owner-typed ``delpi/toolClass`` is re-read from a fresh ``tools/list``
on the same transport and re-checked against DÉLIA policy — unknown
specialist, unconfigured/disabled profile, unadvertised capability,
PREPARE/ACT, unbound DISCOVERY, and non-enabled READ are refused
before ``tools/call`` is sent.

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
    invocable_in_interactive_phase,
    operation_class_from_owner,
)
from app.infrastructure.interoperability.config import (
    SpecialistConnectionProfile,
)
from app.infrastructure.interoperability.delegation import (
    DelegatedCredentialProvider,
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
        credential_provider: DelegatedCredentialProvider | None = None,
        transport_factory: Callable[..., Any] | None = None,
    ) -> None:
        self._connections = dict(connections)
        self._credential_provider = credential_provider
        self._transport_factory = transport_factory or (
            lambda profile, bearer_token: DelpiMcpTransport(
                profile.endpoint,
                timeout_seconds=profile.timeout_seconds,
                bearer_token=bearer_token,
                host_header=profile.host_header,
            )
        )

    @property
    def adapter_kind(self) -> str:
        return self.ADAPTER_KIND

    def list_remote_tools(
        self, specialist: SpecialistRef, *, timeout_seconds: float
    ) -> tuple[RemoteToolDescriptor, ...]:
        profile, transport = self._connect(specialist)
        try:
            tools = transport.list_tools()
        except SpecialistInteropError as exc:
            self._invalidate_on_auth_failure(profile, exc)
            raise
        descriptors: list[RemoteToolDescriptor] = []
        for tool in tools:
            name = tool.get("name")
            if not isinstance(name, str) or not name.strip():
                continue
            meta = tool.get("_meta")
            operation_class = (
                meta.get("delpi/toolClass")
                if isinstance(meta, Mapping)
                else None
            )
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
                    operation_class=(
                        operation_class
                        if isinstance(operation_class, str)
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
        profile, transport = self._connect(specialist)
        try:
            tools = transport.list_tools()
            self._require_invocable(specialist, remote_name, tools)
            result = transport.call_tool(remote_name, arguments)
        except SpecialistInteropError as exc:
            self._invalidate_on_auth_failure(profile, exc)
            raise
        return self._map_outcome(result)

    def _connect(
        self, specialist: SpecialistRef
    ) -> tuple[SpecialistConnectionProfile, Any]:
        profile = self._profile(specialist.specialist_id)
        if self._credential_provider is None:
            # No user-delegated credential mechanism configured —
            # deterministic fail-closed before any wire activity. DÉLIA
            # has no service-token or static-token path to the
            # specialist MCPs.
            raise SpecialistInteropError(
                MCP_AUTHENTICATION_FAILED,
                "no user-delegated credential provider for specialist",
            )
        bearer_token = self._credential_provider.credential_for(profile)
        transport = self._transport_factory(profile, bearer_token)
        try:
            transport.initialize()
        except SpecialistInteropError as exc:
            self._invalidate_on_auth_failure(profile, exc)
            raise
        return profile, transport

    def _invalidate_on_auth_failure(
        self, profile: SpecialistConnectionProfile, exc: SpecialistInteropError
    ) -> None:
        """R1B-R2: any wire-level auth refusal drops the cached credential.

        The next call re-exchanges instead of reusing a rejected token.
        No automatic retry — the failed call still propagates.
        """
        if exc.code == MCP_AUTHENTICATION_FAILED:
            self._credential_provider.invalidate(profile)

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

    def _require_invocable(
        self,
        specialist: SpecialistRef,
        remote_name: str,
        tools: tuple[Mapping[str, Any], ...],
    ) -> None:
        """Second fail-closed gate on a fresh owner tools/list.

        The owner-typed ``delpi/toolClass`` is re-read here — a
        reclassified or removed capability cannot ride a stale grant.
        Class is orchestration policy, not permission: DISCOVERY and
        READ are invocable; PREPARE/ACT/UNKNOWN are refused before
        ``tools/call``.
        """
        tool = next(
            (
                t
                for t in tools
                if t.get("name") == remote_name
                or (
                    isinstance(t.get("name"), str)
                    and t["name"].strip() == remote_name
                )
            ),
            None,
        )
        if tool is None:
            raise SpecialistInteropError(
                UNKNOWN_CAPABILITY,
                "remote capability is not advertised by the specialist",
            )
        meta = tool.get("_meta")
        raw_class = (
            meta.get("delpi/toolClass") if isinstance(meta, Mapping) else None
        )
        operation_class = operation_class_from_owner(raw_class)
        if operation_class in (
            SpecialistOperationClass.PREPARE,
            SpecialistOperationClass.ACT,
        ):
            raise SpecialistInteropError(
                WRITE_CAPABILITY_BLOCKED,
                "write-class capability is never invocable in this slice",
            )
        if not invocable_in_interactive_phase(operation_class):
            raise SpecialistInteropError(
                CAPABILITY_NOT_ALLOWED_IN_PHASE,
                "capability requires a DÉLIA governance binding",
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
