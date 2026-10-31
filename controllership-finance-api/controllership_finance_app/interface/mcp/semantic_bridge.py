"""CLARA semantic MCP bridge — six stable tools over a typed registry.

CLARA-MCP-SEMANTIC-001 (doc 119): the public ``tools/list`` surface is
exactly six tools — ``get_context``, ``read``, ``analyze``,
``knowledge``, ``execute``, ``delete``. Every call dispatches on
``(entity, action)`` from the owner-local allowlist registry; no URL,
HTTP method, SQL or model-supplied handler names. All handlers delegate
to the same BFF route functions / governed writes used by the legacy
surface — parity, never reimplementation.

Governance (política vigente — docs 94/106, plano §5):
- ``read``/``analyze``/``knowledge`` — immediate, human principal +
  live Core AuthZ via the canonical route functions.
- ``execute`` — ``phase="prepare"`` seals the proposal and returns the
  Portal consent URL; ``phase="commit"`` executes only with the exact
  handle. Direct execution is not granted by this refactor: every
  governed operation keeps PREPARE → trusted Portal consent → ACT.
- ``delete`` — same governed flow, restricted to capabilities marked
  ``destructive`` in the catalog.
- ``batch`` — reuses ``ClaraBatchOrchestrator``: one consolidated
  Portal consent covers the whole ordered plan; governed operations
  never bypass the challenge.
"""

from __future__ import annotations

from typing import Any, Callable

from mcp.types import CallToolResult

from delpi_mcp.errors import mcp_tool_result

from controllership_finance_app.application.clara.agent_intelligence_service import (  # noqa: E501
    ClaraAgentIntelligenceService,
)
from controllership_finance_app.domain.closing_checklist.errors import (
    ChecklistDomainError,
)
from controllership_finance_app.interface.mcp import tool_bridge as bridge
from controllership_finance_app.interface.mcp.tool_bridge import (
    _batch_orchestrator,
    _domain_fail,
    _error,
    _governed_writes,
    _ok,
    _user_and_access,
)
from controllership_finance_app.interface.http.authz import actor_subject

SEMANTIC_CATALOG_VERSION = "clara-semantic-v1"

MAX_PAGE_SIZE = 200


# ------------------------------------------------------------------
# helpers internos
# ------------------------------------------------------------------


def _err(
    message: str,
    *,
    status_code: int = 400,
    error_code: str = "validation_error",
    data: dict | None = None,
) -> CallToolResult:
    return _error(
        message,
        status_code=status_code,
        data=data,
        error_code=error_code,
    )


def _wrap(
    entity: str, action: str, result: CallToolResult
) -> CallToolResult:
    """Envelope semântico — entity/action carimbados sobre o payload
    oficial; semântica de sucesso/erro do handler preservada."""
    payload = dict(
        getattr(result, "structured_content", None) or {}
    )
    payload.setdefault("entity", entity)
    payload.setdefault("action", action)
    return mcp_tool_result(payload, is_error=bool(result.is_error))


def _clean(params: dict | None) -> dict:
    out = {}
    for key, value in (params or {}).items():
        if value is not None:
            out[key] = value
    return out


def _validate_params(
    spec: dict, params: dict, *, where: str
) -> CallToolResult | None:
    """Schema por action: required + allowlist + tipos básicos."""
    required = spec.get("required", ())
    missing = [p for p in required if params.get(p) is None]
    if missing:
        return _err(
            f"Parâmetros obrigatórios ausentes: {missing}.",
            error_code="validation_error",
            data={"missing": missing, "at": where},
        )
    allowed = set(spec.get("allowed", ())) | set(required)
    unknown = sorted(set(params) - allowed)
    if unknown:
        return _err(
            f"Parâmetros desconhecidos para a action: {unknown}.",
            error_code="validation_error",
            data={"unknown": unknown, "allowed": sorted(allowed)},
        )
    return None


def _capability_id(entity: str, action: str) -> str:
    return f"{entity}.{action}"


# ------------------------------------------------------------------
# READ registry — (entity, action) → handler + schema de params
# ------------------------------------------------------------------
# `ref_param`: nome do parâmetro que recebe `ref`.
# `allowed`: filtros aceitos em `filters`/`params`.


def _read_spec(
    handler: Callable[..., CallToolResult],
    *,
    ref_param: str | None = None,
    required: tuple[str, ...] = (),
    allowed: tuple[str, ...] = (),
) -> dict:
    return {
        "handler": handler,
        "ref_param": ref_param,
        "required": required,
        "allowed": allowed,
    }


READ_ACTIONS: dict[tuple[str, str], dict] = {
    ("competence", "list"): _read_spec(
        bridge.tool_list_competences
    ),
    ("competence", "get"): _read_spec(
        bridge.tool_get_competence, required=("period",)
    ),
    ("competence", "state"): _read_spec(
        bridge.tool_get_competence_state, required=("period",)
    ),
    ("competence", "cockpit"): _read_spec(
        bridge.tool_get_closing_cockpit, required=("period",)
    ),
    ("checklist", "list"): _read_spec(
        bridge.tool_get_checklist_items,
        required=("period",),
        allowed=("sheet", "recipient_area", "state"),
    ),
    ("checklist", "get"): _read_spec(
        bridge.tool_get_checklist_item,
        ref_param="item_key",
        required=("period", "item_key"),
    ),
    ("document", "list"): _read_spec(
        bridge.tool_list_documents,
        required=("period",),
        allowed=("snapshot_item_id", "state", "branch_scope"),
    ),
    ("document", "get"): _read_spec(
        bridge.tool_get_document,
        ref_param="document_id",
        required=("period", "document_id"),
        allowed=("branch_scope", "include_audit"),
    ),
    ("document", "participants"): _read_spec(
        bridge.tool_lookup_participants,
        ref_param="document_id",
        required=("period", "document_id", "ids"),
        allowed=("branch_scope",),
    ),
    ("pendency", "list"): _read_spec(
        bridge.tool_list_pendencies,
        required=("period",),
        allowed=("state", "kind"),
    ),
    ("pendency", "get"): _read_spec(
        bridge.tool_get_pendency,
        ref_param="pendency_id",
        required=("period", "pendency_id"),
        allowed=("include_history", "branch_scope"),
    ),
    ("task", "list"): _read_spec(
        bridge.tool_list_my_tasks, allowed=("period",)
    ),
    ("p3", "state"): _read_spec(
        bridge.tool_get_p3_reconciliation, required=("period",)
    ),
    ("p3", "events"): _read_spec(
        bridge.tool_list_p3_events, required=("period",)
    ),
    ("package", "review"): _read_spec(
        bridge.tool_get_package_review, required=("period",)
    ),
    ("package", "get"): _read_spec(
        bridge.tool_get_package,
        ref_param="package_id",
        required=("period", "package_id"),
    ),
    ("validation", "item"): _read_spec(
        bridge.tool_get_item_validation,
        ref_param="item_key",
        required=("period", "item_key"),
        allowed=("branch_scope",),
    ),
    ("report", "settlements"): _read_spec(
        bridge.tool_get_financial_settlements,
        required=("side", "start_date", "end_date"),
        allowed=(
            "nature_code", "movement_type", "sort_by", "sort_dir",
            "page", "page_size",
        ),
    ),
    ("report", "settlements_summary"): _read_spec(
        bridge.tool_get_financial_settlements_summary,
        required=("start_date", "end_date"),
        allowed=("nature_code", "movement_type"),
    ),
    ("report", "stock_inventory"): _read_spec(
        bridge.tool_get_stock_inventory,
        required=("period",),
        allowed=(
            "branch", "report_scope", "warehouse",
            "page", "page_size",
        ),
    ),
    ("report", "stock_movements"): _read_spec(
        bridge.tool_get_stock_movements,
        required=("period",),
        allowed=("branch", "report_scope"),
    ),
    ("report", "work_in_process"): _read_spec(
        bridge.tool_get_work_in_process,
        required=("period",),
        allowed=(
            "branch", "report_scope", "warehouse",
            "page", "page_size",
        ),
    ),
    ("report", "stock_reconciliation"): _read_spec(
        bridge.tool_get_stock_reconciliation,
        required=("period",),
        allowed=("branch", "report_scope"),
    ),
    ("report", "stock_kardex"): _read_spec(
        bridge.tool_get_stock_kardex,
        required=("period",),
        allowed=(
            "branch", "warehouse", "product_code",
            "movement_kind", "page", "page_size",
        ),
    ),
    ("report", "stock_kardex_summary"): _read_spec(
        bridge.tool_get_stock_kardex_summary,
        required=("period",),
        allowed=("branch", "warehouse", "product_code"),
    ),
    ("report", "inventory_adjustments"): _read_spec(
        bridge.tool_get_inventory_adjustments,
        required=("period",),
        allowed=(
            "branch", "warehouse", "product_code",
            "movement_kind", "page", "page_size",
        ),
    ),
    ("report", "inventory_adjustments_summary"): _read_spec(
        bridge.tool_get_inventory_adjustments_summary,
        required=("period",),
        allowed=("branch", "warehouse", "product_code"),
    ),
    ("report", "cpv"): _read_spec(
        bridge.tool_get_cpv,
        required=("period",),
        allowed=("branch", "top_limit"),
    ),
    ("report", "cost_center_expenses"): _read_spec(
        bridge.tool_get_cost_center_expenses,
        required=("period",),
        allowed=(
            "branch", "universe", "view", "cost_center",
            "product_code", "document", "supplier_code", "tes",
            "page", "page_size",
        ),
    ),
    ("report", "billing_exclusion_roster"): _read_spec(
        bridge.tool_get_billing_exclusion_roster,
        required=("period",),
        allowed=(
            "branch", "view", "product_group",
            "product_code", "document", "customer_code", "tes",
            "page", "page_size",
        ),
    ),
    ("report", "cost_closing_state"): _read_spec(
        bridge.tool_get_cost_closing_state,
        required=("period",),
        allowed=("branch",),
    ),
    ("report", "matrix"): _read_spec(
        bridge.tool_get_report_matrix,
        required=("period",),
        allowed=("branch_scope",),
    ),
    ("catalog", "list"): _read_spec(
        bridge.tool_list_closing_catalogs
    ),
    ("catalog", "entries"): _read_spec(
        bridge.tool_list_catalog_entries,
        required=("catalog_key",),
        allowed=("include_inactive",),
    ),
    ("template", "list"): _read_spec(
        bridge.tool_list_checklist_templates
    ),
    ("template", "version"): _read_spec(
        bridge.tool_get_checklist_template_version,
        ref_param="template_id",
        required=("template_id", "version"),
    ),
    ("received", "deliveries"): _read_spec(
        bridge.tool_list_received_deliveries
    ),
    ("received", "delivery"): _read_spec(
        bridge.tool_get_received_delivery, required=("period",)
    ),
    ("received", "document"): _read_spec(
        bridge.tool_get_received_document,
        ref_param="document_id",
        required=("period", "document_id"),
    ),
    ("batch", "status"): _read_spec(
        bridge.tool_get_batch_status,
        ref_param="batch_id",
        required=("batch_id",),
    ),
}


ANALYZE_ACTIONS: dict[str, dict] = {
    "closing_blockers": {
        "handler": bridge.tool_analyze_closing_blockers,
        "required": ("period",),
        "allowed": (),
        "description": (
            "Achados FACT/RECOMMENDATION sobre bloqueios do "
            "fechamento da competência."
        ),
    },
    "report_comparison": {
        "handler": bridge.tool_analyze_report_comparison,
        "required": ("subjects",),
        "allowed": (
            "comparison_kind", "subjects", "measure", "grain",
            "baseline_index", "diff_page", "diff_page_size",
        ),
        "description": (
            "Comparação transversal governada de relatórios "
            "(doc 126): 2–6 sujeitos {reportId, period, branch, "
            "filters}, kinds PERIOD|BRANCH|REPORT|DOCUMENT|TREND|"
            "EXPLAIN; classifica compatibilidade semântica por par "
            "e nunca trata ausência como zero."
        ),
    },
}


KNOWLEDGE_ACTIONS: dict[str, dict] = {
    "search": {
        "handler": bridge.tool_search_closing_knowledge,
        "required": ("query",),
        "allowed": ("topic", "report_id", "business_step", "limit"),
    },
    "get": {
        "handler": bridge.tool_get_knowledge_item,
        "required": ("knowledge_id",),
        "allowed": (),
    },
    "sources": {
        "handler": bridge.tool_list_knowledge_sources,
        "required": (),
        "allowed": (),
    },
}


# ------------------------------------------------------------------
# catálogo semântico (get_context)
# ------------------------------------------------------------------


def _semantic_catalog(identity: dict | None = None) -> dict:
    """Catálogo versionado de (entity, action) — sem schemas pesados;
    detalhe por action via get_context(topic="schema")."""
    managed = bool((identity or {}).get("is_manage"))
    dre = bool((identity or {}).get("is_dre"))

    def _entry(tool: str, entity: str, action: str, gate: str,
               required: tuple[str, ...], description: str) -> dict:
        return {
            "entity": entity,
            "action": action,
            "tool": tool,
            "gate": gate,
            "required_params": list(required),
            "description": description,
        }

    read_entries = [
        _entry("read", e, a, "access", s["required"], s["handler"].__doc__ or "")
        for (e, a), s in sorted(READ_ACTIONS.items())
    ]
    analyze_entries = [
        _entry("analyze", "closing", name, "access", spec["required"],
               spec["description"])
        for name, spec in sorted(ANALYZE_ACTIONS.items())
    ]
    knowledge_entries = [
        _entry("knowledge", "knowledge", name, "access",
               spec["required"], spec["handler"].__doc__ or "")
        for name, spec in sorted(KNOWLEDGE_ACTIONS.items())
    ]
    governed = []
    try:
        for cap in _governed_writes().capabilities():
            entity, _, action = cap["capability"].partition(".")
            governed.append(
                _entry(
                    "delete" if cap.get("destructive") else "execute",
                    entity,
                    action,
                    cap["gate"],
                    tuple(cap["required_params"]),
                    "",
                )
                | {
                    "capability": cap["capability"],
                    "resource_type": cap["resource_type"],
                    "destructive": bool(cap.get("destructive")),
                    "direct": bool(cap.get("direct")),
                    "phase_policy": (
                        "direct_or_prepare_consent_act"
                        if cap.get("direct")
                        else "prepare_consent_act"
                    ),
                }
            )
    except Exception:  # noqa: BLE001 — catálogo nunca quebra contexto
        governed = []
    return {
        "catalog_version": SEMANTIC_CATALOG_VERSION,
        "actor_capabilities": {
            "access": True,
            "manage": managed,
            "dre": dre,
        },
        "actions": {
            "read": read_entries,
            "analyze": analyze_entries,
            "knowledge": knowledge_entries,
            "governed": governed,
        },
    }


def _identity_snapshot(user) -> dict:
    is_dre = False
    try:
        is_dre = bool(
            _governed_writes()._identity().get("is_dre")
        )
    except Exception:  # noqa: BLE001 — identidade best-effort
        is_dre = False
    return {
        "subject": actor_subject(user),
        "name": getattr(user, "name", None)
        or getattr(user, "email", None),
        "is_manage": bridge._is_manage(user),
        "is_dre": is_dre,
    }


def _schema_for(entity: str, action: str) -> dict | None:
    """Schema JSON de uma action específica — sob demanda, nunca em
    massa (budget de contexto)."""
    key = (entity, action)
    if key in READ_ACTIONS:
        spec = READ_ACTIONS[key]
        return {
            "tool": "read",
            "entity": entity,
            "action": action,
            "required_params": list(spec["required"]),
            "optional_params": sorted(spec["allowed"]),
            "top_level_args": [
                "entity", "action", "ref", "period", "filters",
                "page", "page_size", "projection",
            ],
        }
    if action in ANALYZE_ACTIONS:
        spec = ANALYZE_ACTIONS[action]
        return {
            "tool": "analyze",
            "analysis_type": action,
            "required_params": list(spec["required"]),
            "optional_params": sorted(spec["allowed"]),
            "description": spec["description"],
        }
    if action in KNOWLEDGE_ACTIONS:
        spec = KNOWLEDGE_ACTIONS[action]
        return {
            "tool": "knowledge",
            "knowledge_action": action,
            "required_params": list(spec["required"]),
            "optional_params": sorted(spec["allowed"]),
        }
    table = _governed_writes()._capability_table()
    cap_id = _capability_id(entity, action)
    spec = table.get(cap_id)
    if spec is not None:
        return {
            "tool": "delete" if spec.get("destructive") else "execute",
            "capability": cap_id,
            "gate": spec["gate"],
            "destructive": bool(spec.get("destructive")),
            "direct": bool(spec.get("direct")),
            "required_params": list(spec["required_params"]),
            "phase_policy": (
                "phase=direct (default) executa já com AuthZ + "
                "idempotência; phase=prepare → consentimento Portal → "
                "phase=commit também é aceito"
                if spec.get("direct")
                else "phase=prepare → Portal consent → phase=commit; "
                "confirmação humana verificável obrigatória"
            ),
        }
    return None


def tool_get_context(
    topic: str | None = None,
    entity: str | None = None,
    action: str | None = None,
    scope: str | None = None,
    selected_ref: str | None = None,
) -> CallToolResult:
    _request, user = _user_and_access()
    identity = _identity_snapshot(user)
    topic_norm = (topic or "").strip().lower() or "summary"

    if topic_norm == "schema":
        if not entity or not action:
            return _err(
                "topic=schema exige entity e action.",
                error_code="validation_error",
            )
        schema = _schema_for(
            entity.strip().lower(), action.strip().lower()
        )
        if schema is None:
            return _err(
                f"Action desconhecida: {entity}.{action}.",
                status_code=404,
                error_code="not_implemented",
            )
        return _ok(
            schema,
            message="Schema da action (contrato versionado).",
        )

    my_context = bridge.tool_get_my_context()
    base = {
        "actor": (
            my_context.structured_content.get("data")
            if my_context.structured_content
            else None
        ),
        "capabilities": identity,
    }
    if topic_norm in ("actor", "context"):
        return _ok(base, message="Contexto do ator autenticado.")
    if topic_norm in ("persona", "avatar"):
        return _ok(
            {
                **base,
                "agent_directives": (
                    ClaraAgentIntelligenceService.agent_directives()
                ),
            },
            message="Persona oficial da CLARA (FICTION_IDENTITY_ONLY).",
        )
    catalog = _semantic_catalog(identity)
    catalog["knowledge"] = bridge._safe_corpus_version()
    if topic_norm in ("catalog", "capabilities"):
        return _ok(
            {**base, "catalog": catalog},
            message="Catálogo versionado de ações efetivas.",
        )
    if topic_norm in ("summary", ""):
        counts = {
            name: len(items)
            for name, items in catalog["actions"].items()
        }
        return _ok(
            {
                **base,
                "catalog_version": SEMANTIC_CATALOG_VERSION,
                "action_counts": counts,
                "agent_directives": (
                    ClaraAgentIntelligenceService.agent_directives()
                ),
                "hint": (
                    "get_context(topic='catalog') para a lista "
                    "completa; get_context(topic='schema', entity=…, "
                    "action=…) para o contrato de uma action."
                ),
            },
            message="Contexto operacional resumido.",
        )
    return _err(
        f"topic desconhecido: {topic!r} — use summary|actor|catalog|"
        "schema|persona.",
        error_code="validation_error",
    )


# ------------------------------------------------------------------
# read / analyze / knowledge
# ------------------------------------------------------------------


def tool_read(
    entity: str,
    action: str,
    ref: str | None = None,
    period: str | None = None,
    filters: dict | None = None,
    page: int | None = None,
    page_size: int | None = None,
    projection: str | None = None,
) -> CallToolResult:
    ent = (entity or "").strip().lower()
    act = (action or "").strip().lower()
    spec = READ_ACTIONS.get((ent, act))
    if spec is None:
        return _err(
            f"Read action desconhecida: {ent}.{act} — consulte "
            "get_context(topic='catalog').",
            status_code=404,
            error_code="not_implemented",
        )
    params = dict(filters or {})
    accepted = set(spec["required"]) | set(spec["allowed"])
    if period is not None and "period" in accepted:
        params["period"] = period
    if ref is not None and spec["ref_param"]:
        params[spec["ref_param"]] = ref
    if page is not None:
        params["page"] = page
    if page_size is not None:
        if int(page_size) > MAX_PAGE_SIZE:
            return _err(
                f"page_size máximo: {MAX_PAGE_SIZE}.",
                error_code="validation_error",
            )
        params["page_size"] = page_size
    bad = _validate_params(spec, _clean(params), where=f"{ent}.{act}")
    if bad is not None:
        return bad
    result = spec["handler"](**_clean(params))
    return _wrap(ent, act, result)


def tool_analyze(
    analysis_type: str,
    period: str | None = None,
    refs: list[str] | None = None,
    filters: dict | None = None,
    question: str | None = None,
    parameters: dict | None = None,
) -> CallToolResult:
    atype = (analysis_type or "").strip().lower()
    spec = ANALYZE_ACTIONS.get(atype)
    if spec is None:
        return _err(
            f"analysis_type desconhecido: {atype!r} — disponíveis: "
            f"{sorted(ANALYZE_ACTIONS)}.",
            status_code=404,
            error_code="not_implemented",
        )
    params = dict(parameters or {}) | dict(filters or {})
    if period is not None:
        params["period"] = period
    bad = _validate_params(spec, _clean(params), where=atype)
    if bad is not None:
        return bad
    result = spec["handler"](**_clean(params))
    return _wrap("closing", atype, result)


def tool_knowledge(
    action: str,
    query: str | None = None,
    topic: str | None = None,
    report_id: str | None = None,
    business_step: str | None = None,
    knowledge_id: str | None = None,
    limit: int | None = None,
) -> CallToolResult:
    act = (action or "").strip().lower()
    spec = KNOWLEDGE_ACTIONS.get(act)
    if spec is None:
        return _err(
            f"knowledge action desconhecida: {act!r} — use "
            f"{sorted(KNOWLEDGE_ACTIONS)}.",
            status_code=404,
            error_code="not_implemented",
        )
    params = _clean(
        {
            "query": query,
            "topic": topic,
            "report_id": report_id,
            "business_step": business_step,
            "knowledge_id": knowledge_id,
            "limit": limit,
        }
    )
    bad = _validate_params(spec, params, where=f"knowledge.{act}")
    if bad is not None:
        return bad
    result = spec["handler"](**params)
    return _wrap("knowledge", act, result)


# ------------------------------------------------------------------
# execute / delete — fluxo governado (PREPARE → consentimento → ACT)
# ------------------------------------------------------------------


def _governed_spec(entity: str, action: str) -> dict | None:
    table = _governed_writes()._capability_table()
    return table.get(_capability_id(entity, action))


def _prepare_single(
    entity: str,
    action: str,
    params: dict,
    actor_sub: str,
) -> CallToolResult:
    try:
        proposal = _governed_writes().prepare(
            capability=_capability_id(entity, action),
            params=params,
            actor_sub=actor_sub,
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc)
    return _wrap(entity, action, _ok(proposal))


def _commit_single(
    proposal_handle: str,
    actor_sub: str,
) -> CallToolResult:
    try:
        result = _governed_writes().commit(
            handle=proposal_handle,
            actor_sub=actor_sub,
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc)
    return _ok(result)


def _direct_single(
    entity: str,
    action: str,
    payload: dict,
    actor_sub: str,
) -> CallToolResult:
    """Execução imediata de capability DIRECT_ALLOWED (doc 126).

    Mesmo núcleo governado — selagem, claim atômico, execução
    canônica, pós-condição por read-back e auditoria — sem o desafio
    de consentimento, substituído pela constraint física de
    idempotência (V019)."""
    try:
        result = _governed_writes().execute_direct(
            capability=_capability_id(entity, action),
            params=payload,
            actor_sub=actor_sub,
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc)
    return _ok(result)


def _run_operations(
    batch: dict,
    actor_sub: str,
) -> CallToolResult:
    """Orquestra N capabilities em uma solicitação (doc 126 §4.C).

    Diretas executam já (com AuthZ + idempotência); governadas
    retornam proposta selada + confirmation_url e bloqueiam seus
    dependentes até o ACT do usuário. Outcomes parciais são
    reportados honestamente — sem atomicidade global implícita.
    """
    operations = batch.get("operations") or []
    if not operations:
        return _err(
            "batch.operations obrigatório.",
            error_code="validation_error",
        )
    ops = [
        {
            "capability": o.get("capability")
            or _capability_id(
                str(o.get("entity", "")).strip().lower(),
                str(o.get("action", "")).strip().lower(),
            ),
            "params": _clean(o.get("params") or {}),
            **(
                {"depends_on": o["depends_on"]}
                if o.get("depends_on") is not None
                else {}
            ),
        }
        for o in operations
    ]
    gw = _governed_writes()
    orch = _batch_orchestrator()
    try:
        plan = orch.plan_batch(operations=ops, actor_sub=actor_sub)
    except ChecklistDomainError as exc:
        return _domain_fail(exc)
    table = gw._capability_table()
    state_by_index: dict[int, str] = {}
    outcomes: list[dict] = []
    for op in plan["operations"]:
        idx = op["index"]
        capability = op["capability"]
        entry = {
            "index": idx,
            "capability": capability,
            "resource_type": op.get("resource_type"),
        }
        if op["status"] != "viable":
            state_by_index[idx] = "blocked"
            outcomes.append(
                entry | {
                    "status": "blocked",
                    "reason": op.get("block_reason") or "not_viable",
                }
            )
            continue
        waiting = [
            d
            for d in op.get("depends_on", [])
            if state_by_index.get(d) != "executed"
        ]
        if waiting:
            state_by_index[idx] = "blocked"
            outcomes.append(
                entry | {
                    "status": "blocked",
                    "reason": "dependency_not_executed",
                    "depends_on": waiting,
                }
            )
            continue
        spec = table.get(capability)
        if spec is not None and spec.get("direct"):
            try:
                result = gw.execute_direct(
                    capability=capability,
                    params=op["params"],
                    actor_sub=actor_sub,
                )
            except ChecklistDomainError as exc:
                state_by_index[idx] = "failed"
                outcomes.append(
                    entry | {
                        "status": "failed",
                        "error_code": getattr(exc, "code", "error"),
                        "message": str(exc),
                    }
                )
                continue
            state_by_index[idx] = "executed"
            outcomes.append(entry | {"status": "executed",
                                     "result": result})
            continue
        # Governada — PREPARE selado + URL de consentimento; o ACT
        # posterior revalida ator/escopo/estado como sempre.
        try:
            prepared = gw.prepare(
                capability=capability,
                params=op["params"],
                actor_sub=actor_sub,
            )
        except ChecklistDomainError as exc:
            state_by_index[idx] = "failed"
            outcomes.append(
                entry | {
                    "status": "failed",
                    "error_code": getattr(exc, "code", "error"),
                    "message": str(exc),
                }
            )
            continue
        state_by_index[idx] = "pending"
        outcomes.append(
            entry | {
                "status": "pending_confirmation",
                "operation": prepared["operation"],
                "proposal_id": prepared["proposal_id"],
                "proposal_handle": prepared["proposal_handle"],
                "confirmation_url": prepared["confirmation_url"],
                "expires_at": prepared["expires_at"],
            }
        )
    counts = {"executed": 0, "pending_confirmation": 0,
              "blocked": 0, "failed": 0}
    for o in outcomes:
        counts[o["status"] if o["status"] in counts else "failed"] += 1
    return _ok(
        {
            "orchestration": "operations",
            "plan_hash": plan["plan_hash"],
            "summary": counts,
            "operations": outcomes,
            "note": (
                "Operações diretas já executadas; "
                "pending_confirmation exige consentimento no Portal "
                "antes do ACT. Não há transação global — outcomes são "
                "parciais por operação."
            ),
        }
    )


def _run_batch(
    batch: dict,
    actor_sub: str,
) -> CallToolResult:
    phase = (batch.get("phase") or "").strip().lower()
    # Fase omitida ou explícita "direct/immediate/run": orquestração
    # proporcional ao risco — diretas já, governadas preparam.
    if phase in ("", "direct", "immediate", "run"):
        return _run_operations(batch, actor_sub)
    orch = _batch_orchestrator()
    try:
        if phase == "prepare":
            operations = batch.get("operations") or []
            ops = [
                {
                    "capability": o.get("capability")
                    or _capability_id(
                        str(o.get("entity", "")).strip().lower(),
                        str(o.get("action", "")).strip().lower(),
                    ),
                    "params": _clean(o.get("params") or {}),
                    **(
                        {"depends_on": o["depends_on"]}
                        if o.get("depends_on") is not None
                        else {}
                    ),
                }
                for o in operations
            ]
            return _ok(
                orch.prepare_batch(operations=ops, actor_sub=actor_sub)
            )
        handle = batch.get("batch_handle") or batch.get("handle")
        if not handle:
            return _err(
                "batch_handle obrigatório nesta fase.",
                error_code="validation_error",
            )
        if phase == "confirm":
            return _ok(
                orch.confirm_batch(
                    handle=handle,
                    actor_sub=actor_sub,
                    plan_hash=batch.get("plan_hash"),
                )
            )
        if phase in ("execute", "commit", "act"):
            return _ok(
                orch.execute_batch(
                    handle=handle,
                    actor_sub=actor_sub,
                    resume=bool(batch.get("resume")),
                )
            )
        return _err(
            f"batch.phase inválida: {phase!r} — "
            "prepare|confirm|execute.",
            error_code="validation_error",
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc)


def _governed_dispatch(
    entity: str | None,
    action: str | None,
    params: dict | None,
    phase: str | None,
    proposal_handle: str | None,
    idempotency_key: str | None,
    expected_revision: Any,
    batch: dict | None,
    *,
    destructive_only: bool,
    tool_name: str,
) -> CallToolResult:
    _request, user = _user_and_access()
    actor = actor_subject(user)

    if batch:
        return _run_batch(batch, actor)

    phase_norm = (phase or "").strip().lower()
    if phase_norm in ("commit", "act"):
        if not proposal_handle:
            return _err(
                "proposal_handle obrigatório em phase=commit.",
                error_code="validation_error",
            )
        return _commit_single(proposal_handle, actor)

    ent = (entity or "").strip().lower()
    act = (action or "").strip().lower()
    spec = _governed_spec(ent, act)
    if spec is None:
        return _err(
            f"Operação governada desconhecida: {ent}.{act} — consulte "
            "get_context(topic='catalog').",
            status_code=404,
            error_code="not_implemented",
        )
    if destructive_only and not spec.get("destructive"):
        return _err(
            f"{ent}.{act} não é operação destrutiva — use execute.",
            error_code="validation_error",
        )
    payload = _clean(params or {})
    if idempotency_key is not None:
        payload.setdefault("idempotency_key", idempotency_key)
    if expected_revision is not None:
        payload.setdefault("expected_revision", expected_revision)
    # Paridade com o contrato legado: valida presença dos required;
    # parâmetros opcionais seguem selados no payload (o execute
    # tipado da capability valida o restante).
    missing = [
        p for p in spec["required_params"] if payload.get(p) is None
    ]
    if missing:
        return _err(
            f"Parâmetros obrigatórios ausentes: {missing}.",
            error_code="validation_error",
            data={"missing": missing, "capability": f"{ent}.{act}"},
        )
    # Política proporcional ao risco (doc 126): DIRECT_ALLOWED
    # executa imediatamente por default e em phase=direct; operações
    # sem o marcador seguem PREPARE → consentimento Portal → ACT.
    if phase_norm in ("", "direct", "immediate", "run"):
        if spec.get("direct") and not destructive_only:
            return _direct_single(ent, act, payload, actor)
        if phase_norm == "":
            return _prepare_single(ent, act, payload, actor)
        return _err(
            f"{ent}.{act} exige confirmação humana verificável — "
            "use phase=prepare e o ACT com consentimento registrado "
            "no Portal (doc 126).",
            status_code=409,
            error_code="consent_required",
        )
    if phase_norm == "prepare":
        return _prepare_single(ent, act, payload, actor)
    return _err(
        f"phase inválida: {phase!r} — direct|prepare|commit.",
        error_code="validation_error",
    )


def tool_execute(
    entity: str | None = None,
    action: str | None = None,
    params: dict | None = None,
    phase: str | None = None,
    proposal_handle: str | None = None,
    idempotency_key: str | None = None,
    expected_revision: int | None = None,
    batch: dict | None = None,
) -> CallToolResult:
    return _governed_dispatch(
        entity,
        action,
        params,
        phase,
        proposal_handle,
        idempotency_key,
        expected_revision,
        batch,
        destructive_only=False,
        tool_name="execute",
    )


def tool_delete(
    entity: str | None = None,
    action: str | None = None,
    target_ref: str | None = None,
    params: dict | None = None,
    phase: str | None = None,
    proposal_handle: str | None = None,
    expected_revision: int | None = None,
) -> CallToolResult:
    payload = dict(params or {})
    if target_ref is not None:
        # ref → parâmetro-chave da capability (document_id/item_key/…)
        spec = _governed_spec(
            (entity or "").strip().lower(),
            (action or "").strip().lower(),
        )
        if spec is not None:
            key_params = [
                p for p in spec["required_params"]
                if p.endswith("_id") or p == "code"
            ]
            if len(key_params) == 1:
                payload.setdefault(key_params[0], target_ref)
    return _governed_dispatch(
        entity,
        action,
        payload,
        phase,
        proposal_handle,
        None,
        expected_revision,
        None,
        destructive_only=True,
        tool_name="delete",
    )
