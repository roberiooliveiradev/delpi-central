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
from engineering_app.interface.mcp import semantic_bridge, tool_bridge as bridge

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

    @mcp.tool(
        name="export_nonconformities",
        title="Export nonconformities",
        description=(
            "READ-only full JSON export of the nonconformity record set "
            "(backup/migration contract): version, generated_at, count "
            "and items — official Engineering store only."
        ),
        annotations=_annotations("export_nonconformities", "Export nonconformities"),
        meta=meta,
    )
    async def export_nonconformities() -> CallToolResult:
        return await bridge.tool_export_nonconformities()

    @mcp.tool(
        name="list_lmps",
        title="List LMPs",
        description=(
            "READ-only functional LMP list (orders tracked by "
            "Engineering). Filters (optional): start_date/end_date "
            "YYYY-MM-DD, branch, listing_type, status, page/page_size. "
            "Delegated official TOTVS facts under Engineering rules."
        ),
        annotations=_annotations("list_lmps", "List LMPs"),
        meta=meta,
    )
    async def list_lmps(
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
        listing_type: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> CallToolResult:
        return await bridge.tool_list_lmps(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            listing_type=listing_type,
            status=status,
            page=page,
            page_size=page_size,
        )

    @mcp.tool(
        name="get_lmp_summary",
        title="Get LMP summary",
        description=(
            "READ-only realized LMP KPIs (no goals/IDD) for a period: "
            "counts and lead-time aggregates — official values only."
        ),
        annotations=_annotations("get_lmp_summary", "Get LMP summary"),
        meta=meta,
    )
    async def get_lmp_summary(
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
    ) -> CallToolResult:
        return await bridge.tool_get_lmp_summary(
            start_date=start_date, end_date=end_date, branch=branch
        )

    @mcp.tool(
        name="get_lmp_detail",
        title="Get LMP detail",
        description=(
            "READ-only functional detail of a single OV/LMP by "
            "sale_number: status, dates, proposal context and flags "
            "under Engineering rules. not_found is honest."
        ),
        annotations=_annotations("get_lmp_detail", "Get LMP detail"),
        meta=meta,
    )
    async def get_lmp_detail(
        sale_number: str,
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
    ) -> CallToolResult:
        return await bridge.tool_get_lmp_detail(
            sale_number=sale_number,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )

    @mcp.tool(
        name="get_lmp_history",
        title="Get LMP history",
        description=(
            "READ-only OV history by sale_number. view=events returns "
            "the audit event list; view=flow returns status "
            "transitions/lead-time flow — use it to explain why an LMP "
            "was late or how it progressed. Optional period/branch/"
            "revision filters."
        ),
        annotations=_annotations("get_lmp_history", "Get LMP history"),
        meta=meta,
    )
    async def get_lmp_history(
        sale_number: str,
        view: str,
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
        revision: str | None = None,
    ) -> CallToolResult:
        return await bridge.tool_get_lmp_history(
            sale_number=sale_number,
            view=view,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            revision=revision,
        )

    @mcp.tool(
        name="get_lmp_goal_context",
        title="Get LMP goal context",
        description=(
            "READ-only goals context for the LMP dashboard — delegated "
            "to the Strategic Indicators owner; explains targets behind "
            "on-time/lead-time evaluation."
        ),
        annotations=_annotations("get_lmp_goal_context", "Get LMP goal context"),
        meta=meta,
    )
    async def get_lmp_goal_context(
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
    ) -> CallToolResult:
        return await bridge.tool_get_lmp_goal_context(
            start_date=start_date, end_date=end_date, branch=branch
        )

    @mcp.tool(
        name="get_lmp_department_idd",
        title="Get LMP department IDD",
        description=(
            "READ-only departmental IDD score — delegated to the "
            "Strategic Indicators owner; optional competence (YYYY-MM) "
            "or period filter."
        ),
        annotations=_annotations(
            "get_lmp_department_idd", "Get LMP department IDD"
        ),
        meta=meta,
    )
    async def get_lmp_department_idd(
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
    ) -> CallToolResult:
        return await bridge.tool_get_lmp_department_idd(
            competence=competence,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )

    @mcp.tool(
        name="get_lmp_nc_streak",
        title="Get LMP NC streak",
        description=(
            "READ-only days-without-NC streak as published by the NC "
            "owner for the LMP dashboard — delegated, never "
            "recalculated."
        ),
        annotations=_annotations("get_lmp_nc_streak", "Get LMP NC streak"),
        meta=meta,
    )
    async def get_lmp_nc_streak() -> CallToolResult:
        return await bridge.tool_get_lmp_nc_streak()

    @mcp.tool(
        name="get_product_structure",
        title="Get product structure",
        description=(
            "READ-only product structure/BOM by product_code — "
            "delegated to the Products owner with the caller's Bearer; "
            "payload returned intact with honest availability."
        ),
        annotations=_annotations("get_product_structure", "Get product structure"),
        meta=meta,
    )
    async def get_product_structure(
        product_code: str,
        max_depth: int = 6,
        page_size: int = 200,
    ) -> CallToolResult:
        return await bridge.tool_get_product_structure(
            product_code=product_code,
            max_depth=max_depth,
            page_size=page_size,
        )

    @mcp.tool(
        name="create_nonconformity",
        title="Create nonconformity",
        description=(
            "ACT — creates a nonconformity through the official "
            "Engineering contract as the authenticated human. Present "
            "the candidate via prepare_nonconformity_mutation first; "
            "call with confirmed=true ONLY after the user explicitly "
            "authorizes the creation. Optional idempotency_key "
            "deduplicates retries. Result includes read-back "
            "postcondition. Never invent product, date, user, cause or "
            "corrective action data the user did not provide."
        ),
        annotations=_annotations("create_nonconformity", "Create nonconformity"),
        meta=meta,
    )
    async def create_nonconformity(
        payload: dict,
        confirmed: bool = False,
        idempotency_key: str | None = None,
    ) -> CallToolResult:
        return await bridge.tool_create_nonconformity(
            payload=payload,
            confirmed=confirmed,
            idempotency_key=idempotency_key,
        )

    @mcp.tool(
        name="update_nonconformity",
        title="Update nonconformity",
        description=(
            "ACT — updates a nonconformity. The official contract is "
            "full-replace PUT: pass ONLY the intended field changes in "
            "`changes`; the bridge fetches the current record, merges "
            "and sends the full payload with optimistic locking. 409 "
            "means a concurrent edit — re-fetch and re-confirm with the "
            "user. confirmed=true required."
        ),
        annotations=_annotations("update_nonconformity", "Update nonconformity"),
        meta=meta,
    )
    async def update_nonconformity(
        record_id: str,
        changes: dict,
        confirmed: bool = False,
        expected_updated_at: str | None = None,
    ) -> CallToolResult:
        return await bridge.tool_update_nonconformity(
            record_id=record_id,
            changes=changes,
            confirmed=confirmed,
            expected_updated_at=expected_updated_at,
        )

    @mcp.tool(
        name="delete_nonconformity",
        title="Delete nonconformity",
        description=(
            "ACT destructive — hard-deletes a nonconformity AND its "
            "history (official cascade, irreversible). HIGH RISK: "
            "present the record first and require explicit user "
            "confirmation; call with confirmed=true only afterwards. "
            "Result includes the deleted record summary and read-back "
            "postcondition."
        ),
        annotations=_annotations("delete_nonconformity", "Delete nonconformity"),
        meta=meta,
    )
    async def delete_nonconformity(
        record_id: str,
        confirmed: bool = False,
    ) -> CallToolResult:
        return await bridge.tool_delete_nonconformity(
            record_id=record_id, confirmed=confirmed
        )

    @mcp.tool(
        name="import_nonconformities",
        title="Import nonconformities",
        description=(
            "ACT destructive — JSON import that REPLACES the entire "
            "nonconformity record set when dry_run=false (legacy "
            "semantics). ALWAYS run with dry_run=true first and present "
            "the impact report (would_replace_all, per-item results). "
            "Real import requires dry_run=false + confirm_replace=true "
            "+ confirmed=true after explicit user authorization; the "
            "environment may refuse replacement — report the refusal "
            "honestly, never retry to bypass it."
        ),
        annotations=_annotations("import_nonconformities", "Import nonconformities"),
        meta=meta,
    )
    async def import_nonconformities(
        items: list,
        confirmed: bool = False,
        dry_run: bool = True,
        confirm_replace: bool = False,
    ) -> CallToolResult:
        return await bridge.tool_import_nonconformities(
            items=items,
            confirmed=confirmed,
            dry_run=dry_run,
            confirm_replace=confirm_replace,
        )

    # --- Semantic surface (EVA.MCP.SEMANTIC.R1 / plano 54) ---------------
    # Exactly six stable tools; (entity, action) dispatch via the typed
    # registry. New Engineering capabilities become actions, never tools.

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
