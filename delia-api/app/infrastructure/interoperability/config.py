"""Specialist connection profiles — Infrastructure configuration.

Endpoints, enablement, timeouts, and the specialist→resource binding
come from DELIA_MCP_* settings — never hard-coded at call sites, never
logged, never propagated into Domain/Application contracts.

C3-MCP-INTEROP-01R1A: the static global user-token path was removed.
Each profile now carries the specialist's approved MCP *resource*
identity used by the single-requester token exchange:

- ``exchange_audience``: the canonical Keycloak client id that owns the
  specialist MCP resource (the ``audience`` parameter of the exchange);
- ``resource_audience``: the canonical MCP resource URL that must be
  present in the resulting delegated token's ``aud``.

Both default to the documented canonical contract and may only be
narrowed by trusted runtime configuration — never by user/model/tool
metadata. Unknown specialist/resource fails closed.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping

from app.infrastructure.config.settings import Settings


# Canonical MCP OAuth contracts (doc 60 / runbook): one resource client
# and one resource audience per approved specialist. Derived from the
# domain's single governed identity registry — never a second list.
from app.domain.specialist_interop.rules import _SPECIALIST_IDENTITY

CANONICAL_MCP_CLIENT_IDS = {
    sid: identity[2] for sid, identity in _SPECIALIST_IDENTITY.items()
}
CANONICAL_MCP_RESOURCE_AUDIENCES = {
    sid: identity[3] for sid, identity in _SPECIALIST_IDENTITY.items()
}


@dataclass(frozen=True, slots=True)
class SpecialistConnectionProfile:
    """Runtime connection profile for one approved specialist."""

    endpoint: str
    enabled: bool
    timeout_seconds: float
    exchange_audience: str
    resource_audience: str
    host_header: str = ""


def specialist_connections_from_settings(
    settings: Settings,
) -> Mapping[str, SpecialistConnectionProfile]:
    profiles: dict[str, SpecialistConnectionProfile] = {}
    for specialist_id in CANONICAL_MCP_CLIENT_IDS:
        key = specialist_id.upper()
        profiles[specialist_id] = SpecialistConnectionProfile(
            endpoint=settings.mcp_specialist_endpoints.get(specialist_id, ""),
            enabled=settings.mcp_specialist_enabled.get(specialist_id, False),
            timeout_seconds=settings.mcp_timeout_seconds,
            exchange_audience=(
                os.getenv(f"DELIA_MCP_{key}_CLIENT_ID")
                or CANONICAL_MCP_CLIENT_IDS[specialist_id]
            ).strip(),
            resource_audience=(
                os.getenv(f"DELIA_MCP_{key}_RESOURCE_AUDIENCE")
                or CANONICAL_MCP_RESOURCE_AUDIENCES[specialist_id]
            ).strip(),
            host_header=(
                os.getenv(f"DELIA_MCP_{key}_HOST_HEADER") or ""
            ).strip(),
        )
    return profiles
