from __future__ import annotations

from typing import Protocol

from app.application.platform_access import PlatformAccessContext


class PlatformAccessPort(Protocol):
    """Resolve authoritative platform access for a validated user bearer token."""

    def resolve(self, bearer_token: str) -> PlatformAccessContext:
        """Return Core-backed access context.

        Must fail closed on AuthN failure or Core authority unavailability.
        Must not authorize from JWT permission/role claims.
        """


class AuthenticationError(Exception):
    """Bearer token missing, malformed, invalid, or JWT config fail-closed."""


class AuthorityUnavailableError(Exception):
    """Core effective access could not be established."""
