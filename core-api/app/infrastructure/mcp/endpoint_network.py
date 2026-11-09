"""Infrastructure: trusted-host config + DNS for MCP endpoint safety."""

from __future__ import annotations

import os
import socket
from urllib.parse import urlparse

from app.domain.mcp_providers.endpoint_policy import (
    DEFAULT_TRUSTED_ENDPOINT_HOSTS,
    evaluate_mcp_endpoint_ref,
)
from app.domain.mcp_providers.lifecycle import McpProviderLifecycleError


def load_trusted_endpoint_hosts() -> frozenset[str]:
    extra = (os.getenv("CORE_MCP_TRUSTED_ENDPOINT_HOSTS") or "").strip()
    hosts = set(DEFAULT_TRUSTED_ENDPOINT_HOSTS)
    if extra:
        hosts.update(
            h.strip().lower() for h in extra.split(",") if h.strip()
        )
    return frozenset(hosts)


def resolve_endpoint_host_ips(host: str, port: int) -> list[str]:
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise McpProviderLifecycleError(
            "mcp_provider.endpoint_dns",
            f"endpointRef host could not be resolved: {host}",
        ) from exc
    ips: list[str] = []
    for info in infos:
        sockaddr = info[4]
        raw_ip = sockaddr[0]
        if raw_ip not in ips:
            ips.append(str(raw_ip))
    return ips


def assert_registerable_mcp_endpoint(endpoint_ref: str) -> str:
    """Cadastro boundary: structure + trust + DNS resolution checks."""
    trusted = load_trusted_endpoint_hosts()
    evaluate_mcp_endpoint_ref(
        endpoint_ref, trusted_hosts=trusted, resolved_ips=None
    )
    parsed = urlparse(endpoint_ref.strip())
    host = (parsed.hostname or "").lower().rstrip(".")
    if not host:
        raise McpProviderLifecycleError(
            "mcp_provider.endpoint_host",
            "endpointRef must include a host",
        )
    if host in trusted:
        return evaluate_mcp_endpoint_ref(
            endpoint_ref, trusted_hosts=trusted, resolved_ips=None
        )
    try:
        import ipaddress

        ipaddress.ip_address(host)
        # Literal IP — no DNS step
        return evaluate_mcp_endpoint_ref(
            endpoint_ref, trusted_hosts=trusted, resolved_ips=None
        )
    except ValueError:
        pass
    ips = resolve_endpoint_host_ips(host, parsed.port or (443 if parsed.scheme == "https" else 80))
    return evaluate_mcp_endpoint_ref(
        endpoint_ref, trusted_hosts=trusted, resolved_ips=ips
    )
