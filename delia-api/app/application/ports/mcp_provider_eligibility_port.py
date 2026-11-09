"""Port: revalidate Core MCP provider approval at invoke time.

Composition-time eligibility is never a durable grant. Core remains
the approval authority; DÉLIA rechecks before each governed MCP call.
"""

from __future__ import annotations

from typing import Protocol


class McpProviderEligibilityError(Exception):
    """Provider not eligible / Core unavailable / malformed response."""

    def __init__(self, code: str, message: str = "") -> None:
        super().__init__(message or code)
        self.code = code
        self.message = message or code


class McpProviderEligibilityPort(Protocol):
    def require_eligible(self, provider_ref: str) -> None:
        """Raise ``McpProviderEligibilityError`` when not callable.

        Fail closed on Core transport/auth/parse failures — never treat
        composition-time state as sufficient authorization.
        """
        ...
