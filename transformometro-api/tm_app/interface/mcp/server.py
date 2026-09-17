"""FastMCP server — TÉO FULL CRUD tools over Transformômetro façade."""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import CallToolResult, Tool as MCPTool, ToolAnnotations

from tm_app.interface.mcp.branding import TEO_MCP_INSTRUCTIONS
from tm_app.interface.mcp.constants import MCP_TOOL_NAMES, TOOL_CLASS
from tm_app.interface.mcp.oauth_contract import TEO_MCP_SECURITY_SCHEMES
from tm_app.interface.mcp.resource_metadata import public_host_allowed_for_mcp
from tm_app.interface.mcp import tool_bridge as bridge

logger = logging.getLogger(__name__)


class TransformometroFastMCP(FastMCP):
    """Expose OAuth securitySchemes on every tool for OpenAI Plugin discovery."""

    async def list_tools(self) -> list[MCPTool]:
        tools = self._tool_manager.list_tools()
        listed: list[MCPTool] = []
        for info in tools:
            meta = dict(info.meta or {})
            schemes = meta.get("securitySchemes") or TEO_MCP_SECURITY_SCHEMES
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
            listed.append(MCPTool.model_validate(payload))
        return listed


def _annotations(tool_name: str, title: str) -> ToolAnnotations:
    kind = TOOL_CLASS.get(tool_name, "ACT")
    read_only = kind == "READ"
    return ToolAnnotations(
        readOnlyHint=read_only,
        destructiveHint=tool_name in {"delete_record", "manage_evidence"},
        openWorldHint=False,
        title=title,
    )


def create_mcp_server() -> FastMCP:
    hosts, origins = public_host_allowed_for_mcp()
    mcp = TransformometroFastMCP(
        name="transformometro",
        instructions=TEO_MCP_INSTRUCTIONS,
        streamable_http_path="/",
        stateless_http=True,
        json_response=True,
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=hosts,
            allowed_origins=origins,
        ),
    )
    meta = {"securitySchemes": TEO_MCP_SECURITY_SCHEMES}

    @mcp.tool(
        name="get_my_context",
        title="Get my context",
        description="Minimal personal context (name/role). Not authorization.",
        annotations=_annotations("get_my_context", "Get my context"),
        meta=meta,
    )
    def get_my_context() -> CallToolResult:
        return bridge.tool_get_my_context()

    @mcp.tool(
        name="get_catalog",
        title="Get catalog",
        description="Catalog options, registration_guide, diagram_catalog.",
        annotations=_annotations("get_catalog", "Get catalog"),
        meta=meta,
    )
    def get_catalog() -> CallToolResult:
        return bridge.tool_get_catalog()

    @mcp.tool(
        name="get_process_context",
        title="Get process context",
        description="Aggregated read-only process intelligence context.",
        annotations=_annotations("get_process_context", "Get process context"),
        meta=meta,
    )
    def get_process_context(
        process_id: str,
        instance_id: str | None = None,
        revision_id: str | None = None,
    ) -> CallToolResult:
        return bridge.tool_get_process_context(
            process_id=process_id,
            instance_id=instance_id,
            revision_id=revision_id,
        )

    @mcp.tool(
        name="analyze",
        title="Analyze dashboard",
        description="Dashboard KPIs. view=meta|summary|processes|instances|rows.",
        annotations=_annotations("analyze", "Analyze dashboard"),
        meta=meta,
    )
    def analyze(
        view: str,
        filial_id: str | None = None,
        setor_id: str | None = None,
        processo_id: str | None = None,
        revisao_id: str | None = None,
        familia_processo: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
        limit: int | None = None,
    ) -> CallToolResult:
        return bridge.tool_analyze(
            view=view,
            filial_id=filial_id,
            setor_id=setor_id,
            processo_id=processo_id,
            revisao_id=revisao_id,
            familia_processo=familia_processo,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
            limit=limit,
        )

    @mcp.tool(
        name="search_records",
        title="Search records",
        description="Search/list Transformômetro records by entity slug.",
        annotations=_annotations("search_records", "Search records"),
        meta=meta,
    )
    def search_records(
        entity: str,
        parent_id: str | None = None,
        instance_id: str | None = None,
        filial_id: str | None = None,
        setor_id: str | None = None,
        status: str | None = None,
        familia_processo: str | None = None,
        q: str | None = None,
        unit_code: str | None = None,
    ) -> CallToolResult:
        return bridge.tool_search_records(
            entity=entity,
            parent_id=parent_id,
            instance_id=instance_id,
            filial_id=filial_id,
            setor_id=setor_id,
            status=status,
            familia_processo=familia_processo,
            q=q,
            unit_code=unit_code,
        )

    @mcp.tool(
        name="get_record",
        title="Get record",
        description="Get one record by entity and id.",
        annotations=_annotations("get_record", "Get record"),
        meta=meta,
    )
    def get_record(entity: str, id: str) -> CallToolResult:
        return bridge.tool_get_record(entity=entity, id=id)

    @mcp.tool(
        name="create_record",
        title="Create record",
        description=(
            "ACT: create entity. Nested fields under data. "
            "Call get_catalog registration_guide first."
        ),
        annotations=_annotations("create_record", "Create record"),
        meta=meta,
    )
    def create_record(entity: str, data: dict | None = None) -> CallToolResult:
        return bridge.tool_create_record(entity=entity, data=data)

    @mcp.tool(
        name="update_record",
        title="Update record",
        description=(
            "ACT: update entity. May require confirm_vigencia_change for revision dates."
        ),
        annotations=_annotations("update_record", "Update record"),
        meta=meta,
    )
    def update_record(entity: str, id: str, data: dict | None = None) -> CallToolResult:
        return bridge.tool_update_record(entity=entity, id=id, data=data)

    @mcp.tool(
        name="delete_record",
        title="Delete record",
        description="ACT: soft-delete entity record.",
        annotations=_annotations("delete_record", "Delete record"),
        meta=meta,
    )
    def delete_record(entity: str, id: str) -> CallToolResult:
        return bridge.tool_delete_record(entity=entity, id=id)

    @mcp.tool(
        name="duplicate_record",
        title="Duplicate record",
        description="ACT: duplicate process, instance, or revision.",
        annotations=_annotations("duplicate_record", "Duplicate record"),
        meta=meta,
    )
    def duplicate_record(
        entity: str, id: str, data: dict | None = None
    ) -> CallToolResult:
        return bridge.tool_duplicate_record(entity=entity, id=id, data=data)

    @mcp.tool(
        name="activate_revision",
        title="Activate revision",
        description="ACT: activate revision as operational current version.",
        annotations=_annotations("activate_revision", "Activate revision"),
        meta=meta,
    )
    def activate_revision(id: str) -> CallToolResult:
        return bridge.tool_activate_revision(id=id)

    @mcp.tool(
        name="recalculate_dashboard",
        title="Recalculate dashboard",
        description="ACT: recalculate materialised dashboard cache.",
        annotations=_annotations("recalculate_dashboard", "Recalculate dashboard"),
        meta=meta,
    )
    def recalculate_dashboard(
        revisao_id: str | None = None,
        processo_id: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
    ) -> CallToolResult:
        return bridge.tool_recalculate_dashboard(
            revisao_id=revisao_id,
            processo_id=processo_id,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
        )

    @mcp.tool(
        name="meeting_minute_workflow",
        title="Meeting minute workflow",
        description="ACT: send|finalize|cancel meeting minute.",
        annotations=_annotations("meeting_minute_workflow", "Meeting minute workflow"),
        meta=meta,
    )
    def meeting_minute_workflow(
        id: str, action: str, reason: str | None = None
    ) -> CallToolResult:
        return bridge.tool_meeting_minute_workflow(id=id, action=action, reason=reason)

    @mcp.tool(
        name="validate_improvement_package",
        title="Validate improvement package",
        description="PREPARE: validate package without writing. Returns ready/missing.",
        annotations=_annotations(
            "validate_improvement_package", "Validate improvement package"
        ),
        meta=meta,
    )
    def validate_improvement_package(
        process: dict | None = None,
        instance: dict | None = None,
        baseline: dict | None = None,
        scenario: dict | None = None,
    ) -> CallToolResult:
        return bridge.tool_validate_improvement_package(
            process=process,
            instance=instance,
            baseline=baseline,
            scenario=scenario,
        )

    @mcp.tool(
        name="commit_improvement_package",
        title="Commit improvement package",
        description=(
            "ACT: persist improvement package after user confirmation. "
            "Prefer validate_improvement_package first."
        ),
        annotations=_annotations(
            "commit_improvement_package", "Commit improvement package"
        ),
        meta=meta,
    )
    def commit_improvement_package(
        process: dict | None = None,
        instance: dict | None = None,
        baseline: dict | None = None,
        scenario: dict | None = None,
        dry_run: bool = False,
        activate_scenario: bool = False,
        recalculate: bool = False,
    ) -> CallToolResult:
        return bridge.tool_commit_improvement_package(
            process=process,
            instance=instance,
            baseline=baseline,
            scenario=scenario,
            dry_run=dry_run,
            activate_scenario=activate_scenario,
            recalculate=recalculate,
        )

    @mcp.tool(
        name="list_evidence",
        title="List evidence",
        description="READ: list process/revision evidence metadata (no binary).",
        annotations=_annotations("list_evidence", "List evidence"),
        meta=meta,
    )
    def list_evidence(scope: str, parent_id: str) -> CallToolResult:
        return bridge.tool_list_evidence(scope=scope, parent_id=parent_id)

    @mcp.tool(
        name="manage_evidence",
        title="Manage evidence",
        description=(
            "ACT: create_link|update_description|delete. "
            "delete requires confirm_delete=true."
        ),
        annotations=_annotations("manage_evidence", "Manage evidence"),
        meta=meta,
    )
    def manage_evidence(
        scope: str,
        operation: str,
        parent_id: str,
        evidence_id: str | None = None,
        url_externa: str | None = None,
        descricao: str | None = None,
        confirm_delete: bool = False,
    ) -> CallToolResult:
        return bridge.tool_manage_evidence(
            scope=scope,
            operation=operation,
            parent_id=parent_id,
            evidence_id=evidence_id,
            url_externa=url_externa,
            descricao=descricao,
            confirm_delete=confirm_delete,
        )

    @mcp.tool(
        name="get_process_timeline",
        title="Get process timeline",
        description="READ: process audit timeline.",
        annotations=_annotations("get_process_timeline", "Get process timeline"),
        meta=meta,
    )
    def get_process_timeline(
        processo_id: str, page: int = 1, page_size: int = 100
    ) -> CallToolResult:
        return bridge.tool_get_process_timeline(
            processo_id=processo_id, page=page, page_size=page_size
        )

    @mcp.tool(
        name="adjust_shared_resource_cost",
        title="Adjust shared resource cost",
        description="ACT: register shared-resource cost adjustment.",
        annotations=_annotations(
            "adjust_shared_resource_cost", "Adjust shared resource cost"
        ),
        meta=meta,
    )
    def adjust_shared_resource_cost(
        recurso_compartilhado_id: str,
        valor_mensal: float,
        vigente_desde: str,
        observacoes: str | None = None,
    ) -> CallToolResult:
        return bridge.tool_adjust_shared_resource_cost(
            recurso_compartilhado_id=recurso_compartilhado_id,
            valor_mensal=valor_mensal,
            vigente_desde=vigente_desde,
            observacoes=observacoes,
        )

    @mcp.tool(
        name="meeting_minute_manage",
        title="Meeting minute manage",
        description=(
            "ACT/READ extras for atas (pending/audit/versions/resend/...). "
            "resend requires data.confirm_resend=true. "
            "Does not replace meeting_minute_workflow send/finalize/cancel."
        ),
        annotations=_annotations("meeting_minute_manage", "Meeting minute manage"),
        meta=meta,
    )
    def meeting_minute_manage(
        action: str,
        minute_id: str | None = None,
        data: dict | None = None,
    ) -> CallToolResult:
        return bridge.tool_meeting_minute_manage(
            action=action, minute_id=minute_id, data=data
        )

    registered = {t.name for t in mcp._tool_manager.list_tools()}
    missing = set(MCP_TOOL_NAMES) - registered
    if missing:
        logger.error("teo_mcp_tools_missing=%s", sorted(missing))
    return mcp


__all__ = ["TransformometroFastMCP", "create_mcp_server"]
