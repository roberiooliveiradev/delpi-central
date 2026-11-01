"""MCPServer — EVA governed MCP surface (DISCOVERY/READ/PREPARE/ACT)."""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.mcpserver import Context, MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import CallToolResult, Tool as MCPTool, ToolAnnotations
from pydantic import ConfigDict

from delpi_mcp.tool_metadata import (
    DELPI_META_DEPRECATED,
    DELPI_META_TOOL_CLASS,
    security_schemes_meta,
    tool_annotations_payload,
)
from delpi_mcp.transport import mcp_transport_security_settings

from engineering_app.interface.mcp.branding import EVA_MCP_INSTRUCTIONS
from engineering_app.interface.mcp.constants import (
    DESTRUCTIVE_ACT_TOOLS,
    EVA_LEGACY_TOOL_NAMES,
    TOOL_CLASS,
)
from engineering_app.interface.mcp.oauth_contract import (
    EVA_MCP_SECURITY_SCHEMES,
)
from engineering_app.interface.mcp.resource_metadata import (
    public_host_allowed_for_mcp,
)
from engineering_app.interface.mcp import semantic_bridge

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
            # Legacy tools stay registered during migration (plan 54 M6)
            # — deprecation is metadata, never a silent removal.
            if info.name in EVA_LEGACY_TOOL_NAMES:
                meta[DELPI_META_DEPRECATED] = True
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
        name="get_context",
        title="Get context",
        description=(
            "EVA semantic discovery — working context, entities, "
            "actions, schemas on demand, risk/phase model, act_enabled "
            "and honest availability states. Call FIRST, before any "
            "other tool. Context is never authorization: live Core "
            "AuthZ is re-checked on every call."
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
            "(typed allowlist; no URLs/methods/handler names). "
            "entities: engineering(home|overview), lmp(list|summary|"
            "detail|history_events|history_flow|goal_context|"
            "department_idd|nc_streak), product(structure), "
            "nonconformity(search|detail|history|indicators|tags|"
            "context|export). ref = primary identifier "
            "(sale_number|record_id|product_code); filters/pagination "
            "are per-action allowlisted fields."
        ),
        annotations=_annotations("read", "Read"),
        meta=meta,
    )
    async def read(
        entity: str,
        action: str,
        ref: str | None = None,
        filters: dict | None = None,
        pagination: dict | None = None,
        projection: list | None = None,
    ) -> CallToolResult:
        return await semantic_bridge.tool_read(
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
            "Grounded Engineering analyses over official facts — every "
            "value labeled OBSERVED|CALCULATED|INFERRED|UNKNOWN with "
            "verifiable method and provenance. Types: "
            "nonconformity.recurrence (group_by), lmp.performance, "
            "product.drawing_analysis (product_code[, visual_"
            "observations[], scope[]]). "
            "Unknown types answer not_implemented — never fabricated."
        ),
        annotations=_annotations("analyze", "Analyze"),
        meta=meta,
    )
    async def analyze(
        analysis_type: str,
        subject_refs: list | None = None,
        question: str | None = None,
        parameters: dict | None = None,
    ) -> CallToolResult:
        return await semantic_bridge.tool_analyze(
            analysis_type=analysis_type,
            subject_refs=subject_refs,
            question=question,
            parameters=parameters,
        )

    @mcp.tool(
        name="knowledge",
        title="Knowledge",
        description=(
            "Versioned owner-authorized Engineering guidance — "
            "nonconformity.guide (contract semantics), lmp.guide "
            "(domain concepts), eva.usage (operation). Guidance, not "
            "facts: unindexed topics answer not_implemented honestly."
        ),
        annotations=_annotations("knowledge", "Knowledge"),
        meta=meta,
    )
    def knowledge(
        topic: str,
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
            "Governed mutations. nonconformity.create|update run "
            "DIRECTLY when the request is unambiguous and authorized — "
            "idempotency_key for create, expected_version "
            "(optimistic locking) for update; phase=prepare validates "
            "with zero side effects. nonconformity.import is "
            "DESTRUCTIVE replace-all: phase=prepare dry-runs and seals "
            "a server-side proposal; phase=commit requires the exact "
            "proposal_ref + verifiable human confirmation — "
            "confirmed=true is never proof. Requires live Core AuthZ; "
            "risk-tiered flags: ENG_EVA_ACT_ENABLED (write) and "
            "ENG_EVA_ACT_IMPORT_ENABLED (replace-all commit)."
        ),
        annotations=_annotations("execute", "Execute"),
        meta=meta,
    )
    async def execute(
        entity: str,
        action: str,
        target_ref: str | None = None,
        payload: dict | None = None,
        changes: dict | None = None,
        idempotency_key: str | None = None,
        expected_version: str | None = None,
        proposal_ref: str | None = None,
        phase: str | None = None,
        ctx: Context | None = None,
    ) -> CallToolResult:
        return await semantic_bridge.tool_execute(
            entity=entity,
            action=action,
            target_ref=target_ref,
            payload=payload,
            changes=changes,
            idempotency_key=idempotency_key,
            expected_version=expected_version,
            proposal_ref=proposal_ref,
            phase=phase,
            ctx=ctx,
        )

    @mcp.tool(
        name="delete",
        title="Delete",
        description=(
            "Governed DESTRUCTIVE deletes — never direct. "
            "phase=prepare seals target + impact into a server-side "
            "proposal (actor-bound, expiring, single-use); phase=commit "
            "executes only with the exact proposal_ref after verifiable "
            "human confirmation via MCP elicitation (the human retypes "
            "the target id). Requires ENG_EVA_ACT_ENABLED + "
            "ENG_EVA_ACT_DELETE_ENABLED. Currently: "
            "nonconformity.delete."
        ),
        annotations=_annotations("delete", "Delete"),
        meta=meta,
    )
    async def delete(
        entity: str,
        target_ref: str,
        proposal_ref: str | None = None,
        phase: str | None = None,
        ctx: Context | None = None,
    ) -> CallToolResult:
        return await semantic_bridge.tool_delete(
            entity=entity,
            target_ref=target_ref,
            proposal_ref=proposal_ref,
            phase=phase,
            ctx=ctx,
        )

    return mcp
