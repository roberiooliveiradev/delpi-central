"""MCP protocol-version policy primitives.

Encodes the second VISTA incident as a testable contract: an MCP server
whose SDK's ``LATEST_PROTOCOL_VERSION`` predates the platform minimum cannot
serve clients that demand the modern discovery-era version
(``MCP-Protocol-Version: 2026-07-28`` produced HTTP 400 on ``mcp 1.30``).

Every production MCP runs mcp 2.x; any server below the platform minimum
is a hard FAIL — drift is reported, never hidden.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

# Earliest protocol era a DELPI MCP must be able to negotiate/serve.
# Set to the modern discovery-era version proven necessary by the VISTA
# incident (ChatGPT probing MCP-Protocol-Version: 2026-07-28).
DELPI_MCP_PROTOCOL_MINIMUM = "2026-07-28"

ProtocolSupport = Literal["SUPPORTED", "UNSUPPORTED"]


@dataclass(frozen=True)
class ProtocolCheck:
    support: ProtocolSupport
    sdk_latest_protocol: str
    platform_minimum: str
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
    platform_minimum: str = DELPI_MCP_PROTOCOL_MINIMUM,
) -> ProtocolCheck:
    """Classify one server's protocol capability against the platform floor.

    ``sdk_latest_protocol`` is the SDK's ``LATEST_PROTOCOL_VERSION`` (or the
    newest version the deployed runtime can serve).
    """
    latest = str(sdk_latest_protocol or "").strip()
    if not latest or _version_key(latest) == (0, 0, 0):
        return ProtocolCheck(
            support="UNSUPPORTED",
            sdk_latest_protocol=latest,
            platform_minimum=platform_minimum,
            message="cannot determine SDK latest protocol version",
        )
    if _version_key(latest) >= _version_key(platform_minimum):
        return ProtocolCheck(
            support="SUPPORTED",
            sdk_latest_protocol=latest,
            platform_minimum=platform_minimum,
            message=f"sdk supports {latest} >= platform minimum {platform_minimum}",
        )
    return ProtocolCheck(
        support="UNSUPPORTED",
        sdk_latest_protocol=latest,
        platform_minimum=platform_minimum,
        message=(
            f"sdk latest {latest} < platform minimum {platform_minimum}; "
            "server cannot serve the modern protocol era"
        ),
    )
