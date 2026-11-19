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

from .multiserver import (
    get_infrastructure_health,
    get_server_health,
    get_server_services,
    list_servers,
)
from .reader import (
    ItPortalReader, ReadError, deployment_revision, host_health,
    managed_services, service_health, Settings,
)
from .windows_service_actions import (
    confirm_windows_service_action,
    prepare_windows_service_action,
)

REQUIRED_PERMISSIONS = ("it-portal.access", "it-portal.servers.view")
CONTROL_PERMISSIONS = (
    "it-portal.access",
    "it-portal.servers.view",
    "it-portal.host-services.control",
)

READ_TOOLS = frozenset((
    "get_host_health",
    "list_managed_services",
    "get_service_health",
    "get_deployment_revision",
    "list_servers",
    "get_server_health",
    "get_infrastructure_health",
    "get_server_services",
))
CONTROL_TOOLS = frozenset((
    "start_windows_service",
    "stop_windows_service",
    "restart_windows_service",
    "prepare_windows_service_action",
    "confirm_windows_service_action",
))
APPROVED_TOOLS = READ_TOOLS | CONTROL_TOOLS
OAUTH_SECURITY_SCHEMES = [{"type": "oauth2", "scopes": list(MCP_TRANSPORT_SCOPES)}]


class _LinuxOpsWireTool(MCPTool):
    """Preserve the provider-visible top-level OAuth securitySchemes."""
    model_config = ConfigDict(extra="allow")


class LinuxOpsMCPServer(MCPServer):
    async def list_tools(self) -> list[MCPTool]:
        result: list[MCPTool] = []
        for info in self._tool_manager.list_tools():
            if info.name not in APPROVED_TOOLS:
                raise RuntimeError("Unapproved MCP tool registered")
            meta = dict(info.meta or {})
            tool_class = "ACT" if info.name in CONTROL_TOOLS else "READ"
            meta[DELPI_META_TOOL_CLASS] = tool_class
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


def _tool_annotations(title: str, *, read_only: bool = True, destructive: bool = False) -> ToolAnnotations:
    return ToolAnnotations(
        title=title,
        readOnlyHint=read_only,
        destructiveHint=destructive,
        idempotentHint=read_only,
        openWorldHint=False,
    )


async def _context_authorization(
    *,
    required_permissions: tuple[str, ...] = REQUIRED_PERMISSIONS,
) -> str:
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
    if not all(has_permission(fresh_user, permission) for permission in required_permissions):
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
        snapshot = await ItPortalReader(
            Settings.from_environment(require_legacy_server_id=True),
        ).latest(bearer)
        if name is not None:
            return {"ok": True, "data": projector(snapshot, name)}
        return {"ok": True, "data": projector(snapshot)}
    except Exception as exc:  # fail closed without exposing upstream details
        return _safe_error(exc)


async def _multiread(operation) -> dict[str, Any]:
    try:
        bearer = await _context_authorization()
        reader = ItPortalReader(Settings.from_environment(require_legacy_server_id=False))
        data = await operation(reader, bearer)
        if isinstance(data, dict) and data.get("ok") is False and data.get("error"):
            return data
        return {"ok": True, "data": data}
    except Exception as exc:
        return _safe_error(exc)


def security_settings():
    hosts, origins = mcp_allowed_hosts_and_origins(os.getenv("PUBLIC_BASE_URL"))
    return mcp_transport_security_settings(
        allowed_hosts=hosts,
        allowed_origins=origins,
    )


async def _control(operation) -> dict[str, Any]:
    try:
        bearer = await _context_authorization(required_permissions=CONTROL_PERMISSIONS)
        return await operation(bearer)
    except Exception as exc:
        return _safe_error(exc)


def create_mcp_server() -> MCPServer:
    mcp = LinuxOpsMCPServer(
        "delpi-linux-ops",
        instructions=(
            "Host observations and governed Windows service control via IT Portal. "
            "Prefer list_servers, get_server_health, get_infrastructure_health and "
            "get_server_services for diagnosis. Windows control requires prepare then "
            "explicit confirm_windows_service_action with user_confirmed=true; never "
            "treat the original request as confirmation. control_allowed marks "
            "controllable services. No deployment PREPARE/ACT, shell, Docker, or "
            "arbitrary PowerShell. Always report observed evidence; never claim success "
            "from queue acceptance alone."
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

    @mcp.tool(
        name="list_servers",
        description=(
            "List servers registered in IT Portal inventory. Filters: unit, environment, "
            "OS family (linux/windows), criticality, administrative status. Archived "
            "servers are excluded by default. Paginate explicitly; does not silently "
            "stop at the first page."
        ),
        annotations=_tool_annotations("Listar servidores do Portal de TI"),
        meta={"delpi/toolClass": "READ"},
    )
    async def list_servers_tool(
        q: str | None = None,
        unit_code: str | None = None,
        environment: str | None = None,
        criticality: str | None = None,
        os_family: Literal["linux", "windows"] | None = None,
        administrative_status: str | None = None,
        include_archived: bool = False,
        page: int = 1,
        page_size: int = 25,
    ) -> dict[str, Any]:
        async def operation(reader, bearer):
            return await list_servers(
                reader,
                bearer,
                q=q,
                unit_code=unit_code,
                environment=environment,
                criticality=criticality,
                os_family=os_family,
                administrative_status=administrative_status,
                include_archived=include_archived,
                page=page,
                page_size=page_size,
            )
        return await _multiread(operation)

    @mcp.tool(
        name="get_server_health",
        description=(
            "Analyze health for one IT Portal server by UUID or hostname. Supports "
            "Linux and Windows observations. Does not invent missing metrics. Ambiguous "
            "hostnames return candidates without arbitrary selection."
        ),
        annotations=_tool_annotations("Consultar saude de um servidor"),
        meta={"delpi/toolClass": "READ"},
    )
    async def get_server_health_tool(
        server_id: str | None = None,
        hostname: str | None = None,
        include_archived: bool = False,
    ) -> dict[str, Any]:
        async def operation(reader, bearer):
            return await get_server_health(
                reader,
                bearer,
                server_id=server_id,
                hostname=hostname,
                include_archived=include_archived,
            )
        return await _multiread(operation)

    @mcp.tool(
        name="get_infrastructure_health",
        description=(
            "Consolidate health across registered IT Portal servers. Uses bounded "
            "concurrency, isolates per-server failures, and reports missing/stale/"
            "partial observations separately from host health."
        ),
        annotations=_tool_annotations("Diagnostico consolidado da infraestrutura"),
        meta={"delpi/toolClass": "READ"},
    )
    async def get_infrastructure_health_tool(
        unit_code: str | None = None,
        environment: str | None = None,
        criticality: str | None = None,
        os_family: Literal["linux", "windows"] | None = None,
        include_archived: bool = False,
        page: int = 1,
        page_size: int = 25,
    ) -> dict[str, Any]:
        async def operation(reader, bearer):
            return await get_infrastructure_health(
                reader,
                bearer,
                unit_code=unit_code,
                environment=environment,
                criticality=criticality,
                os_family=os_family,
                include_archived=include_archived,
                page=page,
                page_size=page_size,
            )
        return await _multiread(operation)

    @mcp.tool(
        name="get_server_services",
        description=(
            "List observed services for one server. Windows uses IT Portal host-services "
            "inventory; Linux uses allowlisted systemd states from the latest observation. "
            "Read-only; never starts/stops services."
        ),
        annotations=_tool_annotations("Consultar servicos de um servidor"),
        meta={"delpi/toolClass": "READ"},
    )
    async def get_server_services_tool(
        server_id: str | None = None,
        hostname: str | None = None,
        include_archived: bool = False,
        state: str | None = None,
        q: str | None = None,
        favorites_only: bool = False,
        critical_only: bool = False,
        page: int = 1,
        page_size: int = 25,
        include_windows_dashboard: bool = False,
    ) -> dict[str, Any]:
        async def operation(reader, bearer):
            return await get_server_services(
                reader,
                bearer,
                server_id=server_id,
                hostname=hostname,
                include_archived=include_archived,
                state=state,
                q=q,
                favorites_only=favorites_only,
                critical_only=critical_only,
                page=page,
                page_size=page_size,
                include_windows_dashboard=include_windows_dashboard,
            )
        return await _multiread(operation)

    @mcp.tool(
        name="prepare_windows_service_action",
        description=(
            "Prepare a Windows service start/stop/restart against IT Portal allowlist. "
            "Returns confirmation_id; does not execute. Requires host-services.control."
        ),
        annotations=_tool_annotations(
            "Preparar acao de servico Windows", read_only=False, destructive=True,
        ),
        meta={"delpi/toolClass": "ACT"},
    )
    async def prepare_windows_service_action_tool(
        action: Literal["start", "stop", "restart"],
        service_name: str,
        server_id: str | None = None,
        hostname: str | None = None,
        include_archived: bool = False,
    ) -> dict[str, Any]:
        async def operation(bearer):
            return await prepare_windows_service_action(
                authorization=bearer,
                action=action,
                server_id=server_id,
                hostname=hostname,
                service_name=service_name,
                include_archived=include_archived,
            )
        return await _control(operation)

    @mcp.tool(
        name="start_windows_service",
        description=(
            "Prepare start of an allowlisted Windows service. Never executes alone; "
            "returns confirmation_id for confirm_windows_service_action."
        ),
        annotations=_tool_annotations(
            "Preparar inicio de servico Windows", read_only=False, destructive=True,
        ),
        meta={"delpi/toolClass": "ACT"},
    )
    async def start_windows_service_tool(
        service_name: str,
        server_id: str | None = None,
        hostname: str | None = None,
        include_archived: bool = False,
    ) -> dict[str, Any]:
        async def operation(bearer):
            return await prepare_windows_service_action(
                authorization=bearer,
                action="start",
                server_id=server_id,
                hostname=hostname,
                service_name=service_name,
                include_archived=include_archived,
            )
        return await _control(operation)

    @mcp.tool(
        name="stop_windows_service",
        description=(
            "Prepare stop of an allowlisted Windows service. Never executes alone; "
            "returns confirmation_id for confirm_windows_service_action."
        ),
        annotations=_tool_annotations(
            "Preparar parada de servico Windows", read_only=False, destructive=True,
        ),
        meta={"delpi/toolClass": "ACT"},
    )
    async def stop_windows_service_tool(
        service_name: str,
        server_id: str | None = None,
        hostname: str | None = None,
        include_archived: bool = False,
    ) -> dict[str, Any]:
        async def operation(bearer):
            return await prepare_windows_service_action(
                authorization=bearer,
                action="stop",
                server_id=server_id,
                hostname=hostname,
                service_name=service_name,
                include_archived=include_archived,
            )
        return await _control(operation)

    @mcp.tool(
        name="restart_windows_service",
        description=(
            "Prepare restart of an allowlisted Windows service. Never executes alone; "
            "returns confirmation_id for confirm_windows_service_action."
        ),
        annotations=_tool_annotations(
            "Preparar reinicio de servico Windows", read_only=False, destructive=True,
        ),
        meta={"delpi/toolClass": "ACT"},
    )
    async def restart_windows_service_tool(
        service_name: str,
        server_id: str | None = None,
        hostname: str | None = None,
        include_archived: bool = False,
    ) -> dict[str, Any]:
        async def operation(bearer):
            return await prepare_windows_service_action(
                authorization=bearer,
                action="restart",
                server_id=server_id,
                hostname=hostname,
                service_name=service_name,
                include_archived=include_archived,
            )
        return await _control(operation)

    @mcp.tool(
        name="confirm_windows_service_action",
        description=(
            "Execute a previously prepared Windows service action after explicit human "
            "confirmation. Requires confirmation_id and user_confirmed=true. Revalidates "
            "permissions and polls IT Portal for proven state_after."
        ),
        annotations=_tool_annotations(
            "Confirmar acao de servico Windows", read_only=False, destructive=True,
        ),
        meta={"delpi/toolClass": "ACT"},
    )
    async def confirm_windows_service_action_tool(
        confirmation_id: str,
        user_confirmed: bool,
        action: Literal["start", "stop", "restart"],
        service_name: str,
        server_id: str | None = None,
        hostname: str | None = None,
        include_archived: bool = False,
    ) -> dict[str, Any]:
        async def operation(bearer):
            return await confirm_windows_service_action(
                authorization=bearer,
                confirmation_id=confirmation_id,
                user_confirmed=user_confirmed,
                server_id=server_id,
                hostname=hostname,
                service_name=service_name,
                action=action,
                include_archived=include_archived,
            )
        return await _control(operation)

    return mcp
