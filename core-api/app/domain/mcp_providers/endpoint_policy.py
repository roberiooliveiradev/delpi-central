"""Pure MCP endpoint eligibility rules (no env, no DNS, no I/O).

Cadastro and connection-time callers supply trusted hosts and any
resolved addresses. Infrastructure owns env loading and DNS resolution.
"""

from __future__ import annotations

import ipaddress
from collections.abc import Sequence
from urllib.parse import urlparse

from app.domain.mcp_providers.lifecycle import McpProviderLifecycleError

# Default trusted DNS names for in-cluster DELPI MCP servers (DEV/compose).
# Callers may extend via configuration — never via attacker-controlled names.
DEFAULT_TRUSTED_ENDPOINT_HOSTS = frozenset(
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


def is_disallowed_ip(ip: ipaddress._BaseAddress) -> bool:
    return bool(
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def evaluate_mcp_endpoint_ref(
    endpoint_ref: str,
    *,
    trusted_hosts: frozenset[str] | set[str] = DEFAULT_TRUSTED_ENDPOINT_HOSTS,
    resolved_ips: Sequence[str] | None = None,
) -> str:
    """Evaluate endpoint structure and optional resolved addresses.

    ``resolved_ips is None`` → structural/trust checks only (no DNS
    evidence yet). ``resolved_ips`` provided → every resolved address
    must be allowed (empty sequence is treated as DNS failure by the
    caller before invoking this function).
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
    trusted = frozenset(h.strip().lower() for h in trusted_hosts if h)

    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        ip = None

    if ip is not None:
        if host in trusted:
            return value
        if is_disallowed_ip(ip):
            raise McpProviderLifecycleError(
                "mcp_provider.endpoint_ssrf",
                "endpointRef resolves to a disallowed address",
            )
        if parsed.scheme != "https":
            raise McpProviderLifecycleError(
                "mcp_provider.endpoint_https_required",
                "non-trusted endpointRef must use https",
            )
        return value

    if host in {"localhost", "metadata.google.internal"} or host.startswith(
        "metadata."
    ):
        raise McpProviderLifecycleError(
            "mcp_provider.endpoint_ssrf",
            "endpointRef host is not allowed",
        )

    if host in trusted:
        return value

    if parsed.scheme != "https":
        raise McpProviderLifecycleError(
            "mcp_provider.endpoint_https_required",
            "external endpointRef must use https",
        )

    if resolved_ips is None:
        return value

    for raw_ip in resolved_ips:
        try:
            resolved = ipaddress.ip_address(raw_ip)
        except ValueError:
            continue
        if is_disallowed_ip(resolved):
            raise McpProviderLifecycleError(
                "mcp_provider.endpoint_ssrf",
                "endpointRef DNS resolution points to a disallowed address",
            )
    return value


# Backward-compatible alias used by older tests during migration.
def validate_mcp_endpoint_ref(
    endpoint_ref: str,
    *,
    resolve_dns: bool = True,
    trusted_hosts: frozenset[str] | set[str] = DEFAULT_TRUSTED_ENDPOINT_HOSTS,
    resolved_ips: Sequence[str] | None = None,
) -> str:
    """Compatibility wrapper — prefer ``evaluate_mcp_endpoint_ref``.

    When ``resolve_dns=True`` and ``resolved_ips`` is omitted, this
    wrapper only performs structural checks (DNS belongs to infrastructure).
    """
    del resolve_dns  # DNS is never performed in domain
    return evaluate_mcp_endpoint_ref(
        endpoint_ref,
        trusted_hosts=trusted_hosts,
        resolved_ips=resolved_ips,
    )
