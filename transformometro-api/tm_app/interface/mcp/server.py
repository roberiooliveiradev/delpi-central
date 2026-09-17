"""FastMCP server — TÉO FULL CRUD with governed PREPARE → ACT writes."""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import CallToolResult, Tool as MCPTool, ToolAnnotations

from tm_app.interface.mcp.branding import TEO_MCP_INSTRUCTIONS
from tm_app.interface.mcp.constants import (
    DESTRUCTIVE_ACT_TOOLS,
    MCP_TOOL_NAMES,
    TOOL_CLASS,
)
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
    read_only = kind in {"READ", "ANALYSIS"}
    # PREPARE is not read-only (plans a write) and not destructive by itself.
    destructive = tool_name in DESTRUCTIVE_ACT_TOOLS
    return ToolAnnotations(
        readOnlyHint=read_only,
        destructiveHint=destructive,
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

    # --- READ -------------------------------------------------------------

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
        name="list_evidence",
        title="List evidence",
        description="READ: list process/revision evidence metadata (no binary).",
        annotations=_annotations("list_evidence", "List evidence"),
        meta=meta,
    )
    def list_evidence(scope: str, parent_id: str) -> CallToolResult:
        return bridge.tool_list_evidence(scope=scope, parent_id=parent_id)

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
        name="meeting_minute_read",
        title="Meeting minute read",
        description=(
            "READ: pending_signatures|audit|versions|participants|signers. "
            "Writes use prepare/act_meeting_minute_manage."
        ),
        annotations=_annotations("meeting_minute_read", "Meeting minute read"),
        meta=meta,
    )
    def meeting_minute_read(
        action: str,
        minute_id: str | None = None,
        data: dict | None = None,
    ) -> CallToolResult:
        return bridge.tool_meeting_minute_read(
            action=action, minute_id=minute_id, data=data
        )

    @mcp.tool(
        name="generate_from_transcript",
        title="Generate from transcript",
        description=(
            "ANALYSIS: draft from transcript without persistence. "
            "Not an ACT write."
        ),
        annotations=_annotations(
            "generate_from_transcript", "Generate from transcript"
        ),
        meta=meta,
    )
    def generate_from_transcript(
        minute_id: str | None = None,
        data: dict | None = None,
    ) -> CallToolResult:
        return bridge.tool_generate_from_transcript(minute_id=minute_id, data=data)

    # --- PREPARE ----------------------------------------------------------

    @mcp.tool(
        name="prepare_create_record",
        title="Prepare create record",
        description=(
            "PREPARE: exact create change → proposal_handle. "
            "Then call act_create_record with that handle only."
        ),
        annotations=_annotations("prepare_create_record", "Prepare create record"),
        meta=meta,
    )
    def prepare_create_record(entity: str, data: dict | None = None) -> CallToolResult:
        return bridge.tool_prepare_create_record(entity=entity, data=data)

    @mcp.tool(
        name="prepare_update_record",
        title="Prepare update record",
        description=(
            "PREPARE: exact update → proposal_handle. "
            "May note confirm_vigencia_change for revision dates."
        ),
        annotations=_annotations("prepare_update_record", "Prepare update record"),
        meta=meta,
    )
    def prepare_update_record(
        entity: str, id: str, data: dict | None = None
    ) -> CallToolResult:
        return bridge.tool_prepare_update_record(entity=entity, id=id, data=data)

    @mcp.tool(
        name="prepare_delete_record",
        title="Prepare delete record",
        description="PREPARE: soft-delete proposal → proposal_handle.",
        annotations=_annotations("prepare_delete_record", "Prepare delete record"),
        meta=meta,
    )
    def prepare_delete_record(entity: str, id: str) -> CallToolResult:
        return bridge.tool_prepare_delete_record(entity=entity, id=id)

    @mcp.tool(
        name="prepare_duplicate_record",
        title="Prepare duplicate record",
        description="PREPARE: duplicate process/instance/revision → proposal_handle.",
        annotations=_annotations(
            "prepare_duplicate_record", "Prepare duplicate record"
        ),
        meta=meta,
    )
    def prepare_duplicate_record(
        entity: str, id: str, data: dict | None = None
    ) -> CallToolResult:
        return bridge.tool_prepare_duplicate_record(entity=entity, id=id, data=data)

    @mcp.tool(
        name="prepare_activate_revision",
        title="Prepare activate revision",
        description="PREPARE: activate revision proposal (overwrites current).",
        annotations=_annotations(
            "prepare_activate_revision", "Prepare activate revision"
        ),
        meta=meta,
    )
    def prepare_activate_revision(id: str) -> CallToolResult:
        return bridge.tool_prepare_activate_revision(id=id)

    @mcp.tool(
        name="prepare_recalculate_dashboard",
        title="Prepare recalculate dashboard",
        description="PREPARE: materialised dashboard cache recalculate proposal.",
        annotations=_annotations(
            "prepare_recalculate_dashboard", "Prepare recalculate dashboard"
        ),
        meta=meta,
    )
    def prepare_recalculate_dashboard(
        revisao_id: str | None = None,
        processo_id: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
    ) -> CallToolResult:
        return bridge.tool_prepare_recalculate_dashboard(
            revisao_id=revisao_id,
            processo_id=processo_id,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
        )

    @mcp.tool(
        name="prepare_meeting_minute_workflow",
        title="Prepare meeting minute workflow",
        description="PREPARE: send|finalize|cancel meeting minute → proposal_handle.",
        annotations=_annotations(
            "prepare_meeting_minute_workflow", "Prepare meeting minute workflow"
        ),
        meta=meta,
    )
    def prepare_meeting_minute_workflow(
        id: str, action: str, reason: str | None = None
    ) -> CallToolResult:
        return bridge.tool_prepare_meeting_minute_workflow(
            id=id, action=action, reason=reason
        )

    @mcp.tool(
        name="prepare_improvement_package",
        title="Prepare improvement package",
        description=(
            "PREPARE: validate package + AuthZ + governed proposal_handle. "
            "Incomplete packages return ready=false and act_allowed=false (NO WRITE). "
            "Commit only via act_commit_improvement_package(proposal_handle)."
        ),
        annotations=_annotations(
            "prepare_improvement_package", "Prepare improvement package"
        ),
        meta=meta,
    )
    def prepare_improvement_package(
        process: dict | None = None,
        instance: dict | None = None,
        baseline: dict | None = None,
        scenario: dict | None = None,
        activate_scenario: bool = False,
        recalculate: bool = False,
    ) -> CallToolResult:
        return bridge.tool_prepare_improvement_package(
            process=process,
            instance=instance,
            baseline=baseline,
            scenario=scenario,
            activate_scenario=activate_scenario,
            recalculate=recalculate,
        )

    @mcp.tool(
        name="prepare_manage_evidence",
        title="Prepare manage evidence",
        description=(
            "PREPARE: create_link|update_description|delete. "
            "delete requires confirm_delete=true in the prepared change."
        ),
        annotations=_annotations("prepare_manage_evidence", "Prepare manage evidence"),
        meta=meta,
    )
    def prepare_manage_evidence(
        scope: str,
        operation: str,
        parent_id: str,
        evidence_id: str | None = None,
        url_externa: str | None = None,
        descricao: str | None = None,
        confirm_delete: bool = False,
    ) -> CallToolResult:
        return bridge.tool_prepare_manage_evidence(
            scope=scope,
            operation=operation,
            parent_id=parent_id,
            evidence_id=evidence_id,
            url_externa=url_externa,
            descricao=descricao,
            confirm_delete=confirm_delete,
        )

    @mcp.tool(
        name="prepare_adjust_shared_resource_cost",
        title="Prepare adjust shared resource cost",
        description="PREPARE: shared-resource cost adjustment → proposal_handle.",
        annotations=_annotations(
            "prepare_adjust_shared_resource_cost",
            "Prepare adjust shared resource cost",
        ),
        meta=meta,
    )
    def prepare_adjust_shared_resource_cost(
        recurso_compartilhado_id: str,
        valor_mensal: float,
        vigente_desde: str,
        observacoes: str | None = None,
    ) -> CallToolResult:
        return bridge.tool_prepare_adjust_shared_resource_cost(
            recurso_compartilhado_id=recurso_compartilhado_id,
            valor_mensal=valor_mensal,
            vigente_desde=vigente_desde,
            observacoes=observacoes,
        )

    @mcp.tool(
        name="prepare_meeting_minute_manage",
        title="Prepare meeting minute manage",
        description=(
            "PREPARE: write actions for atas (resend/...). "
            "resend requires data.confirm_resend=true. "
            "READ actions → meeting_minute_read; transcript → generate_from_transcript."
        ),
        annotations=_annotations(
            "prepare_meeting_minute_manage", "Prepare meeting minute manage"
        ),
        meta=meta,
    )
    def prepare_meeting_minute_manage(
        action: str,
        minute_id: str | None = None,
        data: dict | None = None,
    ) -> CallToolResult:
        return bridge.tool_prepare_meeting_minute_manage(
            action=action, minute_id=minute_id, data=data
        )

    # --- ACT (proposal_handle only) ---------------------------------------

    def _act_desc(name: str) -> str:
        return (
            f"ACT: execute the exact prepared {name} change. "
            "Accepts only proposal_handle from the matching prepare_* tool. "
            "Revalidates AuthZ, fingerprint, and verifies authoritative read-back."
        )

    @mcp.tool(
        name="act_create_record",
        title="Act create record",
        description=_act_desc("create_record"),
        annotations=_annotations("act_create_record", "Act create record"),
        meta=meta,
    )
    def act_create_record(proposal_handle: str) -> CallToolResult:
        return bridge.tool_act_create_record(proposal_handle=proposal_handle)

    @mcp.tool(
        name="act_update_record",
        title="Act update record",
        description=_act_desc("update_record"),
        annotations=_annotations("act_update_record", "Act update record"),
        meta=meta,
    )
    def act_update_record(proposal_handle: str) -> CallToolResult:
        return bridge.tool_act_update_record(proposal_handle=proposal_handle)

    @mcp.tool(
        name="act_delete_record",
        title="Act delete record",
        description=_act_desc("delete_record"),
        annotations=_annotations("act_delete_record", "Act delete record"),
        meta=meta,
    )
    def act_delete_record(proposal_handle: str) -> CallToolResult:
        return bridge.tool_act_delete_record(proposal_handle=proposal_handle)

    @mcp.tool(
        name="act_duplicate_record",
        title="Act duplicate record",
        description=_act_desc("duplicate_record"),
        annotations=_annotations("act_duplicate_record", "Act duplicate record"),
        meta=meta,
    )
    def act_duplicate_record(proposal_handle: str) -> CallToolResult:
        return bridge.tool_act_duplicate_record(proposal_handle=proposal_handle)

    @mcp.tool(
        name="act_activate_revision",
        title="Act activate revision",
        description=_act_desc("activate_revision"),
        annotations=_annotations("act_activate_revision", "Act activate revision"),
        meta=meta,
    )
    def act_activate_revision(proposal_handle: str) -> CallToolResult:
        return bridge.tool_act_activate_revision(proposal_handle=proposal_handle)

    @mcp.tool(
        name="act_recalculate_dashboard",
        title="Act recalculate dashboard",
        description=_act_desc("recalculate_dashboard"),
        annotations=_annotations(
            "act_recalculate_dashboard", "Act recalculate dashboard"
        ),
        meta=meta,
    )
    def act_recalculate_dashboard(proposal_handle: str) -> CallToolResult:
        return bridge.tool_act_recalculate_dashboard(proposal_handle=proposal_handle)

    @mcp.tool(
        name="act_meeting_minute_workflow",
        title="Act meeting minute workflow",
        description=_act_desc("meeting_minute_workflow"),
        annotations=_annotations(
            "act_meeting_minute_workflow", "Act meeting minute workflow"
        ),
        meta=meta,
    )
    def act_meeting_minute_workflow(proposal_handle: str) -> CallToolResult:
        return bridge.tool_act_meeting_minute_workflow(proposal_handle=proposal_handle)

    @mcp.tool(
        name="act_commit_improvement_package",
        title="Act commit improvement package",
        description=(
            "ACT: commit the exact prepared improvement package. "
            "proposal_handle only — does not accept a different package payload."
        ),
        annotations=_annotations(
            "act_commit_improvement_package", "Act commit improvement package"
        ),
        meta=meta,
    )
    def act_commit_improvement_package(proposal_handle: str) -> CallToolResult:
        return bridge.tool_act_commit_improvement_package(
            proposal_handle=proposal_handle
        )

    @mcp.tool(
        name="act_manage_evidence",
        title="Act manage evidence",
        description=_act_desc("manage_evidence"),
        annotations=_annotations("act_manage_evidence", "Act manage evidence"),
        meta=meta,
    )
    def act_manage_evidence(proposal_handle: str) -> CallToolResult:
        return bridge.tool_act_manage_evidence(proposal_handle=proposal_handle)

    @mcp.tool(
        name="act_adjust_shared_resource_cost",
        title="Act adjust shared resource cost",
        description=_act_desc("adjust_shared_resource_cost"),
        annotations=_annotations(
            "act_adjust_shared_resource_cost", "Act adjust shared resource cost"
        ),
        meta=meta,
    )
    def act_adjust_shared_resource_cost(proposal_handle: str) -> CallToolResult:
        return bridge.tool_act_adjust_shared_resource_cost(
            proposal_handle=proposal_handle
        )

    @mcp.tool(
        name="act_meeting_minute_manage",
        title="Act meeting minute manage",
        description=_act_desc("meeting_minute_manage"),
        annotations=_annotations(
            "act_meeting_minute_manage", "Act meeting minute manage"
        ),
        meta=meta,
    )
    def act_meeting_minute_manage(proposal_handle: str) -> CallToolResult:
        return bridge.tool_act_meeting_minute_manage(proposal_handle=proposal_handle)

    registered = {t.name for t in mcp._tool_manager.list_tools()}
    missing = set(MCP_TOOL_NAMES) - registered
    if missing:
        logger.error("teo_mcp_tools_missing=%s", sorted(missing))
    return mcp


__all__ = ["TransformometroFastMCP", "create_mcp_server"]
