"""FastMCP server — TÉO capability-driven MCP (PREPARE → commit_proposal)."""

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
        description=(
            "Discovery catalog: entities, workflows, analysis, registration_guide, "
            "diagram_catalog, capability_surface. Use before writes."
        ),
        annotations=_annotations("get_catalog", "Get catalog"),
        meta=meta,
    )
    def get_catalog() -> CallToolResult:
        return bridge.tool_get_catalog()

    @mcp.tool(
        name="get_methodology_guide",
        title="Get methodology guide",
        description=(
            "READ-only TÉO process-methodology playbooks. "
            "Optional method (macroprocess, key_process, end_to_end, sipoc, lean, "
            "ishikawa, five_whys, ctp, tdr, kpi, swot, as_is, to_be) and/or task "
            "(discover, map, diagnose, redesign, measure, prioritize, interview). "
            "Guidance is not authorization, not domain truth, and does not write."
        ),
        annotations=_annotations("get_methodology_guide", "Get methodology guide"),
        meta=meta,
    )
    def get_methodology_guide(
        method: str | None = None,
        task: str | None = None,
    ) -> CallToolResult:
        return bridge.tool_get_methodology_guide(method=method, task=task)

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

    # --- PREPARE (generic entity + specialized workflows) -----------------

    @mcp.tool(
        name="prepare_record_change",
        title="Prepare record change",
        description=(
            "PREPARE only (no write): conventional ENTITY CRUD "
            "(create|update|delete|duplicate) for catalog entities "
            "(e.g. process_document). Returns opaque proposal_handle. "
            "Do NOT use for business workflows (revision activation, "
            "evidence, meeting minutes, packages, cost adjustment) — "
            "use the specialized prepare_* tools instead. "
            "Then call commit_proposal(proposal_handle)."
        ),
        annotations=_annotations("prepare_record_change", "Prepare record change"),
        meta=meta,
    )
    def prepare_record_change(
        entity: str,
        operation: str,
        record_id: str | None = None,
        changes: dict | None = None,
    ) -> CallToolResult:
        return bridge.tool_prepare_record_change(
            entity=entity,
            operation=operation,
            record_id=record_id,
            changes=changes,
        )

    @mcp.tool(
        name="prepare_activate_revision",
        title="Prepare activate revision",
        description=(
            "PREPARE WORKFLOW: activate revision (overwrites current). "
            "Not a generic entity update. Then commit_proposal."
        ),
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
        description=(
            "PREPARE WORKFLOW: materialised dashboard cache recalculate. "
            "Then commit_proposal."
        ),
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
        description=(
            "PREPARE WORKFLOW: send|finalize|cancel meeting minute. "
            "Then commit_proposal."
        ),
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
            "PREPARE WORKFLOW: validate package + AuthZ + proposal_handle (NO WRITE). "
            "Incomplete packages: ready=false / act_allowed=false. "
            "Commit only via commit_proposal(proposal_handle)."
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
            "PREPARE WORKFLOW: create_link|update_description|delete evidence. "
            "Not generic file CRUD. delete needs confirm_delete in prepare. "
            "Then commit_proposal."
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
        description=(
            "PREPARE WORKFLOW: shared-resource cost adjustment with domain rules. "
            "Then commit_proposal."
        ),
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
            "PREPARE WORKFLOW: write actions for atas (resend/...). "
            "resend requires data.confirm_resend=true. "
            "READ → meeting_minute_read; transcript → generate_from_transcript. "
            "Then commit_proposal."
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

    # --- COMMON COMMIT (proposal_handle only; not a generic executor) -----

    @mcp.tool(
        name="commit_proposal",
        title="Commit proposal",
        description=(
            "ACT/COMMIT: execute the exact prepared change. "
            "Accepts only proposal_handle (and optional confirmation flags already "
            "bound in the proposal). Does NOT accept entity/operation/changes/"
            "tool_name. Revalidates AuthZ, user binding, fingerprint, then "
            "authoritative read-back. Use after any prepare_* tool."
        ),
        annotations=_annotations("commit_proposal", "Commit proposal"),
        meta=meta,
    )
    def commit_proposal(
        proposal_handle: str, confirmation: bool = True
    ) -> CallToolResult:
        return bridge.tool_commit_proposal(
            proposal_handle=proposal_handle, confirmation=confirmation
        )

    registered = {t.name for t in mcp._tool_manager.list_tools()}
    missing = set(MCP_TOOL_NAMES) - registered
    if missing:
        logger.error("teo_mcp_tools_missing=%s", sorted(missing))
    return mcp


__all__ = ["TransformometroFastMCP", "create_mcp_server"]
