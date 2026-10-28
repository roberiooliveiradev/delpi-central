"""MCPServer — EVA read-only MCP surface (get_catalog/home/overview)."""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import CallToolResult, Tool as MCPTool, ToolAnnotations
from pydantic import ConfigDict

from delpi_mcp.tool_metadata import (
    DELPI_META_TOOL_CLASS,
    security_schemes_meta,
    tool_annotations_payload,
)
from delpi_mcp.transport import mcp_transport_security_settings

from engineering_app.interface.mcp.branding import EVA_MCP_INSTRUCTIONS
from engineering_app.interface.mcp.constants import (
    DESTRUCTIVE_ACT_TOOLS,
    TOOL_CLASS,
)
from engineering_app.interface.mcp.oauth_contract import (
    EVA_MCP_SECURITY_SCHEMES,
)
from engineering_app.interface.mcp.resource_metadata import (
    public_host_allowed_for_mcp,
)
from engineering_app.interface.mcp import tool_bridge as bridge

logger = logging.getLogger(__name__)


class _EvaWireTool(MCPTool):
    """Tool wire model preserving the top-level ``securitySchemes`` extension."""

    model_config = ConfigDict(extra="allow")


class EngineeringMCPServer(MCPServer):
    """Expose OAuth securitySchemes on every tool for OpenAI Plugin discovery."""

    async def list_tools(self) -> list[MCPTool]:
        tools = self._tool_manager.list_tools()
        listed: list[MCPTool] = []
        for info in tools:
            meta = dict(info.meta or {})
            # Owner-typed operation class — typed catalog metadata the
            # consumer may project; never a permission grant. Default ACT
            # is the fail-closed class for unregistered names.
            meta[DELPI_META_TOOL_CLASS] = TOOL_CLASS.get(info.name, "ACT")
            schemes = meta.get("securitySchemes") or EVA_MCP_SECURITY_SCHEMES
            payload: dict[str, Any] = {
                "name": info.name,
                "title": info.title,
                "description": info.description or "",
                "inputSchema": info.parameters,
                "outputSchema": info.output_schema,
                "annotations": info.annotations,
                "icons": info.icons,
                "_meta": meta or None,
                "securitySchemes": schemes,
            }
            listed.append(_EvaWireTool.model_validate(payload))
        return listed


def _annotations(tool_name: str, title: str) -> ToolAnnotations:
    kind = TOOL_CLASS.get(tool_name, "ACT")
    read_only = kind in {"DISCOVERY", "READ", "ANALYSIS"}
    destructive = tool_name in DESTRUCTIVE_ACT_TOOLS
    return ToolAnnotations.model_validate(
        tool_annotations_payload(
            title,
            read_only=read_only,
            destructive=destructive,
        )
    )


def eva_mcp_transport_security() -> TransportSecuritySettings:
    hosts, origins = public_host_allowed_for_mcp()
    return mcp_transport_security_settings(
        allowed_hosts=hosts,
        allowed_origins=origins,
    )


def create_mcp_server() -> MCPServer:
    mcp = EngineeringMCPServer(
        name="engineering",
        instructions=EVA_MCP_INSTRUCTIONS,
    )
    meta = security_schemes_meta(EVA_MCP_SECURITY_SCHEMES)

    @mcp.tool(
        name="get_catalog",
        title="Get catalog",
        description=(
            "EVA discovery catalog: implemented tools, capability classes, "
            "input/output schemas, permissions and honest limitations. "
            "Call before any data tool. Planning entries are explicitly "
            "marked not_implemented and are never executable."
        ),
        annotations=_annotations("get_catalog", "Get catalog"),
        meta=meta,
    )
    def get_catalog() -> CallToolResult:
        return bridge.tool_get_catalog()

    @mcp.tool(
        name="get_engineering_home",
        title="Get engineering home",
        description=(
            "READ-only authorized Engineering workspace: sections, "
            "attention items, tasks, requests and LMPs the authenticated "
            "user may see, plus per-source availability (available|empty|"
            "unavailable|forbidden|not_implemented). A failed source is "
            "NOT the same as no work — report availability honestly. "
            "No identity arguments; the caller's token decides the scope."
        ),
        annotations=_annotations("get_engineering_home", "Get engineering home"),
        meta=meta,
    )
    async def get_engineering_home() -> CallToolResult:
        return await bridge.tool_get_engineering_home()

    @mcp.tool(
        name="get_engineering_overview",
        title="Get engineering overview",
        description=(
            "READ-only official Engineering indicators (3 LMP + 3 "
            "TRANSFORMA+): lmp_on_time, lmp_lead_time, "
            "lmp_total_proposals, transforma_gross_savings, "
            "transforma_solutions, transforma_roi — with official values, "
            "units, period, scope and provenance. Goals/IDD only on "
            "lmp_on_time and transforma_gross_savings (owner-authorized). "
            "Filters (optional): start_date/end_date YYYY-MM-DD, "
            "competence YYYY-MM, branch (unidade operacional). EVA never "
            "recalculates indicators."
        ),
        annotations=_annotations("get_engineering_overview", "Get engineering overview"),
        meta=meta,
    )
    async def get_engineering_overview(
        start_date: str | None = None,
        end_date: str | None = None,
        competence: str | None = None,
        branch: str | None = None,
    ) -> CallToolResult:
        return await bridge.tool_get_engineering_overview(
            start_date=start_date,
            end_date=end_date,
            competence=competence,
            branch=branch,
        )

    return mcp
