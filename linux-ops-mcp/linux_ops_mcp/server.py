"""Read-only MCP surface. No Docker socket, shell execution, or host mounts."""
from __future__ import annotations

import os
from typing import Any, Literal

from delpi_auth.authz_core import has_permission
from delpi_mcp.identity import require_mcp_context
from delpi_mcp.transport import mcp_transport_security_settings
from delpi_mcp.resource_contract import mcp_allowed_hosts_and_origins
from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from .reader import (
    ItPortalReader, ReadError, deployment_revision, host_health,
    managed_services, service_health,
)

REQUIRED_PERMISSIONS = ("it-portal.access", "it-portal.servers.view")


def _tool_annotations(title: str) -> ToolAnnotations:
    return ToolAnnotations(
        title=title,
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    )


def _context_authorization() -> str:
    context = require_mcp_context()
    user = context.user
    if getattr(user, "principal_type", None) != "user" or getattr(user, "rbac_unavailable", True):
        raise ReadError("forbidden")
    if not all(has_permission(user, permission) for permission in REQUIRED_PERMISSIONS):
        raise ReadError("forbidden")
    if not context.authorization.startswith("Bearer "):
        raise ReadError("unauthorized")
    return context.authorization


def _safe_error(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, (ReadError, PermissionError)):
        return {"ok": False, "error": exc.code if isinstance(exc, ReadError) else "unauthorized"}
    # Never return exception text, upstream response, token, stack or raw log.
    return {"ok": False, "error": "read_unavailable"}


async def _read(projector, *, name: str | None = None) -> dict[str, Any]:
    try:
        bearer = _context_authorization()
        snapshot = await ItPortalReader().latest(bearer)
        if name is not None:
            return {"ok": True, "data": projector(snapshot, name)}
        return {"ok": True, "data": projector(snapshot)}
    except Exception as exc:  # fail closed without exposing upstream details
        return _safe_error(exc)


def security_settings():
    hosts, origins = mcp_allowed_hosts_and_origins(os.getenv("PUBLIC_BASE_URL"))
    return mcp_transport_security_settings(
        allowed_hosts=hosts,
        allowed_origins=origins,
    )


def create_mcp_server() -> MCPServer:
    mcp = MCPServer(
        "delpi-linux-ops",
        instructions=(
            "Read-only host observations from IT Portal. Data can be stale or absent. "
            "No deployment, shell, Docker commands, writes, or remote execution. "
            "Always report observed_at and observation_status; missing data is unknown."
        ),
    )

    @mcp.tool(
        name="get_host_health",
        description="Read sanitized host CPU, RAM, swap, root filesystem and observation freshness.",
        annotations=_tool_annotations("Consultar saude do host Linux"),
        meta={"delpi/toolClass": "READ"},
    )
    async def get_host_health() -> dict[str, Any]:
        return await _read(host_health)

    @mcp.tool(
        name="list_managed_services",
        description="Read only allowlisted systemd service states and aggregated Docker counts.",
        annotations=_tool_annotations("Consultar servicos Linux"),
        meta={"delpi/toolClass": "READ"},
    )
    async def list_managed_services() -> dict[str, Any]:
        return await _read(managed_services)

    @mcp.tool(
        name="get_service_health",
        description="Read observed state of one predefined systemd service. No shell, no Docker control.",
        annotations=_tool_annotations("Consultar estado do servico"),
        meta={"delpi/toolClass": "READ"},
    )
    async def get_service_health(
        service: Literal[
            "docker.service", "containerd.service", "ssh.service",
            "sshd.service", "cron.service", "crond.service",
            "nginx.service", "zabbix-agent.service",
            "zabbix-agent2.service",
        ],
    ) -> dict[str, Any]:
        return await _read(service_health, name=service)

    @mcp.tool(
        name="get_deployment_revision",
        description=(
            "Report deployed revision availability. Read-only Linux observation "
            "does not provide an authoritative SHA; returns not_available."
        ),
        annotations=_tool_annotations("Consultar revisao implantada"),
        meta={"delpi/toolClass": "READ"},
    )
    async def get_deployment_revision() -> dict[str, Any]:
        return await _read(deployment_revision)

    return mcp
