"""MCPServer — TÉO Semantic V3 MCP (six semantic tools, issue #124)."""

from __future__ import annotations

import logging
from typing import Annotated, Any, Literal

from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from delpi_mcp.tool_metadata import (
    DELPI_META_TOOL_CLASS,
    security_schemes_meta,
    tool_annotations_payload,
)
from delpi_mcp.transport import mcp_transport_security_settings
from mcp.types import CallToolResult, Tool as MCPTool, ToolAnnotations
from pydantic import ConfigDict, Field

from tm_app.application.gpt_actions.entities import (
    GptAnalysisView,
    GptEntity,
)
from tm_app.interface.mcp.branding import TEO_MCP_INSTRUCTIONS
from tm_app.interface.mcp.constants import (
    DESTRUCTIVE_ACT_TOOLS,
    MCP_TOOL_NAMES,
    TOOL_CLASS,
)
from tm_app.interface.mcp.oauth_contract import TEO_MCP_SECURITY_SCHEMES
from tm_app.interface.mcp.resource_metadata import public_host_allowed_for_mcp
from tm_app.interface.mcp import tool_bridge_v3 as bridge_v3

logger = logging.getLogger(__name__)

# Canonical owner value domains projected as Literal so the MCP
# inputSchema declares the valid values (enum) — the same authority
# the GPT Actions OpenAPI builder already uses; handlers still
# receive plain strings at runtime.
_EntityParam = Literal[tuple(e.value for e in GptEntity)]
_AnalysisViewParam = Literal[
    tuple(v.value for v in GptAnalysisView)
    + ("meeting_minute_transcript",)
]


class _TeoWireTool(MCPTool):
    """Tool wire model that preserves the top-level ``securitySchemes`` extension.

    mcp-types 2.x ``Tool`` ignores unknown fields at validation; TÉO's
    provider contract promotes ``_meta.securitySchemes`` to the tool top
    level, so the extra field must survive ``model_validate``/``model_dump``.
    """

    model_config = ConfigDict(extra="allow")


class TransformometroMCPServer(MCPServer):
    """Expose OAuth securitySchemes on every tool for OpenAI Plugin discovery."""

    async def list_tools(self) -> list[MCPTool]:
        tools = self._tool_manager.list_tools()
        listed: list[MCPTool] = []
        for info in tools:
            meta = dict(info.meta or {})
            # Owner-typed operation class — typed catalog metadata the
            # consumer may project; never a permission grant. Default
            # ACT is the fail-closed class for unregistered names.
            meta[DELPI_META_TOOL_CLASS] = TOOL_CLASS.get(info.name, "ACT")
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
            listed.append(_TeoWireTool.model_validate(payload))
        return listed


def _annotations(tool_name: str, title: str) -> ToolAnnotations:
    kind = TOOL_CLASS.get(tool_name, "ACT")
    read_only = kind in {"DISCOVERY", "READ", "ANALYSIS"}
    # PREPARE is not read-only (plans a write) and not destructive by itself.
    destructive = tool_name in DESTRUCTIVE_ACT_TOOLS
    return ToolAnnotations.model_validate(
        tool_annotations_payload(
            title,
            read_only=read_only,
            destructive=destructive,
        )
    )


def teo_mcp_transport_security() -> TransportSecuritySettings:
    hosts, origins = public_host_allowed_for_mcp()
    return mcp_transport_security_settings(
        allowed_hosts=hosts,
        allowed_origins=origins,
    )


def create_mcp_server() -> MCPServer:
    mcp = TransformometroMCPServer(
        name="transformometro",
        instructions=TEO_MCP_INSTRUCTIONS,
    )
    meta = security_schemes_meta(TEO_MCP_SECURITY_SCHEMES)

    @mcp.tool(
        name="analyze",
        title="Analyze dashboard",
        description=(
            "Analysis views. Snapshot views: meta|summary|processes|instances|"
            "rows (filial_id/setor_id/competencia filters). Live dashboard: "
            "dashboard_summary_live|dashboard_process_ranking|dashboard_alerts|"
            "dashboard_evolution|dashboard_by_family|dashboard_due_dates|"
            "dashboard_strategic_indicators|processes_calculated. "
            "Process-scoped (processo_id): process_revision_comparison|"
            "decomposition_link_validation|decomposition_draft_suggestion|"
            "diagram_validation|diagram_bpmn_xml. Revision-scoped "
            "(revisao_id): revision_allocation_diagnostic|"
            "revision_diagram_merged|revision_decomposition_merged. "
            "impact_effort_matrix accepts processo_id|instancia_id|revisao_id "
            "(competencia/horizonte_meses optional). Filters may ride flat "
            "args or the params object (Semantic V3). "
            "view=meeting_minute_transcript: non-persisting transcript "
            "analysis (params.minute_id + params.data). READ-only — never "
            "persists."
        ),
        annotations=_annotations("analyze", "Analyze dashboard"),
        meta=meta,
    )
    def analyze(
        view: Annotated[
            _AnalysisViewParam,
            Field(description="Canonical analysis view."),
        ],
        params: Annotated[
            dict | None,
            Field(description="View-scoped parameters object."),
        ] = None,
        filial_id: Annotated[
            str | None, Field(description="Branch (filial) id filter.")
        ] = None,
        setor_id: Annotated[
            str | None, Field(description="Department (setor) id filter.")
        ] = None,
        processo_id: Annotated[
            str | None, Field(description="Process id (process-scoped views).")
        ] = None,
        revisao_id: Annotated[
            str | None, Field(description="Revision id (revision-scoped views).")
        ] = None,
        instancia_id: Annotated[
            str | None, Field(description="Instance id (instance-scoped views).")
        ] = None,
        familia_processo: Annotated[
            str | None, Field(description="Process family name filter.")
        ] = None,
        competencia: Annotated[
            str | None, Field(description="Competency period filter.")
        ] = None,
        competencia_inicio: Annotated[
            str | None, Field(description="Competency range start.")
        ] = None,
        competencia_fim: Annotated[
            str | None, Field(description="Competency range end.")
        ] = None,
        horizonte_meses: Annotated[
            int | None, Field(description="Month horizon for forecast views.")
        ] = None,
        limit: Annotated[
            int | None, Field(description="Result row cap for ranked views.")
        ] = None,
    ) -> CallToolResult:
        merged = {
            k: v
            for k, v in {
                "filial_id": filial_id,
                "setor_id": setor_id,
                "processo_id": processo_id,
                "revisao_id": revisao_id,
                "instancia_id": instancia_id,
                "familia_processo": familia_processo,
                "competencia": competencia,
                "competencia_inicio": competencia_inicio,
                "competencia_fim": competencia_fim,
                "horizonte_meses": horizonte_meses,
                "limit": limit,
            }.items()
            if v is not None
        }
        merged.update(params or {})
        return bridge_v3.tool_analyze(view=view, params=merged)

    # --- SEMANTIC V3 (issue #124 — final cutover) --------------------------
    # The ONLY public surface: six semantic tools over the governed
    # capabilities. The 22 V2 family names are tombstoned; their bridge
    # functions remain internal adapters. Capability/policy/AuthZ
    # resolution is unchanged.

    @mcp.tool(
        name="get_context",
        title="Get context",
        description=(
            "Semantic discovery — context is never authorization. "
            "section=overview (default): authenticated user + current "
            "workspace refs + discovery hint. section=self: personal "
            "context + signature profile. section=workspace: current "
            "process/instance/revision/area refs (navigation hint — "
            "authoritative facts still require read()). section=catalog: "
            "full capability catalog (entities, workflows, write schemas, "
            "execution policies, agent_directives); optional entity "
            "filters one entity contract."
        ),
        annotations=_annotations("get_context", "Get context"),
        meta=meta,
    )
    def get_context(
        section: Annotated[
            Literal["overview", "self", "workspace", "catalog"] | None,
            Field(description="Discovery section (default: overview)."),
        ] = None,
        entity: Annotated[
            str | None,
            Field(
                description=(
                    "Entity filter for section=catalog — projects one "
                    "entity contract instead of the full catalog."
                )
            ),
        ] = None,
    ) -> CallToolResult:
        return bridge_v3.tool_get_context(section=section, entity=entity)

    @mcp.tool(
        name="read",
        title="Read",
        description=(
            "Semantic read — never writes. entity + typed action + params "
            "object. Domain entities (process, instance, revision, "
            "measurement, investment, shared_resource, resource_cost, "
            "resource_link, meeting_minute, process_document, "
            "decomposition_tree, instance_decomposition_scope, "
            "revision_decomposition_overlay, process_diagram, "
            "instance_diagram_scope, revision_diagram_overlay, "
            "process_bpmn_document, impact_effort_matrix, branch, "
            "department): action=search|get (search uses filter/pagination "
            "params; get uses id). Specialized entities: process_context "
            "(get: processo_id + optional instancia_id/revisao_id — "
            "authoritative process intelligence), process_timeline (get: "
            "processo_id — needs an already-identified process, not "
            "discovery), solution (catalog|context), helpdesk "
            "(session|capabilities|tickets|ticket|attachment|catalog), "
            "meeting_minute (pending_signatures|audit|versions|"
            "participants|signers|generate_from_transcript), "
            "evidence (list), task (my_tasks|"
            "task|process_tasks), interaction_room (rooms|room|messages|"
            "attachments|room_links|room_participants|room_impact|"
            "resolve_room), diagnostic (get|by_revision)."
        ),
        annotations=_annotations("read", "Read"),
        meta=meta,
    )
    def read(
        entity: Annotated[
            str,
            Field(
                description=(
                    "Domain or specialized entity to read (see "
                    "description for the closed vocabulary)."
                )
            ),
        ],
        action: Annotated[
            str | None,
            Field(
                description=(
                    "Typed entity action — search|get for domain "
                    "entities; specialized entities declare their own "
                    "closed action set."
                )
            ),
        ] = None,
        params: Annotated[
            dict | None,
            Field(
                description=(
                    "Action-scoped parameters: id for get; "
                    "filters/pagination for search; action-specific "
                    "fields for specialized routes."
                )
            ),
        ] = None,
    ) -> CallToolResult:
        return bridge_v3.tool_read(
            entity=entity, action=action, params=params
        )

    @mcp.tool(
        name="knowledge",
        title="Knowledge",
        description=(
            "Versioned knowledge — guidance, never domain truth or AuthZ. "
            "source=methodology: TÉO process-methodology playbooks "
            "(params: method, task, guide_version v1|v2, intent, context "
            "facts). source=product_guide: Portal/Transformômetro usage "
            "guides (params: topic, section)."
        ),
        annotations=_annotations("knowledge", "Knowledge"),
        meta=meta,
    )
    def knowledge(
        source: Annotated[
            Literal["methodology", "product_guide"],
            Field(description="Knowledge family to project."),
        ],
        params: Annotated[
            dict | None,
            Field(
                description=(
                    "Source-scoped parameters (method/task/intent/ "
                    "context for methodology; topic/section for "
                    "product_guide)."
                )
            ),
        ] = None,
    ) -> CallToolResult:
        return bridge_v3.tool_knowledge(source=source, params=params)

    @mcp.tool(
        name="execute",
        title="Execute",
        description=(
            "Governed writes — PREPARE→policy gate→ACT→authoritative "
            "read-back in one call when the sealed execution_policy is "
            "auto_act (the user request is the intent). Target forms: "
            "capability=<orchestrator capability or canonical family "
            "action> + args{...}; or entity=<record entity> + "
            "operation=create|update|duplicate + changes{...} (+record_id "
            "for update/duplicate). Family actions cover record CRUD, "
            "tasks, rooms/messages, meeting minutes, evidence links, "
            "diagnostics, governed operations (activate_revision, "
            "recalculate_dashboard, commit_improvement_package, "
            "adjust_shared_resource_cost, update_signature_profile, "
            "migrate_legacy_diagram_to_native_bpmn, create/save/revise/"
            "organize_bpmn_document) and Helpdesk writes — see "
            "get_context(section='catalog'). Outcomes: executed_verified "
            "(auto_act, read-back proven) | proposal_pending_confirmation "
            "(confirm_before_act — show exact_change, get ONE explicit "
            "confirmation, then call again with proposal_id + "
            "confirmation=true) | prepared_invalid (validation failed). "
            "ops=[{capability|entity/operation, args|changes}, ...] runs "
            "a typed sequence: $ops.N.<path> refs consume earlier "
            "read-backs; the chain stops on first failure or pending "
            "proposal. Destructive deletes belong to the delete tool."
        ),
        annotations=_annotations("execute", "Execute"),
        meta=meta,
    )
    def execute(
        capability: Annotated[
            str | None,
            Field(
                description=(
                    "Canonical governed capability or family action "
                    "(e.g. create_record, create_task, activate_revision)."
                )
            ),
        ] = None,
        args: Annotated[
            dict | None,
            Field(description="Capability-scoped arguments."),
        ] = None,
        entity: Annotated[
            str | None,
            Field(description="Record entity for entity/operation form."),
        ] = None,
        operation: Annotated[
            Literal["create", "update", "duplicate"] | None,
            Field(description="Record operation for entity form."),
        ] = None,
        record_id: Annotated[
            str | None,
            Field(description="Target record id for update/duplicate."),
        ] = None,
        changes: Annotated[
            dict | None,
            Field(description="Field changes for the entity form."),
        ] = None,
        ops: Annotated[
            list[dict] | None,
            Field(
                description=(
                    "Typed multi-action sequence; $ops.N.<path> refs "
                    "consume earlier authoritative read-backs."
                )
            ),
        ] = None,
        proposal_handle: Annotated[
            str | None,
            Field(description="Opaque handle of a sealed proposal."),
        ] = None,
        proposal_id: Annotated[
            str | None,
            Field(description="Persisted proposal id (gp_...) resume token."),
        ] = None,
        confirmation: Annotated[
            bool | None,
            Field(
                description=(
                    "Explicit confirmation to commit a pending "
                    "proposal (required when the sealed policy is "
                    "confirm_before_act)."
                )
            ),
        ] = None,
    ) -> CallToolResult:
        return bridge_v3.tool_execute(
            capability=capability,
            args=args,
            entity=entity,
            operation=operation,
            record_id=record_id,
            changes=changes,
            ops=ops,
            proposal_handle=proposal_handle,
            proposal_id=proposal_id,
            confirmation=confirmation,
        )

    @mcp.tool(
        name="delete",
        title="Delete",
        description=(
            "Destructive deletes ONLY — exact proposal + explicit "
            "confirmation, never direct execution. First call prepares: "
            "entity + record_id (record delete), or capability + args "
            "for helpdesk_delete_ticket, helpdesk_unlink_glpi_session, "
            "delete_interaction_message, delete_interaction_room, "
            "manage_evidence with args.operation=delete. Returns "
            "proposal_pending_confirmation with the exact sealed change. "
            "Second call: delete(proposal_id=..., confirmation=true) "
            "commits with AuthZ revalidation and postcondition verify. "
            "Cancels, rejects and lifecycle transitions are NOT deletes — "
            "use execute with their canonical capability."
        ),
        annotations=_annotations("delete", "Delete"),
        meta=meta,
    )
    def delete(
        capability: Annotated[
            str | None,
            Field(
                description=(
                    "Destructive capability from the closed set "
                    "(helpdesk_delete_ticket, "
                    "helpdesk_unlink_glpi_session, "
                    "delete_interaction_message, "
                    "delete_interaction_room, manage_evidence "
                    "args.operation=delete)."
                )
            ),
        ] = None,
        args: Annotated[
            dict | None,
            Field(description="Destructive capability arguments."),
        ] = None,
        entity: Annotated[
            _EntityParam | None,
            Field(description="Record entity for record delete form."),
        ] = None,
        record_id: Annotated[
            str | None,
            Field(description="Target record id for entity form."),
        ] = None,
        proposal_handle: Annotated[
            str | None,
            Field(description="Opaque handle of a sealed delete proposal."),
        ] = None,
        proposal_id: Annotated[
            str | None,
            Field(description="Persisted delete proposal id resume token."),
        ] = None,
        confirmation: Annotated[
            bool | None,
            Field(
                description=(
                    "Explicit confirmation — deletes always require a "
                    "pending proposal plus confirmation=true."
                )
            ),
        ] = None,
    ) -> CallToolResult:
        return bridge_v3.tool_delete(
            capability=capability,
            args=args,
            entity=entity,
            record_id=record_id,
            proposal_handle=proposal_handle,
            proposal_id=proposal_id,
            confirmation=confirmation,
        )

    registered = {t.name for t in mcp._tool_manager.list_tools()}
    missing = set(MCP_TOOL_NAMES) - registered
    if missing:
        logger.error("teo_mcp_tools_missing=%s", sorted(missing))
    return mcp


__all__ = ["TransformometroMCPServer", "create_mcp_server"]
