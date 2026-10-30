"""EVA semantic MCP bridge — six stable tools over a typed registry.

EVA.MCP.SEMANTIC.R1 (plano mestre 54): the public surface is exactly
six tools — ``get_context``, ``read``, ``analyze``, ``knowledge``,
``execute``, ``delete``. Every call dispatches on ``(entity, action)``
from the allowlist registry; no URL, HTTP method, SQL or model-supplied
handler names. All handlers delegate to the same official use cases as
the legacy tools — parity, not reimplementation.

Governance model:
- ``read``/``analyze``/``knowledge`` — human principal + live Core
  AuthZ (``engineering.access``), same gate as REST routes.
- ``execute`` — risk-tiered, fail-closed: ``ENG_EVA_ACT_ENABLED`` gates
  the write tier (create/update run directly when the request is
  unequivocal); destructive ``nonconformity.import`` additionally
  requires ``ENG_EVA_ACT_IMPORT_ENABLED`` + prepare → sealed proposal
  → verifiable human confirmation (MCP elicitation) → commit.
- ``delete`` — destructive; requires ``ENG_EVA_ACT_DELETE_ENABLED`` on
  top of the master flag; phase=prepare seals a server-side proposal
  (actor-bound, TTL, single-use, HMAC handle); phase=commit executes
  only after verifiable human confirmation via MCP elicitation —
  ``confirmed=true`` or mere proposal_ref possession is never proof.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from mcp.types import CallToolResult
from pydantic import BaseModel, Field

from delpi_mcp.errors import mcp_tool_result
from engineering_app.application.eva.agent_intelligence_service import (
    EvaAgentIntelligenceService,
)
from engineering_app.application.eva.proposal_store import (
    EvaProposalError,
    fingerprint,
    get_proposal_store,
    load_valid_proposal,
    seal_proposal,
)
from engineering_app.application.eva.semantic_registry import (
    PLANNED_SEMANTIC_ACTIONS,
    SEMANTIC_ACTIONS,
    SEMANTIC_CATALOG_VERSION,
    SEMANTIC_TOOL_NAMES,
    actions_for_entity,
    entities_summary,
    semantic_action,
)
from engineering_app.application.models.lmp import LmpQuery
from engineering_app.composition import nc_composer
from engineering_app.composition.lmp_composer import (
    build_delegated_auxiliary_source,
    build_get_lmp_summary_use_case,
)
from engineering_app.interface.mcp import tool_bridge as bridge
from engineering_app.interface.mcp.branding import EVA_FULL_NAME
from engineering_app.interface.mcp.constants import SEMANTIC_TOOL_CLASS

logger = logging.getLogger(__name__)


def _ok(data: Any, message: str = "ok") -> CallToolResult:
    return mcp_tool_result(
        {"success": True, "message": message, "data": data}, is_error=False
    )


def _err(
    message: str,
    *,
    status_code: int = 400,
    code: str = "validation",
    data: dict | None = None,
) -> CallToolResult:
    err = dict(data or {})
    err.setdefault("error_kind", code)
    return mcp_tool_result(
        {
            "success": False,
            "message": message,
            "status_code": status_code,
            "error_code": code,
            "data": err,
        },
        is_error=True,
    )


def _wrap(entity: str, action: str, result: CallToolResult) -> CallToolResult:
    """Semantic envelope — action/entity stamped on top of the official
    result payload; legacy error/success semantics preserved."""
    payload = dict(getattr(result, "structured_content", None) or {})
    payload.setdefault("entity", entity)
    payload.setdefault("action", action)
    return mcp_tool_result(payload, is_error=bool(result.is_error))


def _handle_error(exc: Exception) -> CallToolResult:
    if isinstance(exc, EvaProposalError):
        return _err(
            str(exc),
            status_code=exc.status_code,
            code=exc.code,
            data={"error_kind": exc.code, **exc.detail},
        )
    return bridge.handle_tool_error(exc)


class _DestructiveConfirmation(BaseModel):
    """MCP elicitation schema — verifiable human confirmation.

    Only primitives are allowed by the spec; ``target_echo`` forces the
    human to retype the exact identifier being destroyed, binding the
    confirmation to this proposal (never a generic click-through).
    """

    confirm: bool = Field(
        description="Confirma a operação destrutiva descrita?"
    )
    target_echo: str = Field(
        description="Redigite o identificador exibido para confirmar."
    )


async def _require_human_confirmation(
    ctx: Any,
    *,
    expected_echo: str,
    summary: str,
    proposal_id: str,
) -> CallToolResult | None:
    """Verifiable human confirmation via MCP elicitation (form mode).

    Possession of ``proposal_ref`` proves the sealed handle; the
    elicitation proves that a human saw target + impact and confirmed
    inside the MCP client during THIS request. When the consumer
    offers no verifiable channel the operation stays blocked honestly
    (``confirmation_unavailable``) — never a silent fallback.
    """
    elicit = getattr(ctx, "elicit", None)
    if not callable(elicit):
        return _err(
            "Confirmação humana verificável indisponível: este "
            "consumidor MCP não suporta elicitation — a operação "
            "permanece bloqueada até um mecanismo aprovado.",
            status_code=403,
            code="confirmation_unavailable",
            data={"proposal_id": proposal_id},
        )
    try:
        result = await elicit(
            message=(
                f"{summary}\nPara confirmar, marque 'confirm' e "
                f"redigite exatamente: {expected_echo}"
            ),
            schema=_DestructiveConfirmation,
        )
    except Exception:
        logger.warning(
            "eva_mcp_elicit_unsupported", extra={"proposal_id": proposal_id}
        )
        return _err(
            "Confirmação humana verificável indisponível: elicitation "
            "não suportada/aceita pelo consumidor — operação bloqueada.",
            status_code=403,
            code="confirmation_unavailable",
            data={"proposal_id": proposal_id},
        )
    action = getattr(result, "action", None)
    content = getattr(result, "content", None) or getattr(
        result, "data", None
    )
    confirmed = action == "accept" and bool(
        getattr(content, "confirm", False)
    ) and str(getattr(content, "target_echo", "") or "").strip() == (
        expected_echo
    )
    if not confirmed:
        return _err(
            "Operação destrutiva não confirmada pelo humano "
            f"(elicitation action={action!r}) — nada foi alterado; a "
            "proposta segue válida para nova tentativa.",
            status_code=403,
            code="confirmation_declined",
            data={"proposal_id": proposal_id},
        )
    logger.info(
        "eva_mcp_destructive_confirmed",
        extra={"proposal_id": proposal_id, "target_echo": expected_echo},
    )
    return None


def _resolve(
    entity: str | None, action: str | None, *, tool: str
) -> tuple[Any | None, CallToolResult | None]:
    """Registry allowlist resolution — honest error, never dynamic."""
    ent = (entity or "").strip().lower()
    act = (action or "").strip().lower()
    if not ent or not act:
        return None, _err(
            "entity e action são obrigatórios.",
            code="validation",
            data={
                "allowed_entities": sorted(
                    {a.entity for a in SEMANTIC_ACTIONS}
                )
            },
        )
    entry = semantic_action(ent, act)
    if entry is None or entry.status != "proven":
        allowed = sorted(a.action for a in actions_for_entity(ent))
        return None, _err(
            f"Ação '{ent}.{act}' não implementada nesta superfície.",
            status_code=400 if entry is None else 501,
            code="not_implemented",
            data={
                "entity": ent,
                "action": act,
                "allowed_actions": allowed,
                "status": entry.status if entry else "unknown",
            },
        )
    if entry.tool != tool:
        return None, _err(
            f"Ação '{ent}.{act}' pertence à tool '{entry.tool}'.",
            code="validation",
            data={"expected_tool": entry.tool},
        )
    return entry, None


def _filters(
    entry, filters: dict | None, pagination: dict | None
) -> tuple[dict[str, Any], CallToolResult | None]:
    """Strict arg mapping: ref → ref_arg; filters → declared fields;
    unknown keys are rejected, never silently dropped."""
    merged: dict[str, Any] = {}
    for key, value in (filters or {}).items():
        if key not in entry.fields:
            return {}, _err(
                f"Campo '{key}' não é filtro de {entry.capability}.",
                code="validation",
                data={"allowed_fields": list(entry.fields)},
            )
        merged[key] = value
    for key, value in (pagination or {}).items():
        if key not in {"page", "page_size"} or not entry.paginated:
            return {}, _err(
                f"Paginação não suportada por {entry.capability}.",
                code="validation",
            )
        merged[key] = value
    return merged, None


# --- get_context ----------------------------------------------------------


def tool_get_context(
    *,
    topic: str | None = None,
    entity: str | None = None,
    selected_ref: str | None = None,
) -> CallToolResult:
    """Semantic discovery — capabilities on demand, never AuthZ."""
    try:
        bridge._require_engineering_human()
        actions = SEMANTIC_ACTIONS
        ent = (entity or "").strip().lower()
        top = (topic or "").strip().lower()
        if ent:
            scoped = actions_for_entity(ent)
            if not scoped:
                return _err(
                    f"Entidade '{ent}' desconhecida.",
                    code="validation",
                    data={
                        "allowed_entities": sorted(
                            {a.entity for a in SEMANTIC_ACTIONS}
                        )
                    },
                )
            actions = scoped
        elif top:
            actions = tuple(
                a
                for a in actions
                if top in a.entity or top in a.action or top in a.description.lower()
            )
        data: dict[str, Any] = {
            "assistant": EVA_FULL_NAME,
            "catalog_version": SEMANTIC_CATALOG_VERSION,
            "semantic_tools": [
                {
                    "name": name,
                    "class": SEMANTIC_TOOL_CLASS[name],
                    "annotations": {
                        "readOnlyHint": SEMANTIC_TOOL_CLASS[name]
                        in {"DISCOVERY", "READ", "ANALYSIS"},
                        "destructiveHint": name == "delete",
                    },
                }
                for name in SEMANTIC_TOOL_NAMES
            ],
            "entities": entities_summary(),
            "actions": [a.public_dict() for a in actions],
            "act_enabled": bridge._eva_act_enabled(),
            "act_tiers": {
                "write": bridge._eva_act_enabled(),
                "delete": bridge._eva_act_delete_enabled(),
                "import": bridge._eva_act_import_enabled(),
            },
            "act_flags": {
                "write": bridge.EVA_ACT_ENV_FLAG,
                "delete": bridge.EVA_ACT_DELETE_ENV_FLAG,
                "import": bridge.EVA_ACT_IMPORT_ENV_FLAG,
            },
            "confirmation_model": {
                "read_analyze_knowledge": "executam imediatamente.",
                "execute_moderate": (
                    "CREATE/UPDATE diretos quando a solicitação é "
                    "inequívoca e autorizada; phase=prepare valida sem "
                    "efeitos."
                ),
                "execute_destructive": (
                    "nonconformity.import exige phase=prepare → proposta "
                    "selada → confirmação humana verificável "
                    "(elicitation) → phase=commit com proposal_ref."
                ),
                "delete": (
                    "Sempre prepare → proposta selada (ator, alvo, TTL, "
                    "uso único) → confirmação humana verificável via "
                    "MCP elicitation → commit com proposal_ref — "
                    "confirmed=true ou posse do ref não são prova."
                ),
            },
            "selected_ref": selected_ref,
            "legacy_surface": {
                "status": "deprecated",
                "note": (
                    "Tools legadas permanecem ativas durante a migração "
                    "— novos consumidores devem usar a superfície "
                    "semântica."
                ),
            },
            "agent_directives": EvaAgentIntelligenceService.agent_directives(),
            "planned_actions": list(PLANNED_SEMANTIC_ACTIONS),
            "required_permission": bridge.ENGINEERING_ACCESS,
            "notes": [
                "Contexto não concede permissão — a autorização efetiva "
                "é verificada pela Core a cada chamada.",
                "Estados honestos: unavailable/forbidden indicam falha "
                "ou falta de autorização na fonte — nunca 'sem dados'.",
            ],
        }
        return _ok(data, "Contexto semântico da EVA.")
    except Exception as exc:
        return _handle_error(exc)


# --- read -----------------------------------------------------------------


async def tool_read(
    *,
    entity: str,
    action: str,
    ref: str | None = None,
    filters: dict | None = None,
    pagination: dict | None = None,
    projection: list | None = None,
) -> CallToolResult:
    """Semantic READ dispatch — typed (entity, action) only."""
    entry, error = _resolve(entity, action, tool="read")
    if error:
        return error
    args, error = _filters(entry, filters, pagination)
    if error:
        return error
    if entry.ref_arg:
        if not (ref or "").strip():
            return _err(
                f"ref ({entry.ref_arg}) é obrigatório para "
                f"{entry.capability}.",
                code="validation",
            )
        args[entry.ref_arg] = ref.strip()
    try:
        handler = _READ_DISPATCH[(entry.entity, entry.action)]
        result = await handler(args)
        if projection and isinstance(projection, list):
            payload = dict(getattr(result, "structured_content", None) or {})
            inner = payload.get("data")
            if isinstance(inner, dict):
                keep = {str(k) for k in projection}
                payload["data"] = {
                    k: v for k, v in inner.items() if k in keep
                }
                return mcp_tool_result(
                    payload, is_error=bool(result.is_error)
                )
        return _wrap(entry.entity, entry.action, result)
    except Exception as exc:
        return _handle_error(exc)


_READ_DISPATCH = {
    ("engineering", "home"): lambda a: bridge.tool_get_engineering_home(),
    ("engineering", "overview"): (
        lambda a: bridge.tool_get_engineering_overview(**a)
    ),
    ("lmp", "list"): lambda a: bridge.tool_list_lmps(**a),
    ("lmp", "summary"): lambda a: bridge.tool_get_lmp_summary(**a),
    ("lmp", "detail"): lambda a: bridge.tool_get_lmp_detail(**a),
    ("lmp", "history_events"): (
        lambda a: bridge.tool_get_lmp_history(view="events", **a)
    ),
    ("lmp", "history_flow"): (
        lambda a: bridge.tool_get_lmp_history(view="flow", **a)
    ),
    ("lmp", "goal_context"): (
        lambda a: bridge.tool_get_lmp_goal_context(**a)
    ),
    ("lmp", "department_idd"): (
        lambda a: bridge.tool_get_lmp_department_idd(**a)
    ),
    ("lmp", "nc_streak"): lambda a: bridge.tool_get_lmp_nc_streak(),
    ("product", "structure"): (
        lambda a: bridge.tool_get_product_structure(**a)
    ),
    ("nonconformity", "search"): (
        lambda a: bridge.tool_search_nonconformities(**a)
    ),
    ("nonconformity", "detail"): (
        lambda a: bridge.tool_get_nonconformity(**a)
    ),
    ("nonconformity", "history"): (
        lambda a: bridge.tool_get_nonconformity_history(**a)
    ),
    ("nonconformity", "indicators"): (
        lambda a: bridge.tool_get_nonconformity_indicators()
    ),
    ("nonconformity", "tags"): (
        lambda a: bridge.tool_get_nonconformity_tags()
    ),
    ("nonconformity", "context"): (
        lambda a: bridge.tool_get_nonconformity_context(**a)
    ),
    ("nonconformity", "export"): (
        lambda a: bridge.tool_export_nonconformities()
    ),
}

# --- analyze --------------------------------------------------------------


async def tool_analyze(
    *,
    analysis_type: str,
    subject_refs: list | None = None,
    question: str | None = None,
    parameters: dict | None = None,
) -> CallToolResult:
    """Semantic ANALYZE — grounded computations over official facts."""
    try:
        context = bridge._require_engineering_human()
        kind = (analysis_type or "").strip().lower()
        params = dict(parameters or {})
        if kind == "nonconformity.recurrence":
            return await _analyze_nc_recurrence(context, params, question)
        if kind == "lmp.performance":
            return await _analyze_lmp_performance(context, params, question)
        return _err(
            f"analysis_type '{kind}' não implementado.",
            status_code=501,
            code="not_implemented",
            data={
                "available": [
                    "nonconformity.recurrence",
                    "lmp.performance",
                ]
            },
        )
    except Exception as exc:
        return _handle_error(exc)


_NC_GROUP_BY = {"product_code", "problem_tag", "status", "customer_name"}


async def _analyze_nc_recurrence(
    context, params: dict, question: str | None
) -> CallToolResult:
    """Verifiable recurrence counts over a bounded official sample."""
    group_by = str(params.pop("group_by", "problem_tag")).strip()
    if group_by not in _NC_GROUP_BY:
        return _err(
            f"group_by inválido — use {sorted(_NC_GROUP_BY)}.",
            code="validation",
        )
    filters = {
        k: v
        for k, v in params.items()
        if k
        in {
            "status", "sale_number", "lmp_number", "customer_name",
            "product_code", "problem_tag", "date_start", "date_end",
        }
    }
    result = await nc_composer.build_list_nonconformities_use_case().execute(
        page=1, page_size=200, **filters
    )
    items = result.get("items", [])
    total = result.get("total", len(items))
    counts: dict[str, int] = {}
    for record in items:
        value = record.get(group_by)
        if isinstance(value, list):
            keys = [str(v) for v in value] or ["(vazio)"]
        else:
            keys = [str(value) if value else "(vazio)"]
        for key in keys:
            counts[key] = counts.get(key, 0) + 1
    ranking = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    return _ok(
        {
            "analysis_type": "nonconformity.recurrence",
            "question": question,
            "method": (
                f"Agrupamento de {len(items)} registros oficiais por "
                f"'{group_by}' — contagem verificável."
            ),
            "data_class": "CALCULATED",
            "group_by": group_by,
            "groups": [{"value": k, "count": v} for k, v in ranking],
            "coverage": {
                "analyzed": len(items),
                "total": total,
                "complete": len(items) >= total,
                "note": (
                    "Amostra limitada a 200 registros — para cobertura "
                    "total use read(nonconformity.export)."
                )
                if len(items) < total
                else "Cobertura completa do período/filtros.",
            },
            "filters_applied": filters,
            "source": "engineering-api official nonconformity records",
            "provenance": "OBSERVED records → CALCULATED aggregation",
        },
        "Análise de recorrência de não conformidades.",
    )


async def _analyze_lmp_performance(
    context, params: dict, question: str | None
) -> CallToolResult:
    """LMP performance briefing — OBSERVED facts, CALCULATED deltas."""
    period = {
        k: v.strip() if isinstance(v, str) else v
        for k, v in params.items()
        if k in {"start_date", "end_date", "branch"}
    }
    error = bridge._validate_period(
        period.get("start_date"), period.get("end_date")
    )
    if error:
        return _err(
            error,
            status_code=400,
            code="validation",
            data={"error_kind": "validation"},
        )
    ctx = bridge._source_context(context)
    query = LmpQuery(**period)
    summary = await build_get_lmp_summary_use_case().execute(ctx, query)
    auxiliary = build_delegated_auxiliary_source()
    goal_context = await auxiliary.fetch_goal_context(
        ctx,
        start_date=period.get("start_date"),
        end_date=period.get("end_date"),
        branch=period.get("branch"),
    )
    streak = await auxiliary.fetch_nc_streak(ctx)
    facts = []
    for name, payload in (
        ("lmp_summary", summary),
        ("goal_context", goal_context),
        ("nc_streak", streak),
    ):
        status = (payload or {}).get("status", "available")
        facts.append(
            {
                "source": name,
                "status": status,
                "data_class": "OBSERVED" if status == "available" else "UNKNOWN",
                "data": payload,
            }
        )
    return _ok(
        {
            "analysis_type": "lmp.performance",
            "question": question,
            "method": (
                "Composição de agregados oficiais — nenhum indicador é "
                "recalculado; comparações com meta são marcadas "
                "CALCULATED."
            ),
            "facts": facts,
            "interpretation_notes": [
                "Metas existem apenas em lmp_on_time e "
                "transforma_gross_savings.",
                "Status unavailable/forbidden = fonte indisponível ou "
                "sem autorização — não significa ausência de dados.",
            ],
            "filters_applied": period,
            "provenance": "OBSERVED official aggregates only",
        },
        "Análise de desempenho de LMPs.",
    )


# --- knowledge --------------------------------------------------------------


_KNOWLEDGE_PATH = (
    Path(__file__).resolve().parents[2]
    / "content"
    / "eva_engineering_knowledge.json"
)
_KNOWLEDGE_DOC: dict[str, Any] | None = None


def _knowledge_document() -> dict[str, Any]:
    global _KNOWLEDGE_DOC
    if _KNOWLEDGE_DOC is None:
        try:
            _KNOWLEDGE_DOC = json.loads(
                _KNOWLEDGE_PATH.read_text(encoding="utf-8")
            )
        except Exception:
            _KNOWLEDGE_DOC = {"version": "unknown", "topics": {}}
    return _KNOWLEDGE_DOC


def tool_knowledge(
    *,
    topic: str,
    task: str | None = None,
    query: str | None = None,
) -> CallToolResult:
    """Versioned owner-authorized Engineering guidance."""
    try:
        bridge._require_engineering_human()
        key = (topic or "").strip().lower()
        doc = _knowledge_document()
        entry = (doc.get("topics") or {}).get(key)
        if entry is None:
            planned = {
                t["topic"]: t for t in doc.get("planned_topics", [])
            }
            if key in planned:
                return _err(
                    f"Tópico '{key}' ainda não possui corpus autorizado.",
                    status_code=501,
                    code="not_implemented",
                    data={"topic": planned[key]},
                )
            return _err(
                f"Tópico '{key}' desconhecido.",
                status_code=404,
                code="not_found",
                data={
                    "available_topics": sorted(
                        (doc.get("topics") or {}).keys()
                    ),
                    "planned_topics": sorted(planned),
                },
            )
        return _ok(
            {
                "topic": key,
                "task": task,
                "query": query,
                "knowledge_version": doc.get("version"),
                "owner": doc.get("owner"),
                **entry,
            },
            "Conhecimento técnico versionado de Engenharia.",
        )
    except Exception as exc:
        return _handle_error(exc)


# --- execute ----------------------------------------------------------------


async def tool_execute(
    *,
    entity: str,
    action: str,
    target_ref: str | None = None,
    payload: dict | None = None,
    changes: dict | None = None,
    idempotency_key: str | None = None,
    expected_version: str | None = None,
    proposal_ref: str | None = None,
    phase: str | None = None,
    ctx: Any = None,
) -> CallToolResult:
    """Semantic ACT — governed mutations via official use cases."""
    entry, error = _resolve(entity, action, tool="execute")
    if error:
        return error
    phase_n = (phase or "act").strip().lower()
    if phase_n not in entry.phases:
        return _err(
            f"phase inválida para {entry.capability} — "
            f"use {list(entry.phases)}.",
            code="validation",
            data={"allowed_phases": list(entry.phases)},
        )
    try:
        context = bridge._require_engineering_human()
        bridge._require_eva_act()
        handler = _EXECUTE_DISPATCH[(entry.entity, entry.action)]
        return await handler(
            context, entry, phase_n,
            target_ref=target_ref,
            payload=payload,
            changes=changes,
            idempotency_key=idempotency_key,
            expected_version=expected_version,
            proposal_ref=proposal_ref,
            ctx=ctx,
        )
    except Exception as exc:
        return _handle_error(exc)


async def _exec_nc_create(context, entry, phase, *, payload, **_kw):
    if phase == "prepare":
        result = await bridge.tool_prepare_nonconformity_mutation(
            operation="create", payload=payload or {}
        )
        return _wrap(entry.entity, entry.action, result)
    data = await bridge._create_nc_record(
        context, payload=payload or {}, idempotency_key=_kw.get("idempotency_key")
    )
    return _ok(
        {"entity": entry.entity, "action": entry.action, **data},
        "Não conformidade criada com sucesso.",
    )


async def _exec_nc_update(context, entry, phase, *, target_ref, changes, **_kw):
    if not (target_ref or "").strip():
        return _err(
            "target_ref (record_id) é obrigatório para update.",
            code="validation",
        )
    if phase == "prepare":
        result = await bridge.tool_prepare_nonconformity_mutation(
            operation="update",
            record_id=target_ref.strip(),
            payload=changes or {},
        )
        return _wrap(entry.entity, entry.action, result)
    data = await bridge._update_nc_record(
        context,
        record_id=target_ref.strip(),
        changes=changes or {},
        expected_updated_at=_kw.get("expected_version"),
    )
    return _ok(
        {"entity": entry.entity, "action": entry.action, **data},
        "Não conformidade atualizada com sucesso.",
    )


async def _exec_nc_import(context, entry, phase, *, payload, **_kw):
    items = (payload or {}).get("items")
    if phase == "prepare":
        if not isinstance(items, list) or not items:
            return _err(
                "items é obrigatório (lista de não conformidades) em "
                "payload.items.",
                code="validation",
            )
        report = await bridge._import_nc_records(
            context, items=items, dry_run=True, confirm_replace=False
        )
        proposal, handle = seal_proposal(
            capability=entry.capability,
            actor_id=str(getattr(context.user, "id", "") or ""),
            target_ref=None,
            change={"items": items},
            impact={
                "operation": "import_replace_all",
                "dry_run_report": report,
                "items_count": len(items),
            },
            validation_result={"dry_run": report},
            expected_postcondition={
                "check": "import_report",
                "note": "created/deleted/skipped/errors oficiais.",
            },
            meta={"items": items},
        )
        return _ok(
            {
                "entity": entry.entity,
                "action": entry.action,
                "phase": "prepare",
                "proposal_ref": handle,
                "proposal": proposal.to_public_dict(),
            },
            "Dry-run de importação concluído — proposta selada aguardando "
            "confirmação humana (phase=commit + proposal_ref).",
        )
    # commit — sealed proposal only; env gate still applies downstream.
    handle = (_kw.get("proposal_ref") or "").strip()
    if not handle:
        raise EvaProposalError(
            "proposal_ref é obrigatório para phase=commit.",
            code="proposal_required",
            status_code=400,
        )
    proposal = load_valid_proposal(
        proposal_handle=handle,
        actor_id=str(getattr(context.user, "id", "") or ""),
        expected_capability=entry.capability,
    )
    # The sealed change fingerprint protects the exact item list — the
    # model cannot swap items between prepare and commit.
    if isinstance(items, list) and items and fingerprint(
        {"items": items}
    ) != proposal.change_fingerprint:
        raise EvaProposalError(
            "Itens divergem da proposta selada — prepare novamente.",
            code="proposal_mismatch",
            status_code=409,
        )
    import_items = _unseal_items(
        proposal, items if isinstance(items, list) and items else None
    )
    # Tier import — replace-all exige flag específica além do master.
    bridge._require_eva_act("import")
    confirmation_error = await _require_human_confirmation(
        _kw.get("ctx"),
        expected_echo="import_replace_all",
        summary=(
            "Substituição TOTAL do dataset de não conformidades: "
            f"{len(import_items)} itens — irreversível e auditada."
        ),
        proposal_id=proposal.proposal_id,
    )
    if confirmation_error is not None:
        return confirmation_error
    get_proposal_store().consume(proposal.proposal_id)
    report = await bridge._import_nc_records(
        context,
        items=import_items,
        dry_run=False,
        confirm_replace=True,
    )
    return _ok(
        {
            "entity": entry.entity,
            "action": entry.action,
            "phase": "commit",
            "proposal_id": proposal.proposal_id,
            **report,
        },
        "Importação de não conformidades concluída (proposta "
        f"{proposal.proposal_id}).",
    )


def _unseal_items(proposal, fallback: list | None) -> list:
    """Exact items are recoverable from meta — sealed at prepare."""
    items = proposal.meta.get("items")
    if isinstance(items, list) and items:
        return items
    if fallback:
        return fallback
    raise EvaProposalError(
        "Itens da proposta indisponíveis — prepare novamente.",
        code="proposal_stale",
        status_code=409,
    )


_EXECUTE_DISPATCH = {
    ("nonconformity", "create"): _exec_nc_create,
    ("nonconformity", "update"): _exec_nc_update,
    ("nonconformity", "import"): _exec_nc_import,
}


# --- delete -----------------------------------------------------------------


async def tool_delete(
    *,
    entity: str,
    target_ref: str,
    proposal_ref: str | None = None,
    phase: str | None = None,
    ctx: Any = None,
) -> CallToolResult:
    """Semantic destructive ACT — sealed proposal, never direct."""
    entry, error = _resolve(entity, "delete", tool="delete")
    if error:
        return error
    phase_n = (phase or "prepare").strip().lower()
    if phase_n not in {"prepare", "commit"}:
        return _err(
            "phase inválida para delete — use prepare|commit.",
            code="validation",
        )
    try:
        context = bridge._require_engineering_human()
        bridge._require_eva_act("delete")
        ref = (target_ref or "").strip()
        if not ref:
            return _err("target_ref é obrigatório.", code="validation")
        if phase_n == "prepare":
            current = (
                await nc_composer.build_get_nonconformity_use_case().execute(
                    ref
                )
            )
            proposal, handle = seal_proposal(
                capability=entry.capability,
                actor_id=str(getattr(context.user, "id", "") or ""),
                target_ref=ref,
                change={"target_ref": ref},
                impact={
                    "operation": "hard_delete",
                    "irreversible": True,
                    "cascades": ["history"],
                    "record_summary": {
                        "sale_number": current.get("sale_number"),
                        "lmp_number": current.get("lmp_number"),
                        "status": current.get("status"),
                        "defect_description": current.get(
                            "defect_description"
                        ),
                    },
                },
                expected_postcondition={"check": "read_back_gone"},
            )
            return _ok(
                {
                    "entity": entry.entity,
                    "action": "delete",
                    "phase": "prepare",
                    "proposal_ref": handle,
                    "proposal": proposal.to_public_dict(),
                },
                "Proposta de exclusão selada — apresente o resumo ao "
                "usuário e execute phase=commit somente após "
                "autorização explícita.",
            )
        # commit
        handle = (proposal_ref or "").strip()
        if not handle:
            raise EvaProposalError(
                "proposal_ref é obrigatório para phase=commit.",
                code="proposal_required",
                status_code=400,
            )
        proposal = load_valid_proposal(
            proposal_handle=handle,
            actor_id=str(getattr(context.user, "id", "") or ""),
            expected_capability=entry.capability,
            expected_target_ref=ref,
        )
        # Posse do proposal_ref não é prova — exige confirmação humana
        # verificável via MCP elicitation dentro desta requisição.
        record = (proposal.impact or {}).get("record_summary") or {}
        confirmation_error = await _require_human_confirmation(
            ctx,
            expected_echo=ref,
            summary=(
                "Exclusão irreversível de não conformidade "
                f"{ref} (LMP {record.get('lmp_number')}, OV "
                f"{record.get('sale_number')}, status "
                f"{record.get('status')}): {record.get('defect_description')}"
            ),
            proposal_id=proposal.proposal_id,
        )
        if confirmation_error is not None:
            return confirmation_error
        get_proposal_store().consume(proposal.proposal_id)
        data = await bridge._delete_nc_record(context, record_id=ref)
        return _ok(
            {
                "entity": entry.entity,
                "action": "delete",
                "phase": "commit",
                "proposal_id": proposal.proposal_id,
                **data,
            },
            "Não conformidade excluída com sucesso.",
        )
    except Exception as exc:
        return _handle_error(exc)
