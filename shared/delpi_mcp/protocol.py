"""MCP protocol-version policy primitives.

Encodes the second VISTA incident as a testable contract: an MCP server
whose SDK's ``LATEST_PROTOCOL_VERSION`` predates the platform minimum cannot
serve clients that demand the modern discovery-era version
(``MCP-Protocol-Version: 2026-07-28`` produced HTTP 400 on ``mcp 1.30``).

Declared-legacy MCPs (existing deployments mid-migration) report the gap as
KNOWN_DRIFT via the conformance result classification — never as PASS.
New or fully migrated MCPs must satisfy the platform minimum outright.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

# Earliest protocol era a DELPI MCP must be able to negotiate/serve.
# Set to the modern discovery-era version proven necessary by the VISTA
# incident (ChatGPT probing MCP-Protocol-Version: 2026-07-28).
DELPI_MCP_PROTOCOL_MINIMUM = "2026-07-28"

ProtocolSupport = Literal["SUPPORTED", "UNSUPPORTED", "LEGACY_ALLOWED_TEMPORARILY"]


@dataclass(frozen=True)
class ProtocolCheck:
    support: ProtocolSupport
    sdk_latest_protocol: str
    platform_minimum: str
    legacy_allowed: bool
    message: str


def _version_key(v: str) -> tuple[int, int, int]:
    """``YYYY-MM-DD`` protocol versions compare chronologically."""
    try:
        y, m, d = (int(p) for p in str(v).split("-"))
    except (ValueError, AttributeError):
        return (0, 0, 0)
    return (y, m, d)


def check_protocol_minimum(
    sdk_latest_protocol: str,
    *,
    legacy_allowed: bool = False,
    platform_minimum: str = DELPI_MCP_PROTOCOL_MINIMUM,
) -> ProtocolCheck:
    """Classify one server's protocol capability against the platform floor.

    ``sdk_latest_protocol`` is the SDK's ``LATEST_PROTOCOL_VERSION`` (or the
    newest version the deployed runtime can serve). ``legacy_allowed`` marks
    a declared migration state (TÉO/DAVI on mcp 1.x); it converts UNSUPPORTED
    into LEGACY_ALLOWED_TEMPORARILY — still reported, never hidden.
    """
    latest = str(sdk_latest_protocol or "").strip()
    if not latest or _version_key(latest) == (0, 0, 0):
        return ProtocolCheck(
            support="UNSUPPORTED",
            sdk_latest_protocol=latest,
            platform_minimum=platform_minimum,
            legacy_allowed=legacy_allowed,
            message="cannot determine SDK latest protocol version",
        )
    if _version_key(latest) >= _version_key(platform_minimum):
        return ProtocolCheck(
            support="SUPPORTED",
            sdk_latest_protocol=latest,
            platform_minimum=platform_minimum,
            legacy_allowed=legacy_allowed,
            message=f"sdk supports {latest} >= platform minimum {platform_minimum}",
        )
    if legacy_allowed:
        return ProtocolCheck(
            support="LEGACY_ALLOWED_TEMPORARILY",
            sdk_latest_protocol=latest,
            platform_minimum=platform_minimum,
            legacy_allowed=True,
            message=(
                f"sdk latest {latest} < platform minimum {platform_minimum}; "
                "declared legacy migration state — must converge"
            ),
        )
    return ProtocolCheck(
        support="UNSUPPORTED",
        sdk_latest_protocol=latest,
        platform_minimum=platform_minimum,
        legacy_allowed=False,
        message=(
            f"sdk latest {latest} < platform minimum {platform_minimum}; "
            "server cannot serve the modern protocol era"
        ),
    )
