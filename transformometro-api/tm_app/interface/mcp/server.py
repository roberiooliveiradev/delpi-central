"""MCPServer — TÉO capability-driven MCP (PREPARE → commit_proposal)."""

from __future__ import annotations

import logging
from typing import Any, Literal

from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from delpi_mcp.tool_metadata import (
    DELPI_META_TOOL_CLASS,
    security_schemes_meta,
    tool_annotations_payload,
)
from delpi_mcp.transport import mcp_transport_security_settings
from mcp.types import CallToolResult, Tool as MCPTool, ToolAnnotations
from pydantic import ConfigDict

from tm_app.application.gpt_actions.capability_descriptors import (
    RECORD_OPERATIONS,
)
from tm_app.application.gpt_actions.entities import (
    GptAnalysisView,
    GptEntity,
)
from tm_app.application.gpt_actions.parity_capabilities_service import (
    MEETING_MINUTE_READ_ACTION_VALUES,
)
from tm_app.application.governed_writes.orchestrator import (
    GOVERNED_OPERATION_ACTION_TO_CAPABILITY,
    MEETING_MINUTE_ACTION_TO_CAPABILITY,
)
from tm_app.application.methodology.guide_v2 import (
    INTENT_IDS,
    SUPPORTED_GUIDE_VERSIONS,
)
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

# Canonical owner value domains projected as Literal so the MCP
# inputSchema declares the valid values (enum) — the same authority
# the GPT Actions OpenAPI builder already uses; handlers still
# receive plain strings at runtime.
_EntityParam = Literal[tuple(e.value for e in GptEntity)]
_AnalysisViewParam = Literal[tuple(v.value for v in GptAnalysisView)]
_RecordOperationParam = Literal[tuple(sorted(RECORD_OPERATIONS))]
_MinuteReadActionParam = Literal[
    tuple(sorted(MEETING_MINUTE_READ_ACTION_VALUES))
]
_MinuteChangeActionParam = Literal[
    tuple(sorted(MEETING_MINUTE_ACTION_TO_CAPABILITY))
]
_GovernedOperationParam = Literal[
    tuple(sorted(GOVERNED_OPERATION_ACTION_TO_CAPABILITY))
]
_GuideVersionParam = Literal[tuple(sorted(SUPPORTED_GUIDE_VERSIONS))]
_MethodIntentParam = Literal[tuple(sorted(INTENT_IDS))]


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
        name="get_workspace_context",
        title="Get current workspace context",
        description=(
            "Current Transformômetro workspace the user is viewing "
            "(process/instance/revision/area refs). Navigation hint only — "
            "never domain truth, never authorization. For 'this process', "
            "'current revision', 'the improvement I'm editing' style "
            "references: read this first, then call get_process_context with "
            "the returned refs for authoritative facts."
        ),
        annotations=_annotations("get_workspace_context", "Get workspace context"),
        meta=meta,
    )
    def get_workspace_context() -> CallToolResult:
        return bridge.tool_get_workspace_context()

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
            "guide_version selects teo-method-playbooks-v1 (default) or "
            "teo-method-playbooks-v2 (intent routing, readiness, soft "
            "composition, sufficiency). V2 also accepts intent and an optional "
            "context object of process facts (boundary_known, as_is_known, "
            "problem_defined, candidate_cause, flow_known, ...). V2 responses "
            "include supported_context_facts — the accepted vocabulary, "
            "accepted values and semantics. "
            "Guidance is not authorization, not domain truth, and does not write."
        ),
        annotations=_annotations("get_methodology_guide", "Get methodology guide"),
        meta=meta,
    )
    def get_methodology_guide(
        method: str | None = None,
        task: str | None = None,
        guide_version: _GuideVersionParam | None = None,
        intent: _MethodIntentParam | None = None,
        context: dict[str, Any] | None = None,
    ) -> CallToolResult:
        return bridge.tool_get_methodology_guide(
            method=method,
            task=task,
            guide_version=guide_version,
            intent=intent,
            context=context,
        )

    @mcp.tool(
        name="get_product_guide",
        title="Get product usage guide",
        description=(
            "READ-only product usage guidance for Portal/Transformômetro "
            "features — how/when/why to use a capability correctly "
            "(GUIDANCE, never domain truth, AuthZ or execution policy; "
            "live contract stays in get_catalog). topic omitted returns "
            "the topic index. section: overview|when_to_use|how_to_use|"
            "field_guidance|quality|relationships|all. Unknown topic "
            "fails typed — never falls back to another guide."
        ),
        annotations=_annotations("get_product_guide", "Get product usage guide"),
        meta=meta,
    )
    def get_product_guide(
        topic: str | None = None,
        section: str | None = None,
    ) -> CallToolResult:
        return bridge.tool_get_product_guide(topic=topic, section=section)

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
            "(competencia/horizonte_meses optional). READ-only — never persists."
        ),
        annotations=_annotations("analyze", "Analyze dashboard"),
        meta=meta,
    )
    def analyze(
        view: _AnalysisViewParam,
        filial_id: str | None = None,
        setor_id: str | None = None,
        processo_id: str | None = None,
        revisao_id: str | None = None,
        instancia_id: str | None = None,
        familia_processo: str | None = None,
        competencia: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
        horizonte_meses: int | None = None,
        limit: int | None = None,
    ) -> CallToolResult:
        return bridge.tool_analyze(
            view=view,
            filial_id=filial_id,
            setor_id=setor_id,
            processo_id=processo_id,
            revisao_id=revisao_id,
            instancia_id=instancia_id,
            familia_processo=familia_processo,
            competencia=competencia,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
            horizonte_meses=horizonte_meses,
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
        entity: _EntityParam,
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
    def get_record(entity: _EntityParam, id: str) -> CallToolResult:
        return bridge.tool_get_record(entity=entity, id=id)

    # --- Semantic family: evidence (structured metadata only) --------------

    @mcp.tool(
        name="evidence_read",
        title="Evidence read",
        description=(
            "READ: evidence metadata — action=list (scope=process|revision, "
            "parent_id required). Binary payloads are not available on this "
            "transport. Writes use prepare_evidence_change."
        ),
        annotations=_annotations("evidence_read", "Evidence read"),
        meta=meta,
    )
    def evidence_read(
        action: Literal["list"],
        scope: str | None = None,
        parent_id: str | None = None,
    ) -> CallToolResult:
        return bridge.tool_evidence_read(
            action=action, scope=scope, parent_id=parent_id
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

    # --- Semantic family: meeting minutes -----------------------------------

    @mcp.tool(
        name="meeting_minute_read",
        title="Meeting minute read",
        description=(
            "READ/ANALYSIS: pending_signatures|audit|versions|participants|"
            "signers|generate_from_transcript (transcript draft is "
            "analysis-only — never persists). Writes use "
            "prepare_meeting_minute_change followed by commit_proposal per "
            "execution_policy."
        ),
        annotations=_annotations("meeting_minute_read", "Meeting minute read"),
        meta=meta,
    )
    def meeting_minute_read(
        action: _MinuteReadActionParam,
        minute_id: str | None = None,
        data: dict | None = None,
    ) -> CallToolResult:
        return bridge.tool_meeting_minute_read(
            action=action, minute_id=minute_id, data=data
        )

    # --- Semantic family: collaboration -------------------------------------
    # Transformômetro tasks + interaction rooms/messages — same canonical
    # use cases as the Portal (TaskCommandUseCases / InteractionRoomUseCases).

    @mcp.tool(
        name="collaboration_read",
        title="Collaboration read",
        description=(
            "READ: collaboration surface — tasks (action=my_tasks, status "
            "filter pending|completed|cancelled|all; action=task needs "
            "task_id; action=process_tasks needs processo_id) and "
            "interaction rooms (action=rooms, inbox_filter; action=room "
            "needs room_id; action=messages needs room_id, optional "
            "limit/before_id; action=attachments returns metadata only — "
            "binary transfer has no MCP transport). Same canonical use "
            "cases as the Portal."
        ),
        annotations=_annotations("collaboration_read", "Collaboration read"),
        meta=meta,
    )
    def collaboration_read(
        action: Literal[
            "my_tasks",
            "task",
            "process_tasks",
            "rooms",
            "room",
            "messages",
            "attachments",
        ],
        task_id: str | None = None,
        processo_id: str | None = None,
        status: str = "pending",
        room_id: str | None = None,
        inbox_filter: str = "all",
        limit: int = 50,
        before_id: str | None = None,
    ) -> CallToolResult:
        return bridge.tool_collaboration_read(
            action=action,
            task_id=task_id,
            processo_id=processo_id,
            status=status,
            room_id=room_id,
            inbox_filter=inbox_filter,
            limit=limit,
            before_id=before_id,
        )

    # --- Semantic family: diagnostics (MCP-native) --------------------------

    @mcp.tool(
        name="diagnostic_read",
        title="Diagnostic read",
        description=(
            "READ: Diagnostic V1 — action=get (diagnostic_id; full detail "
            "with revision context, resolved evidence links and data-quality "
            "signals — findings are OBSERVED/CALCULATED, hypotheses and "
            "conclusions are INFERRED claims, VALIDATED != FACT) or "
            "action=by_revision (revision_id; canonical-ordered summaries, "
            "no evidence fan-out). Use before prepare_diagnostic_change "
            "when target ids are unknown."
        ),
        annotations=_annotations("diagnostic_read", "Diagnostic read"),
        meta=meta,
    )
    def diagnostic_read(
        action: Literal["get", "by_revision"],
        diagnostic_id: str | None = None,
        revision_id: str | None = None,
    ) -> CallToolResult:
        return bridge.tool_diagnostic_read(
            action=action,
            diagnostic_id=diagnostic_id,
            revision_id=revision_id,
        )

    # --- PREPARE (semantic families — action selects capability/policy) ----

    @mcp.tool(
        name="prepare_record_change",
        title="Prepare record change",
        description=(
            "PREPARE only — never persists business state. Conventional "
            "ENTITY CRUD (create|update|delete|duplicate) for catalog "
            "entities (e.g. process_document). Returns opaque "
            "proposal_handle + exact sealed change. Do NOT use for "
            "business workflows (revision activation, evidence, meeting "
            "minutes, packages, cost adjustment, tasks, rooms, "
            "diagnostics) — use the family prepare_* tools instead. "
            "Material execution via commit_proposal(proposal_handle) "
            "follows proposal.execution_policy: auto_act "
            "(create/update/duplicate) commits immediately — no extra "
            "conversational confirmation; confirm_before_act (delete) "
            "shows the exact change and requires one explicit user "
            "confirmation first."
        ),
        annotations=_annotations("prepare_record_change", "Prepare record change"),
        meta=meta,
    )
    def prepare_record_change(
        entity: _EntityParam,
        operation: _RecordOperationParam,
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
        name="prepare_governed_operation",
        title="Prepare governed operation",
        description=(
            "PREPARE only — never persists business state. Special "
            "governed operations (NOT generic record CRUD): "
            "activate_revision (id; overwrites current — "
            "confirm_before_act), recalculate_dashboard (revisao_id or "
            "processo_id + optional competencia range — "
            "confirm_before_act), commit_improvement_package (process + "
            "instance + optional baseline/scenario; ready=false when "
            "incomplete — confirm_before_act), adjust_shared_resource_cost "
            "(recurso_compartilhado_id + valor_mensal + vigente_desde + "
            "optional observacoes — auto_act), update_signature_profile "
            "(display_name — auto_act; updates only the display name, "
            "signature image stays in UI), import_diagram_bpmn_xml "
            "(processo_id + xml text — replaces the macro diagram — "
            "confirm_before_act). Then "
            "commit_proposal per proposal.execution_policy; AuthZ is "
            "revalidated at ACT with authoritative read-back."
        ),
        annotations=_annotations(
            "prepare_governed_operation", "Prepare governed operation"
        ),
        meta=meta,
    )
    def prepare_governed_operation(
        action: _GovernedOperationParam,
        id: str | None = None,
        revisao_id: str | None = None,
        processo_id: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
        recurso_compartilhado_id: str | None = None,
        valor_mensal: float | None = None,
        vigente_desde: str | None = None,
        observacoes: str | None = None,
        process: dict | None = None,
        instance: dict | None = None,
        baseline: dict | None = None,
        scenario: dict | None = None,
        activate_scenario: bool = False,
        recalculate: bool = False,
        display_name: str | None = None,
        xml: str | None = None,
    ) -> CallToolResult:
        return bridge.tool_prepare_governed_operation(
            action=action,
            id=id,
            revisao_id=revisao_id,
            processo_id=processo_id,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
            recurso_compartilhado_id=recurso_compartilhado_id,
            valor_mensal=valor_mensal,
            vigente_desde=vigente_desde,
            observacoes=observacoes,
            process=process,
            instance=instance,
            baseline=baseline,
            scenario=scenario,
            activate_scenario=activate_scenario,
            recalculate=recalculate,
            display_name=display_name,
            xml=xml,
        )

    @mcp.tool(
        name="prepare_evidence_change",
        title="Prepare evidence change",
        description=(
            "PREPARE only — never persists business state. Evidence "
            "actions: create_link|update_description|delete (scope="
            "process|revision + parent_id required; delete needs "
            "confirm_delete=true). Structured metadata only — not generic "
            "file CRUD, no binary payloads. execution_policy="
            "confirm_before_act: show the exact change and obtain one "
            "explicit user confirmation before commit_proposal."
        ),
        annotations=_annotations(
            "prepare_evidence_change", "Prepare evidence change"
        ),
        meta=meta,
    )
    def prepare_evidence_change(
        action: Literal["create_link", "update_description", "delete"],
        scope: str,
        parent_id: str,
        evidence_id: str | None = None,
        url_externa: str | None = None,
        descricao: str | None = None,
        confirm_delete: bool = False,
    ) -> CallToolResult:
        return bridge.tool_prepare_evidence_change(
            action=action,
            scope=scope,
            parent_id=parent_id,
            evidence_id=evidence_id,
            url_externa=url_externa,
            descricao=descricao,
            confirm_delete=confirm_delete,
        )

    @mcp.tool(
        name="prepare_meeting_minute_change",
        title="Prepare meeting minute change",
        description=(
            "PREPARE only — never persists business state. Meeting-minute "
            "writes: workflow transitions send|finalize|cancel|refuse "
            "(minute_id + reason; reason required for refuse) and manage "
            "writes resend|create_version|"
            "set_participants|set_signers (minute_id + data payload; "
            "resend requires data.confirm_resend=true). READ/analyze "
            "actions — pending_signatures|audit|versions|participants|"
            "signers|generate_from_transcript — use meeting_minute_read. "
            "execution_policy=confirm_before_act: show the exact change "
            "and obtain one explicit user confirmation before "
            "commit_proposal."
        ),
        annotations=_annotations(
            "prepare_meeting_minute_change", "Prepare meeting minute change"
        ),
        meta=meta,
    )
    def prepare_meeting_minute_change(
        action: _MinuteChangeActionParam,
        minute_id: str | None = None,
        reason: str | None = None,
        data: dict | None = None,
    ) -> CallToolResult:
        return bridge.tool_prepare_meeting_minute_change(
            action=action, minute_id=minute_id, reason=reason, data=data
        )

    @mcp.tool(
        name="prepare_collaboration_change",
        title="Prepare collaboration change",
        description=(
            "PREPARE only — never persists business state. Collaboration "
            "writes via the same canonical use cases as the Portal. Task "
            "actions: create_task|update_task|complete_task|cancel_task "
            "(TaskCommandUseCases; create needs title; update/complete/"
            "cancel need task_id). Room actions: open_room (processo_id)|"
            "post_message|edit_message|delete_message|toggle_reaction|"
            "pin_message|unpin_message|mark_room_read "
            "(InteractionRoomUseCases; message actions need room_id + "
            "message_id). Then commit_proposal per proposal."
            "execution_policy — auto_act commits immediately with no "
            "extra confirmation; confirm_before_act (cancel_task, "
            "delete_message) requires one explicit user confirmation "
            "first. Binary attachment upload/download is not available "
            "on this transport."
        ),
        annotations=_annotations(
            "prepare_collaboration_change", "Prepare collaboration change"
        ),
        meta=meta,
    )
    def prepare_collaboration_change(
        action: Literal[
            "create_task",
            "update_task",
            "complete_task",
            "cancel_task",
            "open_room",
            "post_message",
            "edit_message",
            "delete_message",
            "toggle_reaction",
            "pin_message",
            "unpin_message",
            "mark_room_read",
        ],
        task_id: str | None = None,
        title: str | None = None,
        description: str | None = None,
        assignee_user_id: str | None = None,
        due_date: str | None = None,
        source_interaction_message_id: str | None = None,
        processo_id: str | None = None,
        room_id: str | None = None,
        message_id: str | None = None,
        content: str | None = None,
        parent_id: str | None = None,
        mentions: list | None = None,
        reaction: str | None = None,
    ) -> CallToolResult:
        return bridge.tool_prepare_collaboration_change(
            action=action,
            task_id=task_id,
            title=title,
            description=description,
            assignee_user_id=assignee_user_id,
            due_date=due_date,
            source_interaction_message_id=source_interaction_message_id,
            processo_id=processo_id,
            room_id=room_id,
            message_id=message_id,
            content=content,
            parent_id=parent_id,
            mentions=mentions,
            reaction=reaction,
        )

    @mcp.tool(
        name="prepare_diagnostic_change",
        title="Prepare diagnostic change",
        description=(
            "PREPARE only — does not persist. Diagnostic writes: "
            "action=create (revision_id + problem_statement; "
            "diagnostic_id is server-generated and shown in the sealed "
            "change — never supply it; execution_policy=auto_act so "
            "commit_proposal may execute immediately without a second "
            "confirmation) or one of the canonical manage actions "
            "(add_finding|add_hypothesis|add_causal_link|"
            "add_evidence_link|add_conclusion|validate_hypothesis|"
            "reject_hypothesis|supersede_hypothesis|"
            "mark_hypothesis_stale_evidence|"
            "mark_hypothesis_revalidation_required|validate_conclusion|"
            "reject_conclusion|supersede_conclusion — diagnostic_id + "
            "payload; add_* entity ids are server-generated, lifecycle/"
            "mark actions target EXISTING ids — READ first via "
            "diagnostic_read; execution_policy=confirm_before_act: one "
            "explicit user confirmation before commit_proposal)."
        ),
        annotations=_annotations(
            "prepare_diagnostic_change", "Prepare diagnostic change"
        ),
        meta=meta,
    )
    def prepare_diagnostic_change(
        action: Literal[
            "create",
            "add_finding",
            "add_hypothesis",
            "add_causal_link",
            "add_evidence_link",
            "add_conclusion",
            "validate_hypothesis",
            "reject_hypothesis",
            "supersede_hypothesis",
            "mark_hypothesis_stale_evidence",
            "mark_hypothesis_revalidation_required",
            "validate_conclusion",
            "reject_conclusion",
            "supersede_conclusion",
        ],
        diagnostic_id: str | None = None,
        revision_id: str | None = None,
        problem_statement: str | None = None,
        provenance: dict | None = None,
        payload: dict | None = None,
    ) -> CallToolResult:
        return bridge.tool_prepare_diagnostic_change(
            action=action,
            diagnostic_id=diagnostic_id,
            revision_id=revision_id,
            problem_statement=problem_statement,
            provenance=provenance,
            payload=payload,
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
        proposal_handle: str, confirmation: bool
    ) -> CallToolResult:
        return bridge.tool_commit_proposal(
            proposal_handle=proposal_handle, confirmation=confirmation
        )

    registered = {t.name for t in mcp._tool_manager.list_tools()}
    missing = set(MCP_TOOL_NAMES) - registered
    if missing:
        logger.error("teo_mcp_tools_missing=%s", sorted(missing))
    return mcp


__all__ = ["TransformometroMCPServer", "create_mcp_server"]
