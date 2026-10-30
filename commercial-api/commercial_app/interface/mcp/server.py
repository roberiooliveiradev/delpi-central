"""MCPServer — CAIO governed MCP surface (six semantic tools)."""

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

from commercial_app.interface.mcp.branding import CAIO_MCP_INSTRUCTIONS
from commercial_app.interface.mcp.constants import (
    DESTRUCTIVE_ACT_TOOLS,
    TOOL_CLASS,
)
from commercial_app.interface.mcp.oauth_contract import (
    CAIO_MCP_SECURITY_SCHEMES,
)
from commercial_app.interface.mcp.resource_metadata import (
    public_host_allowed_for_mcp,
)
from commercial_app.interface.mcp import semantic_bridge

logger = logging.getLogger(__name__)


class _CaioWireTool(MCPTool):
    """Tool wire model preserving the top-level ``securitySchemes`` extension."""

    model_config = ConfigDict(extra="allow")


class CommercialMCPServer(MCPServer):
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
            schemes = meta.get("securitySchemes") or CAIO_MCP_SECURITY_SCHEMES
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
            listed.append(_CaioWireTool.model_validate(payload))
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


def caio_mcp_transport_security() -> TransportSecuritySettings:
    hosts, origins = public_host_allowed_for_mcp()
    return mcp_transport_security_settings(
        allowed_hosts=hosts,
        allowed_origins=origins,
    )


def create_mcp_server() -> MCPServer:
    mcp = CommercialMCPServer(
        name="commercial",
        instructions=CAIO_MCP_INSTRUCTIONS,
    )
    meta = security_schemes_meta(CAIO_MCP_SECURITY_SCHEMES)

    @mcp.tool(
        name="get_context",
        title="Get context",
        description=(
            "CAIO semantic discovery — working context, entities, "
            "actions, fields, risk model, commercial capabilities and "
            "honest availability states. Call FIRST, before any other "
            "tool. Context is never authorization: backend permissions "
            "are re-checked on every call."
        ),
        annotations=_annotations("get_context", "Get context"),
        meta=meta,
    )
    def get_context(
        topic: str | None = None,
        entity: str | None = None,
        selected_ref: str | None = None,
    ) -> CallToolResult:
        return semantic_bridge.tool_get_context(
            topic=topic, entity=entity, selected_ref=selected_ref
        )

    @mcp.tool(
        name="read",
        title="Read",
        description=(
            "Semantic official-data reads — entity + action only "
            "(typed allowlist; no URLs/methods/handler names). The "
            "full action catalog (49 reads: portfolios, customers, "
            "orders, proposals, worklist, rooms, production, profile…) "
            "is discoverable via get_context. filters/pagination are "
            "per-action allowlisted fields — pagination is only "
            "accepted on capabilities that declare it; unsupported "
            "params fail with 400 validation, never silently. "
            "portfolio_id/seller_id select portfolios (manage/team "
            "scope); members see only their own portfolio scope."
        ),
        annotations=_annotations("read", "Read"),
        meta=meta,
    )
    def read(
        entity: str,
        action: str,
        ref: str | None = None,
        filters: dict | None = None,
        pagination: dict | None = None,
        projection: list | None = None,
    ) -> CallToolResult:
        return semantic_bridge.tool_read(
            entity=entity,
            action=action,
            ref=ref,
            filters=filters,
            pagination=pagination,
            projection=projection,
        )

    @mcp.tool(
        name="analyze",
        title="Analyze",
        description=(
            "Grounded Commercial analyses over official facts — every "
            "value labeled OBSERVED|CALCULATED|INFERRED|UNKNOWN with "
            "provenance. 21 analysis types (portfolio, rol, closing "
            "rate, sales order OTD, billing, dashboard, new business, "
            "weg, opportunities) — full catalog via get_context. "
            "Series analyses require granularity per the owner "
            "contract. CAIO never recalculates indicators; unknown "
            "types answer not_implemented."
        ),
        annotations=_annotations("analyze", "Analyze"),
        meta=meta,
    )
    def analyze(
        analysis_type: str,
        subject_refs: list | None = None,
        question: str | None = None,
        parameters: dict | None = None,
    ) -> CallToolResult:
        return semantic_bridge.tool_analyze(
            analysis_type=analysis_type,
            subject_refs=subject_refs,
            question=question,
            parameters=parameters,
        )

    @mcp.tool(
        name="knowledge",
        title="Knowledge",
        description=(
            "Versioned owner-authorized Commercial guidance — "
            "topics (caio.usage, commercial.*), methods "
            "(method.<id>: curated external methodologies) and "
            "playbooks (playbook.<id>: reusable analysis scripts). "
            "Empty topic with query selects the relevant entries "
            "for the question. Guidance, not operational truth: "
            "unindexed topics answer not_found/not_implemented."
        ),
        annotations=_annotations("knowledge", "Knowledge"),
        meta=meta,
    )
    def knowledge(
        topic: str | None = None,
        task: str | None = None,
        query: str | None = None,
    ) -> CallToolResult:
        return semantic_bridge.tool_knowledge(
            topic=topic, task=task, query=query
        )

    @mcp.tool(
        name="execute",
        title="Execute",
        description=(
            "Governed mutations — entity + action only. Authorized "
            "creates/updates execute directly through the official "
            "owner use cases (no repetitive confirmations); backend "
            "authorization and consent policies stay sovereign. "
            "Unactivated contracts answer not_implemented honestly — "
            "never simulated."
        ),
        annotations=_annotations("execute", "Execute"),
        meta=meta,
    )
    def execute(
        entity: str,
        action: str,
        target_ref: str | None = None,
        payload: dict | None = None,
        changes: dict | None = None,
        idempotency_key: str | None = None,
        expected_version: str | None = None,
        proposal_ref: str | None = None,
        phase: str | None = None,
    ) -> CallToolResult:
        return semantic_bridge.tool_execute(
            entity=entity,
            action=action,
            target_ref=target_ref,
            payload=payload,
            changes=changes,
            idempotency_key=idempotency_key,
            expected_version=expected_version,
            proposal_ref=proposal_ref,
            phase=phase,
        )

    @mcp.tool(
        name="delete",
        title="Delete",
        description=(
            "Governed DESTRUCTIVE deletes — never direct: "
            "phase=prepare seals a server-side proposal (actor-bound, "
            "target-bound, expiring, single-use); phase=commit "
            "executes only with the exact proposal_ref. A client-side "
            "'confirmed=true' is never proof."
        ),
        annotations=_annotations("delete", "Delete"),
        meta=meta,
    )
    def delete(
        entity: str,
        target_ref: str,
        action: str | None = None,
        proposal_ref: str | None = None,
        phase: str | None = None,
    ) -> CallToolResult:
        return semantic_bridge.tool_delete(
            entity=entity,
            action=action,
            target_ref=target_ref,
            proposal_ref=proposal_ref,
            phase=phase,
        )

    return mcp
