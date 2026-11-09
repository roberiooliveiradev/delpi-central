"""Repository port for Core MCP provider registry."""

from __future__ import annotations

from typing import Protocol, Sequence

from app.domain.mcp_providers.entities import McpProviderRecord


class McpProviderRepositoryPort(Protocol):
    def get(self, provider_ref: str) -> McpProviderRecord | None: ...

    def list_all(
        self, *, limit: int = 100, offset: int = 0
    ) -> Sequence[McpProviderRecord]: ...

    def list_eligible(self) -> Sequence[McpProviderRecord]: ...

    def save(self, record: McpProviderRecord) -> McpProviderRecord: ...

    def flush(self) -> None: ...
