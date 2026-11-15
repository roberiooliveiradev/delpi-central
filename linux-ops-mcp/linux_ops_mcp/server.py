"""Read-only MCP surface. No Docker socket, shell execution, or host mounts."""
from __future__ import annotations

import os
from typing import Any, Literal
from types import SimpleNamespace

from delpi_auth.authz_core import has_permission
from delpi_auth.middleware.fastapi_auth import load_user_rbac
from delpi_mcp.identity import require_mcp_context
from delpi_mcp.transport import mcp_transport_security_settings
from delpi_mcp.resource_contract import mcp_allowed_hosts_and_origins
from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations, Tool as MCPTool
from pydantic import ConfigDict
from delpi_mcp.tool_metadata import security_schemes_meta, DELPI_META_TOOL_CLASS
from delpi_mcp.resource_contract import MCP_TRANSPORT_SCOPES

from .reader import (
    ItPortalReader, ReadError, deployment_revision, host_health,
    managed_services, service_health,
)

REQUIRED_PERMISSIONS = ("it-portal.access", "it-portal.servers.view")

READ_TOOLS = frozenset((
    "get_host_health",
    "list_managed_services",
    "get_service_health",
    "get_deployment_revision",
))
OAUTH_SECURITY_SCHEMES = [{"type": "oauth2", "scopes": list(MCP_TRANSPORT_SCOPES)}]


class _LinuxOpsWireTool(MCPTool):
    """Preserve the provider-visible top-level OAuth securitySchemes."""
    model_config = ConfigDict(extra="allow")


class LinuxOpsMCPServer(MCPServer):
    async def list_tools(self) -> list[MCPTool]:
        result: list[MCPTool] = []
        for info in self._tool_manager.list_tools():
            if info.name not in READ_TOOLS:
                raise RuntimeError("Unapproved MCP tool registered")
            meta = dict(info.meta or {})
            meta[DELPI_META_TOOL_CLASS] = "READ"
            meta.update(security_schemes_meta(OAUTH_SECURITY_SCHEMES))
            result.append(_LinuxOpsWireTool.model_validate({
                "name": info.name,
                "title": info.title,
                "description": info.description or "",
                "inputSchema": info.parameters,
                "outputSchema": info.output_schema,
                "annotations": info.annotations,
                "icons": info.icons,
                "_meta": meta,
                "securitySchemes": OAUTH_SECURITY_SCHEMES,
            }))
        return result


def _tool_annotations(title: str) -> ToolAnnotations:
    return ToolAnnotations(
        title=title,
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    )


async def _context_authorization() -> str:
    """Require a fresh Core decision, not stale cached RBAC from an earlier call."""
    context = require_mcp_context()
    user = context.user
    if getattr(user, "principal_type", None) != "user" or getattr(user, "rbac_unavailable", True):
        raise ReadError("forbidden")
    if not context.authorization.startswith("Bearer "):
        raise ReadError("unauthorized")
    token = context.authorization.removeprefix("Bearer ").strip()
    if not token:
        raise ReadError("unauthorized")
    # Canonical Core authority, with stale-cache fallback DISABLED.
    # Any exception is handled by _read as a fail-closed error.
    rbac = await load_user_rbac(token, force_refresh=True)
    if (
        not isinstance(rbac, dict)
        or not rbac.get("id")
        or str(rbac["id"]) != str(getattr(user, "id", ""))
    ):
        raise ReadError("forbidden")
    fresh_user = SimpleNamespace(
        permissions=list(rbac.get("permissions") or ()),
        is_superadmin=rbac.get("is_superadmin") is True,
    )
    if not all(has_permission(fresh_user, permission) for permission in REQUIRED_PERMISSIONS):
        raise ReadError("forbidden")
    return context.authorization

def _safe_error(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, (ReadError, PermissionError)):
        return {"ok": False, "error": exc.code if isinstance(exc, ReadError) else "unauthorized"}
    # Never return exception text, upstream response, token, stack or raw log.
    return {"ok": False, "error": "read_unavailable"}


async def _read(projector, *, name: str | None = None) -> dict[str, Any]:
    try:
        bearer = await _context_authorization()
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
    mcp = LinuxOpsMCPServer(
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
