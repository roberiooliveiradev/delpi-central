"""Infrastructure adapter: live Core eligibility recheck (no durable cache)."""

from __future__ import annotations

from app.application.ports.mcp_provider_eligibility_port import (
    McpProviderEligibilityError,
)
from app.infrastructure.interoperability.mcp.core_provider_registry import (
    CoreMcpProviderRegistryClient,
    CoreMcpProviderRegistryError,
)


class CoreMcpProviderEligibilityGuard:
    """Fresh S2S eligibility check per invoke — not an authoritative cache."""

    def __init__(self, client: CoreMcpProviderRegistryClient) -> None:
        self._client = client

    def require_eligible(self, provider_ref: str) -> None:
        pref = str(provider_ref or "").strip().lower()
        if not pref:
            raise McpProviderEligibilityError(
                "mcp_provider_ref_required",
                "provider ref required for eligibility revalidation",
            )
        try:
            items = self._client.list_eligible()
        except CoreMcpProviderRegistryError as exc:
            raise McpProviderEligibilityError(
                "mcp_provider_registry_unavailable",
                str(exc),
            ) from exc
        eligible = {
            str(i.get("providerRef") or "").strip().lower()
            for i in items
            if isinstance(i, dict)
        }
        if pref not in eligible:
            raise McpProviderEligibilityError(
                "mcp_provider_not_eligible",
                f"provider {pref!r} is not currently Core-eligible "
                "(revoked, disabled, unapproved, or missing)",
            )
