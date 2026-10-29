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
    read_only = kind in {"DISCOVERY", "READ", "ANALYSIS", "PREPARE"}
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

    @mcp.tool(
        name="search_nonconformities",
        title="Search nonconformities",
        description=(
            "READ-only paginated LMP nonconformity list. Filters "
            "(optional): status open|in_progress|done, sale_number (OV), "
            "lmp_number, customer_name, product_code, problem_tag, "
            "date_start/date_end (YYYY-MM-DD, occurrence period), "
            "sort_by/sort_dir, page/page_size. Data comes only from the "
            "Engineering-owned nonconformity store; empty is honest."
        ),
        annotations=_annotations("search_nonconformities", "Search nonconformities"),
        meta=meta,
    )
    async def search_nonconformities(
        status: str | None = None,
        sale_number: str | None = None,
        lmp_number: str | None = None,
        customer_name: str | None = None,
        product_code: str | None = None,
        problem_tag: str | None = None,
        date_start: str | None = None,
        date_end: str | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> CallToolResult:
        return await bridge.tool_search_nonconformities(
            status=status,
            sale_number=sale_number,
            lmp_number=lmp_number,
            customer_name=customer_name,
            product_code=product_code,
            problem_tag=problem_tag,
            date_start=date_start,
            date_end=date_end,
            sort_by=sort_by,
            sort_dir=sort_dir,
            page=page,
            page_size=page_size,
        )

    @mcp.tool(
        name="get_nonconformity",
        title="Get nonconformity",
        description=(
            "READ-only detail of a single nonconformity by UUID "
            "(record_id): status, dates, OV/LMP, people, defect, "
            "corrective actions, opinion, products, tags and audit "
            "fields. 404 is honest when the id does not exist."
        ),
        annotations=_annotations("get_nonconformity", "Get nonconformity"),
        meta=meta,
    )
    async def get_nonconformity(record_id: str) -> CallToolResult:
        return await bridge.tool_get_nonconformity(record_id=record_id)

    @mcp.tool(
        name="get_nonconformity_history",
        title="Get nonconformity history",
        description=(
            "READ-only append-only audit trail of a nonconformity by "
            "UUID (record_id): created/updated events with field diffs "
            "and actor identity, newest first."
        ),
        annotations=_annotations("get_nonconformity_history", "Get nonconformity history"),
        meta=meta,
    )
    async def get_nonconformity_history(record_id: str) -> CallToolResult:
        return await bridge.tool_get_nonconformity_history(record_id=record_id)

    @mcp.tool(
        name="get_nonconformity_indicators",
        title="Get nonconformity indicators",
        description=(
            "READ-only days-without-NC indicators: current streak and "
            "record computed from official occurrence dates, last NC "
            "date, reference anchor and degradation flags. EVA never "
            "recalculates — values come from the Engineering store."
        ),
        annotations=_annotations("get_nonconformity_indicators", "Get nonconformity indicators"),
        meta=meta,
    )
    async def get_nonconformity_indicators() -> CallToolResult:
        return await bridge.tool_get_nonconformity_indicators()

    @mcp.tool(
        name="get_nonconformity_tags",
        title="Get nonconformity tags",
        description=(
            "READ-only shared problem-tag catalog with usage counts. "
            "Use these labels when filtering search_nonconformities by "
            "problem_tag or when describing classifications."
        ),
        annotations=_annotations("get_nonconformity_tags", "Get nonconformity tags"),
        meta=meta,
    )
    async def get_nonconformity_tags() -> CallToolResult:
        return await bridge.tool_get_nonconformity_tags()

    @mcp.tool(
        name="get_nonconformity_context",
        title="Get nonconformity context",
        description=(
            "READ-only functional context of a nonconformity by UUID "
            "(record_id): the official OV fact from TOTVS via api-delpi "
            "facts plus product structure/BOM for linked products. Each "
            "source reports its own availability — unavailable or "
            "not_linked never means fabricated data."
        ),
        annotations=_annotations("get_nonconformity_context", "Get nonconformity context"),
        meta=meta,
    )
    async def get_nonconformity_context(record_id: str) -> CallToolResult:
        return await bridge.tool_get_nonconformity_context(record_id=record_id)

    @mcp.tool(
        name="prepare_nonconformity_mutation",
        title="Prepare nonconformity mutation",
        description=(
            "PREPARE-only: analyzes a candidate nonconformity mutation "
            "without any write. operation=create|update; payload = the "
            "candidate fields; record_id required for update. Returns "
            "normalized payload, validation errors and the projected "
            "history diff. Applying always requires human confirmation "
            "through the authorized Portal/API path — EVA has no ACT."
        ),
        annotations=_annotations(
            "prepare_nonconformity_mutation", "Prepare nonconformity mutation"
        ),
        meta=meta,
    )
    async def prepare_nonconformity_mutation(
        operation: str,
        payload: dict,
        record_id: str | None = None,
    ) -> CallToolResult:
        return await bridge.tool_prepare_nonconformity_mutation(
            operation=operation,
            payload=payload,
            record_id=record_id,
        )

    return mcp
