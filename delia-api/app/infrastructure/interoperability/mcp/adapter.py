"""MCP adapter behind SpecialistInteropPort — C3-MCP-INTEROP-01.

Binds the approved-specialist registry to the DELPI MCP wire profile.
Second independent fail-closed boundary: before any wire invocation the
owner-typed ``delpi/toolClass`` is re-read from a fresh ``tools/list``
on the same transport and re-checked against DÉLIA policy — unknown
specialist, unconfigured/disabled profile, unadvertised capability, and
UNKNOWN-class capabilities are refused before ``tools/call`` is sent.
Every owner-typed known class (DISCOVERY/READ/ANALYSIS-as-READ/
PREPARE/ACT) is eligible; class eligibility is orchestration policy,
never permission — write-class calls still pass the generic
governed-write chain upstream and live Core/Domain AuthZ at the owner
(ledger §6.126).

No business rules, no specialist-specific logic, no generic HTTP/MCP
proxy: connections come only from approved-specialist configuration.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Mapping
from typing import Any

from app.application.interaction.turn_budget import remaining_budget
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

_logger = logging.getLogger(__name__)


# LOOP-03R1 (token expiry): one bounded same-call re-exchange is
# allowed ONLY for non-mutating classes — a read retry is idempotent.
# PREPARE/ACT never retry materially.
_NON_MUTATING_CLASSES = frozenset(
    {
        SpecialistOperationClass.DISCOVERY,
        SpecialistOperationClass.READ,
        SpecialistOperationClass.ANALYSIS,
    }
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
        # LOOP-03R2A-R1: ``timeout_seconds`` bounds the WHOLE port
        # operation (connect+initialize+list) — each wire leg gets
        # only the remaining share, never a fresh full timeout.
        started = time.monotonic()
        profile, transport = self._connect(
            specialist, started=started, budget_seconds=timeout_seconds
        )
        try:
            tools = transport.list_tools(
                timeout_seconds=remaining_budget(
                    started, timeout_seconds
                )
            )
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
        return self._call_remote_tool(
            specialist,
            remote_name,
            arguments,
            correlation_id=correlation_id,
            timeout_seconds=timeout_seconds,
            retried=False,
            started=time.monotonic(),
        )

    def _call_remote_tool(
        self,
        specialist: SpecialistRef,
        remote_name: str,
        arguments: Mapping[str, object],
        *,
        correlation_id: str,
        timeout_seconds: float,
        retried: bool,
        started: float,
    ) -> RemoteToolOutcome:
        operation_class: SpecialistOperationClass | None = None
        profile: SpecialistConnectionProfile | None = None
        try:
            profile, transport = self._connect(
                specialist,
                started=started,
                budget_seconds=timeout_seconds,
            )
            tools = transport.list_tools(
                timeout_seconds=remaining_budget(
                    started, timeout_seconds
                )
            )
            operation_class = self._require_invocable(
                specialist, remote_name, tools
            )
            result = transport.call_tool(
                remote_name,
                arguments,
                timeout_seconds=remaining_budget(
                    started, timeout_seconds
                ),
            )
        except SpecialistInteropError as exc:
            if profile is not None:
                self._invalidate_on_auth_failure(profile, exc)
            if (
                not retried
                and exc.code == MCP_AUTHENTICATION_FAILED
                and (
                    operation_class is None
                    or operation_class in _NON_MUTATING_CLASSES
                )
            ):
                # Token expired/rejected mid-call: the cached credential
                # was invalidated above — one bounded same-call
                # re-exchange + reconnect for an idempotent (non-
                # mutating) operation. The retry re-reads the owner
                # tools/list and re-checks invocability on the fresh
                # transport; a second failure propagates.
                _logger.info(
                    "mcp_call auth_retry specialist=%s capability=%s "
                    "correlation_id=%s",
                    specialist.specialist_id,
                    remote_name,
                    correlation_id,
                )
                return self._call_remote_tool(
                    specialist,
                    remote_name,
                    arguments,
                    correlation_id=correlation_id,
                    timeout_seconds=timeout_seconds,
                    retried=True,
                    started=started,
                )
            raise
        return self._map_outcome(result)

    def _connect(
        self,
        specialist: SpecialistRef,
        *,
        started: float | None = None,
        budget_seconds: float | None = None,
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
            transport.initialize(
                timeout_seconds=(
                    remaining_budget(started, budget_seconds)
                    if started is not None
                    else None
                )
            )
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
    ) -> SpecialistOperationClass:
        """Second fail-closed gate on a fresh owner tools/list.

        The owner-typed ``delpi/toolClass`` is re-read here — a
        reclassified or removed capability cannot ride a stale grant.
        Class is orchestration policy, not permission: every owner-typed
        known class is eligible; UNKNOWN-class and unadvertised names
        are refused before ``tools/call``.
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
        if not invocable_in_interactive_phase(operation_class):
            raise SpecialistInteropError(
                CAPABILITY_NOT_ALLOWED_IN_PHASE,
                "capability class is not eligible for orchestration",
            )
        return operation_class

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
