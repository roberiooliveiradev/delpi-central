"""MCP endpoint registration policy — structural + network trust.

Cadastro validation is not a substitute for connection-time SSRF
controls on redirects/rebinding. Trusted internal DELPI hosts are an
explicit allowlist (env), never inferred from attacker-controlled names.
"""

from __future__ import annotations

import ipaddress
import os
import socket
from urllib.parse import urlparse

from app.domain.mcp_providers.lifecycle import McpProviderLifecycleError


# Default trusted DNS names for in-cluster DELPI MCP servers (DEV/compose).
_DEFAULT_TRUSTED_HOSTS = frozenset(
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


def _trusted_hosts() -> frozenset[str]:
    extra = (
        os.getenv("CORE_MCP_TRUSTED_ENDPOINT_HOSTS") or ""
    ).strip()
    hosts = set(_DEFAULT_TRUSTED_HOSTS)
    if extra:
        hosts.update(
            h.strip().lower()
            for h in extra.split(",")
            if h.strip()
        )
    return frozenset(hosts)


def _is_blocked_ip(ip: ipaddress._BaseAddress) -> bool:
    return bool(
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def validate_mcp_endpoint_ref(
    endpoint_ref: str,
    *,
    resolve_dns: bool = True,
) -> str:
    """Validate endpoint for MCP provider registration.

    Raises ``McpProviderLifecycleError`` with stable codes.
    """
    value = str(endpoint_ref or "").strip()
    if not value:
        raise McpProviderLifecycleError(
            "mcp_provider.endpoint_required",
            "endpointRef is required",
        )
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        raise McpProviderLifecycleError(
            "mcp_provider.endpoint_scheme",
            "endpointRef must be http or https",
        )
    if parsed.username or parsed.password:
        raise McpProviderLifecycleError(
            "mcp_provider.endpoint_credentials",
            "endpointRef must not embed credentials",
        )
    if not parsed.hostname:
        raise McpProviderLifecycleError(
            "mcp_provider.endpoint_host",
            "endpointRef must include a host",
        )
    host = parsed.hostname.lower().rstrip(".")
    trusted = _trusted_hosts()

    # Literal IP hosts
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        ip = None

    if ip is not None:
        if host in trusted:
            return value
        if _is_blocked_ip(ip):
            raise McpProviderLifecycleError(
                "mcp_provider.endpoint_ssrf",
                "endpointRef resolves to a disallowed address",
            )
        # Public literal IP allowed only over https
        if parsed.scheme != "https":
            raise McpProviderLifecycleError(
                "mcp_provider.endpoint_https_required",
                "non-trusted endpointRef must use https",
            )
        return value

    # Hostname path
    if host in {"localhost", "metadata.google.internal"} or host.startswith(
        "metadata."
    ):
        raise McpProviderLifecycleError(
            "mcp_provider.endpoint_ssrf",
            "endpointRef host is not allowed",
        )

    if host in trusted:
        # Explicit DELPI internal/compose hosts — http allowed for DEV.
        return value

    if parsed.scheme != "https":
        raise McpProviderLifecycleError(
            "mcp_provider.endpoint_https_required",
            "external endpointRef must use https",
        )

    if not resolve_dns:
        return value

    try:
        infos = socket.getaddrinfo(host, parsed.port or 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise McpProviderLifecycleError(
            "mcp_provider.endpoint_dns",
            f"endpointRef host could not be resolved: {host}",
        ) from exc

    for info in infos:
        sockaddr = info[4]
        raw_ip = sockaddr[0]
        try:
            resolved = ipaddress.ip_address(raw_ip)
        except ValueError:
            continue
        if _is_blocked_ip(resolved):
            raise McpProviderLifecycleError(
                "mcp_provider.endpoint_ssrf",
                "endpointRef DNS resolution points to a disallowed address",
            )
    return value
