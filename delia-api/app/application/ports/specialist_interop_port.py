"""Application-facing port for provider-neutral specialist interoperability.

C3-MCP-INTEROP-01: single boundary between DÉLIA Application and existing
approved specialist providers (DAVI / TÉO / VISTA). Implementations live in
Infrastructure and may use MCP; the port itself carries no MCP SDK,
JSON-RPC, HTTP, or vendor types — a future A2A adapter could implement the
same contract.

This is not a generic HTTP/tool proxy: it is bound to the approved
specialist registry and to the DÉLIA-owned operation-class allowlist.
"""

from __future__ import annotations

from typing import Mapping, Protocol

from app.application.specialist_interop.contracts import (
    RemoteToolDescriptor,
    RemoteToolOutcome,
)
from app.domain.specialist_interop.model import SpecialistRef


class SpecialistInteropPort(Protocol):
    """Bounded specialist interaction. Semantic codes only on failure."""

    @property
    def adapter_kind(self) -> str:
        """e.g. 'MCP'. Transport/protocol kind; never a vendor name."""

    def list_remote_tools(
        self, specialist: SpecialistRef, *, timeout_seconds: float
    ) -> tuple[RemoteToolDescriptor, ...]:
        """Return the remote capability surface as untrusted descriptors.

        Must raise SpecialistInteropError with a semantic code — never a
        raw transport/SDK exception.
        """

    def call_remote_tool(
        self,
        specialist: SpecialistRef,
        remote_name: str,
        arguments: Mapping[str, object],
        *,
        correlation_id: str,
        timeout_seconds: float,
    ) -> RemoteToolOutcome:
        """Invoke one approved remote capability, fail closed.

        Implementations must re-check the owner class on a fresh
        tools/list (unknown specialist/capability, PREPARE/ACT, phase
        gate) before any wire activity — invocation is the second
        enforcement boundary.
        """
