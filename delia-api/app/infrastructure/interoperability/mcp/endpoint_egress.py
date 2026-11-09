"""Connection-time MCP endpoint egress checks (DÉLIA transport boundary).

Cadastro validation in Core does not substitute re-checking the
destination at connect time. Pure classification — no Core import.
Trusted internal hosts come from explicit env allowlist.
"""

from __future__ import annotations

import ipaddress
import os
import socket
from urllib.parse import urlparse

from app.application.specialist_interop.errors import SpecialistInteropError

_DEFAULT_TRUSTED = frozenset(
    {
        "delpi-api-delpi",
        "api-delpi",
        "transformometro-api",
        "tv-dashboard-api",
        "commercial-api",
        "controllership-finance-api",
        "supplies-api",
        "supplies-mcp",
        "engineering-api",
        "delpi-core-api",
        "core-api",
    }
)

MCP_ENDPOINT_EGRESS_DENIED = "mcp_endpoint_egress_denied"


def _trusted_hosts() -> frozenset[str]:
    extra = (os.getenv("DELIA_MCP_TRUSTED_ENDPOINT_HOSTS") or "").strip()
    hosts = set(_DEFAULT_TRUSTED)
    # Align with Core allowlist when present in the same compose stack.
    core_extra = (os.getenv("CORE_MCP_TRUSTED_ENDPOINT_HOSTS") or "").strip()
    for blob in (extra, core_extra):
        if blob:
            hosts.update(h.strip().lower() for h in blob.split(",") if h.strip())
    return frozenset(hosts)


def _disallowed(ip: ipaddress._BaseAddress) -> bool:
    return bool(
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def assert_endpoint_allowed_for_connect(endpoint: str) -> None:
    """Fail closed before opening MCP transport to ``endpoint``."""
    value = str(endpoint or "").strip()
    if not value:
        raise SpecialistInteropError(
            MCP_ENDPOINT_EGRESS_DENIED,
            "mcp endpoint missing",
        )
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        raise SpecialistInteropError(
            MCP_ENDPOINT_EGRESS_DENIED,
            "mcp endpoint scheme not allowed",
        )
    if parsed.username or parsed.password:
        raise SpecialistInteropError(
            MCP_ENDPOINT_EGRESS_DENIED,
            "mcp endpoint must not embed credentials",
        )
    host = (parsed.hostname or "").lower().rstrip(".")
    if not host:
        raise SpecialistInteropError(
            MCP_ENDPOINT_EGRESS_DENIED,
            "mcp endpoint host missing",
        )
    trusted = _trusted_hosts()
    if host in {"localhost", "metadata.google.internal"} or host.startswith(
        "metadata."
    ):
        raise SpecialistInteropError(
            MCP_ENDPOINT_EGRESS_DENIED,
            "mcp endpoint host not allowed",
        )
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        ip = None
    if ip is not None:
        if host not in trusted and _disallowed(ip):
            raise SpecialistInteropError(
                MCP_ENDPOINT_EGRESS_DENIED,
                "mcp endpoint address not allowed",
            )
        if host not in trusted and parsed.scheme != "https":
            raise SpecialistInteropError(
                MCP_ENDPOINT_EGRESS_DENIED,
                "non-trusted mcp endpoint must use https",
            )
        return
    if host in trusted:
        return
    if parsed.scheme != "https":
        raise SpecialistInteropError(
            MCP_ENDPOINT_EGRESS_DENIED,
            "external mcp endpoint must use https",
        )
    port = parsed.port or 443
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise SpecialistInteropError(
            MCP_ENDPOINT_EGRESS_DENIED,
            f"mcp endpoint DNS failed: {host}",
        ) from exc
    for info in infos:
        raw_ip = info[4][0]
        try:
            resolved = ipaddress.ip_address(raw_ip)
        except ValueError:
            continue
        if _disallowed(resolved):
            raise SpecialistInteropError(
                MCP_ENDPOINT_EGRESS_DENIED,
                "mcp endpoint DNS resolved to a disallowed address",
            )
