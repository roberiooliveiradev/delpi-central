"""Specialist connection profiles — Infrastructure configuration.

Endpoints, enablement, timeouts, and the optional user-delegated bearer
token injection point come from DELIA_MCP_* settings — never hard-coded,
never logged, never propagated into Domain/Application contracts.

``user_token`` is a user-delegated OAuth bearer for the specialist's MCP
resource. DÉLIA has no internal service-token path to the specialist MCPs
(they reject service tokens by design); absent a delegated token the
adapter fails closed with MCP_AUTHENTICATION_FAILED.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from app.infrastructure.config.settings import Settings


@dataclass(frozen=True, slots=True)
class SpecialistConnectionProfile:
    """Runtime connection profile for one approved specialist."""

    endpoint: str
    enabled: bool
    timeout_seconds: float
    user_token: str | None = None


def specialist_connections_from_settings(
    settings: Settings,
) -> Mapping[str, SpecialistConnectionProfile]:
    profiles: dict[str, SpecialistConnectionProfile] = {}
    for specialist_id in ("davi", "teo", "vista"):
        profiles[specialist_id] = SpecialistConnectionProfile(
            endpoint=settings.mcp_specialist_endpoints.get(specialist_id, ""),
            enabled=settings.mcp_specialist_enabled.get(specialist_id, False),
            timeout_seconds=settings.mcp_timeout_seconds,
            user_token=settings.mcp_specialist_user_tokens.get(specialist_id),
        )
    return profiles
