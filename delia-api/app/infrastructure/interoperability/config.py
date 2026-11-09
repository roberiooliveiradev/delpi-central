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


def specialist_connections_from_core_eligible(
    settings: Settings,
    eligible_items: list[Mapping[str, object]],
) -> Mapping[str, SpecialistConnectionProfile]:
    """Build profiles from Core eligibility projection.

    Only Core-eligible providers are enabled. Unknown provider refs that
    are not in the domain identity registry are ignored (fail closed for
    that row) — ExternalConnection/onboarding of novel providers is a
    separate contract.
    """
    profiles: dict[str, SpecialistConnectionProfile] = {}
    for raw in eligible_items:
        if not isinstance(raw, Mapping):
            continue
        specialist_id = str(raw.get("providerRef") or "").strip().lower()
        if not specialist_id or specialist_id not in CANONICAL_MCP_CLIENT_IDS:
            continue
        endpoint = str(raw.get("endpointRef") or "").strip()
        if not endpoint:
            continue
        key = specialist_id.upper()
        exchange = str(
            raw.get("resourceClientId")
            or os.getenv(f"DELIA_MCP_{key}_CLIENT_ID")
            or CANONICAL_MCP_CLIENT_IDS[specialist_id]
        ).strip()
        audience = str(
            raw.get("resourceAudience")
            or os.getenv(f"DELIA_MCP_{key}_RESOURCE_AUDIENCE")
            or CANONICAL_MCP_RESOURCE_AUDIENCES[specialist_id]
        ).strip()
        profiles[specialist_id] = SpecialistConnectionProfile(
            endpoint=endpoint,
            enabled=True,
            timeout_seconds=settings.mcp_timeout_seconds,
            exchange_audience=exchange,
            resource_audience=audience,
            host_header=(
                os.getenv(f"DELIA_MCP_{key}_HOST_HEADER") or ""
            ).strip(),
        )
    # Preserve disabled slots for known specialists so adapters keep a
    # stable key set without enabling them.
    for specialist_id in CANONICAL_MCP_CLIENT_IDS:
        if specialist_id in profiles:
            continue
        key = specialist_id.upper()
        profiles[specialist_id] = SpecialistConnectionProfile(
            endpoint=settings.mcp_specialist_endpoints.get(specialist_id, ""),
            enabled=False,
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
