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

from mcp.types import CallToolResult, TextContent
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
import engineering_app.composition.drawing_composer  # noqa: F401
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
    result payload; legacy error/success semantics preserved.
    Non-text content items (e.g. EmbeddedResource with binary
    payloads) are preserved — the envelope only re-wraps the typed
    structured content."""
    payload = dict(getattr(result, "structured_content", None) or {})
    payload.setdefault("entity", entity)
    payload.setdefault("action", action)
    wrapped = mcp_tool_result(payload, is_error=bool(result.is_error))
    wrapped.content.extend(
        item for item in result.content if not isinstance(item, TextContent)
    )
    return wrapped


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
    except Exception as exc:
        logger.warning(
            "eva_mcp_elicit_unsupported",
            extra={"proposal_id": proposal_id, "error": repr(exc)},
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
                "status": "retired",
                "note": (
                    "As 23 tools legadas foram removidas do MCP — "
                    "todas as capacidades permanecem disponíveis "
                    "exclusivamente pelas seis tools semânticas."
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
    ("product", "search"): (
        lambda a: bridge.tool_search_products(**a)
    ),
    ("product", "detail"): (
        lambda a: bridge.tool_get_product_detail(**a)
    ),
    ("product", "structure"): (
        lambda a: bridge.tool_get_product_structure(**a)
    ),
    ("product", "where_used"): (
        lambda a: bridge.tool_get_product_parents(**a)
    ),
    ("product", "suppliers"): (
        lambda a: bridge.tool_get_product_suppliers(**a)
    ),
    ("product", "drawing"): (
        lambda a: bridge.tool_get_product_drawing(**a)
    ),
    ("product", "drawing_download"): (
        lambda a: bridge.tool_get_product_drawing_pdf(**a)
    ),
    ("product", "history"): (
        lambda a: bridge.tool_get_product_history(**a)
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


_ANALYZE_KINDS: frozenset[str] = frozenset(
    {
        "nonconformity.recurrence",
        "lmp.performance",
        "product.drawing_analysis",
        "product.drawing_benchmark",
        "product.drawing_understanding",
    }
)


def analysis_types() -> tuple[str, ...]:
    """Canonical closed vocabulary for ``analyze.analysis_type`` —
    single owner for dispatch, honest errors and the wire ``enum``."""
    return tuple(sorted(_ANALYZE_KINDS))


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
        if kind not in _ANALYZE_KINDS:
            return _err(
                f"analysis_type '{kind}' não implementado.",
                status_code=501,
                code="not_implemented",
                data={"available": sorted(_ANALYZE_KINDS)},
            )
        if kind == "nonconformity.recurrence":
            return await _analyze_nc_recurrence(context, params, question)
        if kind == "lmp.performance":
            return await _analyze_lmp_performance(context, params, question)
        if kind == "product.drawing_analysis":
            return await _analyze_product_drawing(context, params, question)
        if kind == "product.drawing_benchmark":
            return await _analyze_drawing_benchmark(context, params, question)
        if kind == "product.drawing_understanding":
            return await _analyze_drawing_understanding(
                context, params, question
            )
        # Unreachable: the _ANALYZE_KINDS gate above rejects unknown
        # kinds — kept as a fail-closed tail if the set ever drifts
        # from the dispatch chain.
        return _err(
            f"analysis_type '{kind}' não implementado.",
            status_code=501,
            code="not_implemented",
            data={"available": sorted(_ANALYZE_KINDS)},
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


async def _analyze_product_drawing(
    context, params: dict, question: str | None
) -> CallToolResult:
    """analyze(product.drawing_analysis) — desenho oficial × cadastro × BOM."""
    import os

    from engineering_app.application.drawing.drawing_analysis_service import (
        DrawingAnalysisError,
        analyze_product_drawing,
    )
    from engineering_app.domain.drawing.visual_observation import (
        VisualObservationError,
        parse_visual_observations,
    )

    code = str(params.get("product_code") or "").strip()
    if not code:
        return _err(
            "product_code obrigatório para product.drawing_analysis.",
            code="validation",
        )
    try:
        observations = parse_visual_observations(
            params.get("visual_observations")
        )
    except VisualObservationError as exc:
        return _err(
            str(exc),
            status_code=400,
            code="invalid_visual_observation",
        )
    scope_raw = params.get("scope")
    scope = (
        [str(s).strip() for s in scope_raw if str(s).strip()][:20]
        if isinstance(scope_raw, list)
        else None
    )
    ctx = bridge._source_context(context)
    understanding = params.get("understanding")
    if understanding is not None and not isinstance(understanding, dict):
        return _err(
            "understanding deve ser um objeto drawing_understanding.v1.",
            status_code=400,
            code="validation",
        )
    # R12.1 — composição legítima: understanding produzido pelo mesmo
    # caso de uso interno (sem handler→handler, sem reprocessar por
    # ocorrência) quando solicitado e flags habilitadas.
    _tokens: list[dict] | None = None
    if params.get("compose_understanding") and understanding is None:
        if (
            os.environ.get(_BENCHMARK_FLAG) != "true"
            or os.environ.get(_OCR_BENCHMARK_FLAG) != "true"
        ):
            return _err(
                "compose_understanding exige perfil visual "
                "experimental habilitado neste ambiente.",
                status_code=403,
                code="feature_disabled",
            )
        # DEC-VAL-030 — execução prolongada governada: a análise visual
        # integral de documentos multipágina excede o orçamento de uma
        # chamada MCP interativa (ClientDisconnect comprovado). O job
        # executa desacoplado; o consumidor consulta por job_id.
        from engineering_app.application.drawing.analysis_jobs import (
            analysis_job_store,
        )
        import asyncio as _aio
        import hashlib as _hl
        import json as _js

        # DEC-VAL-031 — identidade LÓGICA do owner: o subject do
        # usuário (Keycloak, estável entre renovações de token).
        # access_token NÃO é identidade — muda a cada chamada OAuth
        # e produzia 404 job_not_found no polling do ChatGPT.
        _ident_fp = _drawing_job_owner_fingerprint(ctx)
        _params_fp = _hl.sha256(
            _js.dumps(
                {
                    "code": code,
                    "scope": scope,
                    "obs": bool(observations),
                    "progressive": bool(
                        params.get("progressive_investigation")
                    ),
                },
                sort_keys=True,
                default=str,
            ).encode()
        ).hexdigest()[:20]
        _store = analysis_job_store()
        _job_id = params.get("job_id")
        if _job_id:
            job = _store.get_for_owner(str(_job_id), _ident_fp)
            if job is None:
                return _err(
                    "job_id não encontrado ou expirado.",
                    status_code=404,
                    code="job_not_found",
                )
            if job.status == "RUNNING":
                return _ok(
                    {
                        "analysis_type": "product.drawing_analysis",
                        "status": "RUNNING",
                        "job_id": job.job_id,
                        "retry": {
                            "analysis_type": "product.drawing_analysis",
                            "parameters": {
                                "product_code": code,
                                "compose_understanding": True,
                                "job_id": job.job_id,
                            },
                        },
                    },
                    "Análise visual em execução — consulte o job_id.",
                )
            if job.status == "FAILED":
                err = job.error or {}
                return _err(
                    err.get("message")
                    or "Execução da análise falhou.",
                    status_code=err.get("status_code", 500),
                    code=err.get("code") or "analysis_incomplete",
                )
            return _ok(
                job.result or {},
                "Análise técnica do desenho oficial do produto.",
            )
        job, created = _store.get_or_start(
            product_code=code,
            identity_fingerprint=_ident_fp,
            params_fingerprint=_params_fp,
        )
        if created:
            _ctx_snapshot = ctx
            _mcp_context = context  # contexto MCP cru — exigido por
            # _produce_drawing_understanding (ele resolve
            # _source_context internamente sobre .user/.authorization)

            async def _run_job() -> None:
                try:
                    # DEC-VAL-032 — leituras oficiais delegadas PRIMEIRO
                    # (credencial do usuário ainda válida); OCR depois —
                    # sem autenticação tardia. Evita `product.detail:
                    # forbidden` por token expirado no meio do job.
                    _src = bridge.build_delegated_auxiliary_source()
                    _pf = {
                        "detail_raw": await _src.fetch_product_detail(
                            _ctx_snapshot, code=code, view="engineering"
                        ),
                        "drawing_meta_raw": (
                            await _src.fetch_product_drawing(
                                _ctx_snapshot, code=code
                            )
                        ),
                        "pdf_result": (
                            await _src.fetch_product_drawing_pdf(
                                _ctx_snapshot, code=code
                            )
                        ),
                        "structure_raw": (
                            await _src.fetch_product_structure(
                                _ctx_snapshot,
                                code=code,
                                max_depth=6,
                                page_size=200,
                            )
                        ),
                    }
                    (
                        u,
                        _s,
                        best,
                        tokens,
                        pdf_bytes,
                    ) = await _produce_drawing_understanding(
                        _mcp_context, code
                    )
                    prog = None
                    if params.get("progressive_investigation") or True:
                        prog = {
                            "budget": {
                                "max_crops": 8,
                                "max_attempts_per_region": 2,
                                "max_dpi": 300,
                                "max_pixels": 4_000_000,
                            },
                        }
                        from engineering_app.infrastructure.extraction.pdfium_adapter import (  # noqa: E501
                            PdfiumExtractionAdapter,
                        )
                        from engineering_app.infrastructure.extraction.paddleocr_adapter import (  # noqa: E501
                            PaddleOcrAdapter,
                        )

                        prog.update(
                            {
                                "pdf_bytes": pdf_bytes,
                                "renderer": PdfiumExtractionAdapter(),
                                "ocr": PaddleOcrAdapter(),
                                "page": 1,
                                "reference_dpi": int(
                                    best.get("dpi") or 200
                                ),
                                "reference_dpi_by_page": (
                                    _render_dpi_by_page(best)
                                ),
                            }
                        )
                    report = await analyze_product_drawing(
                        code=code,
                        source=_src,
                        ctx=_ctx_snapshot,
                        visual_observations=observations or None,
                        scope=scope,
                        understanding=u,
                        progressive=prog,
                        drawing_tokens=tokens,
                        prefetched=_pf,
                    )
                    _store.complete(
                        job.job_id,
                        {
                            "analysis_type": "product.drawing_analysis",
                            "question": question,
                            "method": (
                                "Extração determinística + OCR visual "
                                "do PDF oficial + comparação com "
                                "cadastro e BOM oficiais — evidências "
                                "por página, nenhuma inferência "
                                "promovida a fato."
                            ),
                            "data_class": (
                                "OBSERVED|CALCULATED|INFERRED|UNKNOWN"
                            ),
                            "report": _compact_report_for_consumer(
                                report
                            ),
                            "provenance": (
                                "api-delpi product/drawing/structure "
                                "(identidade delegada) + extração "
                                "neutra engineering-api"
                            ),
                        },
                    )
                except DrawingAnalysisError as exc:
                    _store.fail(
                        job.job_id,
                        exc.code,
                        str(exc),
                        status_code=exc.status_code,
                    )
                except Exception as exc:  # noqa: BLE001 — job nunca vaza
                    _store.fail(
                        job.job_id,
                        "analysis_incomplete",
                        f"{type(exc).__name__}: {exc}",
                        status_code=500,
                    )

            _aio.create_task(_run_job())
        return _ok(  # noqa: E501
            {
                "analysis_type": "product.drawing_analysis",
                "status": "RUNNING",
                "job_id": job.job_id,
                "retry": {
                    "analysis_type": "product.drawing_analysis",
                    "parameters": {
                        "product_code": code,
                        "compose_understanding": True,
                        "job_id": job.job_id,
                    },
                },
                "note": (
                    "Análise visual integral em execução prolongada; "
                    "repita a chamada com o job_id retornado."
                ),
            },
            "Análise visual em execução — consulte o job_id.",
        )
    # R13 — investigação progressiva: busca contextual sempre ativa;
    # recorte direcionado via ports REAIS quando o fluxo produziu
    # understanding+PDF (compose) — CAPABILITY_UNAVAILABLE honesto senão.
    progressive = None
    if params.get("progressive_investigation") or params.get(
        "compose_understanding"
    ):
        progressive = {
            "budget": {"max_crops": 8, "max_attempts_per_region": 2,
                       "max_dpi": 300, "max_pixels": 4_000_000},
        }
        if understanding is not None:
            from engineering_app.infrastructure.extraction.pdfium_adapter import (  # noqa: E501
                PdfiumExtractionAdapter,
            )
            from engineering_app.infrastructure.extraction.paddleocr_adapter import (  # noqa: E501
                PaddleOcrAdapter,
            )

            progressive.update(
                {
                    "pdf_bytes": _pdf_bytes,
                    "renderer": PdfiumExtractionAdapter(),
                    "ocr": PaddleOcrAdapter(),
                    "page": 1,
                    "reference_dpi": int(_best.get("dpi") or 200),
                    "reference_dpi_by_page": _render_dpi_by_page(_best),
                }
            )
    try:
        report = await analyze_product_drawing(
            code=code,
            source=bridge.build_delegated_auxiliary_source(),
            ctx=ctx,
            visual_observations=observations or None,
            scope=scope,
            understanding=understanding,
            progressive=progressive,
            drawing_tokens=_tokens,
        )
    except DrawingAnalysisError as exc:
        return _err(
            str(exc),
            status_code=exc.status_code,
            code=exc.code,
        )
    return _ok(
        {
            "analysis_type": "product.drawing_analysis",
            "question": question,
            "method": (
                "Extração determinística da camada de texto do PDF "
                "oficial + comparação com cadastro e BOM oficiais — "
                "evidências por página, nenhuma inferência promovida a "
                "fato."
            ),
            "data_class": "OBSERVED|CALCULATED|INFERRED|UNKNOWN",
            "report": report,
            "provenance": (
                "api-delpi product/drawing/structure (identidade "
                "delegada) + extração neutra engineering-api"
            ),
        },
        "Análise técnica do desenho oficial do produto.",
    )


_HEAVY_RESULT_KEYS = frozenset(
    {
        "_tokens_sample",
        "_text_blob",
        "_graphic_primitives",
        "_graphic_primitives_by_page",
        "tokens",
        "tokens_sample",
        "token_sample",
        "ocr_tokens",
        "sampled_tokens",
    }
)


def _render_dpi_by_page(best: dict) -> dict[int, int]:
    """DPI de render por página do pipeline vencedor — o espaço de
    coordenadas px de tokens/células varia por folha (orçamento de
    pixels por página). ``None`` quando o provider não declara."""
    out: dict[int, int] = {}
    for p in (best or {}).get("pages") or []:
        dpi = (p.get("render") or {}).get("dpi")
        if p.get("page") and dpi:
            out[int(p["page"])] = int(dpi)
    return out


def _drawing_job_owner_fingerprint(ctx) -> str:
    """DEC-VAL-031 — fingerprint da identidade lógica do owner do job.

    Usa apenas o subject estável do usuário (``user_id`` do
    HomeSourceContext — derivado do principal autenticado). O
    access_token continua necessário para as chamadas delegadas
    (AuthN), mas sua renovação não pode invalidar a propriedade do
    job — token não é identidade.
    """
    import hashlib

    user_id = str(getattr(ctx, "user_id", "") or "").strip()
    return hashlib.sha256(f"uid:{user_id}".encode()).hexdigest()[:20]


def _compact_report_for_consumer(report):
    """RQ-VAL-032 — projeção compacta e auditável do relatório.

    Remove campos internos/pesados (amostras de tokens OCR, blobs,
    primitivas) preservando o contrato: cobertura, contagens, findings,
    limitações, códigos contextuais, proveniência e evidências tipadas.
    """
    if isinstance(report, dict):
        out = {}
        for k, v in report.items():
            if k in _HEAVY_RESULT_KEYS or (
                isinstance(k, str) and k.startswith("_")
            ):
                continue
            out[k] = _compact_report_for_consumer(v)
        return out
    if isinstance(report, list):
        return [_compact_report_for_consumer(v) for v in report]
    return report


_BENCHMARK_FLAG = "ENG_DRAWING_BENCHMARK_ENABLED"
_OCR_BENCHMARK_FLAG = "ENG_DRAWING_OCR_BENCHMARK_ENABLED"
_BENCHMARK_PROFILES: dict[str, dict[str, Any]] = {
    "approved_local_extractors": {
        "kind": "text",
        "providers": [
            "pypdf_baseline",
            "pdfplumber_experimental",
            "pdfium_experimental",
        ],
    },
    # R7-08: perfil experimental de percepção visual — exige flag própria
    # além do benchmark master; nunca habilitado por padrão em produção.
    "approved_local_visual_ocr": {
        "kind": "visual_ocr",
        "requires_flag": _OCR_BENCHMARK_FLAG,
        "pipelines": [
            "pdfium_render_paddleocr",
            "pdfium_render_opencv_paddleocr",
        ],
    },
}

_MAX_SPATIAL_SAMPLE = 200


def _benchmark_limitations(runs: list[dict[str, Any]]) -> list[str]:
    """R7-16: limitações derivadas da execução real — um provider que
    rodou nunca é declarado 'não executou'; erro/parcial registra motivo."""
    limitations = [
        "Cobertura por provider — não é acurácia nem ground truth; "
        "presença em OCR não vira fato de Engenharia."
    ]
    for run in runs:
        pid = run.get("provider_id", "?")
        status = run.get("status")
        if status in {"provider_error", "extraction_error", "error"}:
            limitations.append(
                f"provider {pid} não executou: "
                f"{run.get('error') or status}"
            )
        elif status == "partial":
            limitations.append(
                f"provider {pid}: cobertura parcial — "
                + "; ".join(run.get("limitations") or ["ver runs"])
            )
        else:
            for lim in run.get("limitations") or []:
                limitations.append(f"provider {pid}: {lim}")
    return limitations


async def _analyze_drawing_benchmark(
    context, params: dict, question: str | None
) -> CallToolResult:
    """analyze(product.drawing_benchmark) — governed multiprovider
    benchmark over the official drawing PDF (read-only)."""
    import os

    from engineering_app.application.drawing.document_benchmark_service import (
        reconcile_provider_fields,
        run_official_document_benchmark,
    )
    from engineering_app.application.drawing.drawing_analysis_service import (
        DrawingAnalysisError,
    )

    if os.environ.get(_BENCHMARK_FLAG) != "true":
        return _err(
            "Benchmark experimental de desenho desabilitado neste "
            "ambiente.",
            status_code=403,
            code="feature_disabled",
        )
    code = str(params.get("product_code") or "").strip()
    if not code:
        return _err(
            "product_code obrigatório para product.drawing_benchmark.",
            code="validation",
        )
    profile = str(
        params.get("benchmark_profile") or "approved_local_extractors"
    ).strip()
    spec = _BENCHMARK_PROFILES.get(profile)
    if spec is None:
        return _err(
            f"benchmark_profile '{profile}' não permitido.",
            status_code=400,
            code="provider_profile_not_allowed",
            data={"allowed": sorted(_BENCHMARK_PROFILES)},
        )
    extra_flag = spec.get("requires_flag")
    if extra_flag and os.environ.get(extra_flag) != "true":
        return _err(
            "Perfil visual OCR experimental desabilitado neste "
            "ambiente.",
            status_code=403,
            code="feature_disabled",
            data={"required_flag": extra_flag},
        )
    fields_raw = params.get("fields")
    fields = (
        [str(f).strip() for f in fields_raw if str(f).strip()][:50]
        if isinstance(fields_raw, list)
        else []
    )
    ctx = bridge._source_context(context)
    try:
        out = await run_official_document_benchmark(
            code=code,
            source=bridge.build_delegated_auxiliary_source(),
            ctx=ctx,
            providers=spec.get("providers"),
            visual_pipelines=spec.get("pipelines"),
            corpus_id="official_drawing",
            environment="mcp_governed",
        )
    except DrawingAnalysisError as exc:
        return _err(
            str(exc), status_code=exc.status_code, code=exc.code
        )
    coverage = (
        reconcile_provider_fields(out["runs"], fields)
        if fields
        else None
    )
    runs = []
    for r in out["runs"]:
        clean = {k: v for k, v in r.items() if not k.startswith("_")}
        sample = r.get("_tokens_sample")
        if sample:
            clean["spatial_evidence"] = {
                "coordinate_system": "pixels_top_left + "
                "bounding_box_pdf_points (transform explícita por "
                "render scale)",
                "token_sample": sample[:_MAX_SPATIAL_SAMPLE],
                "token_sample_size": len(sample[:_MAX_SPATIAL_SAMPLE]),
                "note": (
                    "Evidência OCR experimental — não é fato oficial; "
                    "número reconhecido ≠ cota validada."
                ),
            }
        runs.append(clean)
    return _ok(
        {
            "analysis_type": "product.drawing_benchmark",
            "question": question,
            "schema_version": "drawing_benchmark.v1",
            "benchmark_profile": profile,
            "document": out["document"],
            "same_document_verified": out["same_document_verified"],
            "providers": runs,
            "field_coverage": coverage,
            "evidence_dedup": out.get("evidence_dedup"),
            "quality_gate": "EVAL_PENDING",
            "limitations": _benchmark_limitations(out["runs"]),
            "provenance": (
                "api-delpi product/drawing/pdf (identidade delegada) "
                "+ adapters locais engineering-api"
            ),
        },
        "Benchmark multiprovider do desenho oficial.",
    )


def _structure_codes(payload: dict) -> list[str]:
    """Extrai códigos de componentes da estrutura BOM (best-effort,
    defensivo — contrato owner api-delpi pode evoluir)."""
    codes: list[str] = []

    def walk(node):
        if isinstance(node, dict):
            for key in ("component_code", "code", "product_code",
                        "item_code", "code_son"):
                v = node.get(key)
                if isinstance(v, str) and v.strip().isdigit():
                    codes.append(v.strip())
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(payload)
    return codes


async def _produce_drawing_understanding(context, code: str):
    """Produção compartilhada de evidência visual (R12.1) — caso de uso
    interno do bridge, NÃO um handler MCP. Chamável por composição
    legítima em `product.drawing_analysis` e `product.drawing_understanding`
    sem dependência circular entre handlers. Retorna
    (understanding, structure, best_run, tokens) ou lança
    DrawingAnalysisError."""
    from engineering_app.application.drawing.document_benchmark_service import (  # noqa: E501
        run_official_document_benchmark,
    )
    from engineering_app.application.drawing.drawing_analysis_service import (  # noqa: E501
        DrawingAnalysisError,
    )
    from engineering_app.application.drawing.drawing_contracts import (
        unwrap_delegated,
    )
    from engineering_app.application.drawing.understanding import (
        build_understanding,
    )

    spec = _BENCHMARK_PROFILES["approved_local_visual_ocr"]
    ctx = bridge._source_context(context)
    out = await run_official_document_benchmark(
        code=code,
        source=bridge.build_delegated_auxiliary_source(),
        ctx=ctx,
        providers=None,
        visual_pipelines=spec.get("pipelines"),
        corpus_id="official_drawing",
        environment="mcp_governed",
    )
    runs = [
        r
        for r in out["runs"]
        if r.get("status") in {"ok", "partial"} and r.get("_tokens_sample")
    ]
    if not runs:
        raise DrawingAnalysisError(
            "Nenhum pipeline visual retornou evidência OCR para "
            "interpretação.",
            status_code=422,
            code="no_ocr_evidence",
        )
    best = max(runs, key=lambda r: r.get("token_count") or 0)
    tokens = [
        {
            "normalized_text": t.get("normalized_text"),
            "raw_text": t.get("raw_text"),
            "bounding_box_px": t.get("bounding_box_px"),
            "confidence": t.get("confidence"),
            "page": t.get("page", 1),
        }
        for t in (best.get("_tokens_sample") or [])
    ]
    # RQ-VAL-029 — evidência por página: tamanhos, primitivas gráficas e
    # status OCR por página para interpretação e cobertura verificável.
    _render_by_page: dict[int, tuple[int, int]] = {}
    _page_status: dict[int, dict[str, Any]] = {}
    for _st in best.get("pages") or []:
        _p = _st.get("page")
        _r = _st.get("render") or {}
        if _p and _r.get("width") and _r.get("height"):
            _render_by_page[int(_p)] = (
                int(_r["width"]),
                int(_r["height"]),
            )
        if _p:
            _page_status[int(_p)] = {
                "status": _st.get("status"),
                "error": _st.get("error"),
            }
    _prims_by_page = best.get("_graphic_primitives_by_page") or {}
    if not _prims_by_page and best.get("_graphic_primitives"):
        _prims_by_page = {1: best["_graphic_primitives"]}
    bom_codes: list[str] | None = None
    structure: dict | None = None
    try:
        _raw_structure = await bridge.build_delegated_auxiliary_source().fetch_product_structure(  # noqa: E501
            ctx, code=code
        )
        bom_codes = _structure_codes(_raw_structure or {}) or None
        try:
            structure = unwrap_delegated(
                _raw_structure,
                what="product.structure",
                not_found_code="structure_not_found",
                not_found_message="",
            )
        except DrawingAnalysisError:
            structure = None
    except Exception:
        bom_codes = None
        structure = None
    from engineering_app.application.drawing.understanding import (
        build_document_understanding,
    )

    understanding = build_document_understanding(
        tokens,
        document_hash=best.get("document_hash") or "",
        bom_codes=bom_codes,
        product_code=code,
        render_size_by_page=_render_by_page,
        graphic_primitives_by_page=_prims_by_page,
    )
    # Identidade do documento oficial analisado — envelope do
    # understanding; consumidores (report/response) não devem
    # depender de `out` do benchmark, que fica fora de escopo aqui.
    understanding["document"] = out["document"]
    understanding["same_document_verified"] = out[
        "same_document_verified"
    ]
    _pdf_pages = best.get("pdf_page_count")
    _attempted = sorted(_page_status)
    _failed = [
        {"page": p, "error": s.get("error")}
        for p, s in sorted(_page_status.items())
        if s.get("status") not in {"ok"}
    ]
    _not_processed = (
        [p for p in range(1, _pdf_pages + 1) if p not in _page_status]
        if _pdf_pages
        else []
    )
    understanding["page_coverage"] = {
        "pdf_page_count": _pdf_pages,
        "pages_attempted": _attempted,
        "pages_ocr_ok": [
            p for p, s in sorted(_page_status.items())
            if s.get("status") == "ok"
        ],
        "pages_failed": _failed,
        "pages_not_processed": _not_processed,
        "token_count": best.get("token_count"),
        "token_sample_truncated": (
            len(tokens) < (best.get("token_count") or 0)
        ),
    }
    understanding["source_run"] = {
        "provider_id": best.get("provider_id"),
        "token_count": best.get("token_count"),
        "token_sample_size": len(tokens),
        "sampled": len(tokens) < (best.get("token_count") or 0),
    }
    # R9.8 — motor SLANet: estrutura de tabela real sobre a região
    # detectada, com associação OCR↔célula; candidate, nunca autoridade.
    _pdf_raw = None
    _pdf_bytes = None
    try:
        _pdf_raw = await bridge.build_delegated_auxiliary_source().fetch_product_drawing_pdf(  # noqa: E501
            ctx, code=code
        )
        _pdf_bytes = (
            _pdf_raw.get("content") if isinstance(_pdf_raw, dict) else None
        )
    except Exception:
        _pdf_bytes = None
    try:
        from engineering_app.infrastructure.extraction.engine_adapters import (
            TableStructureEngine,
        )

        _tbl_box = (
            understanding.get("component_table") or {}
        ).get("box") or None
        _sl = TableStructureEngine().run(
            bytes(_pdf_bytes) if _pdf_bytes else b"",
            document_hash_sha256=best.get("document_hash") or "",
            product_code=code,
            crop_box=_tbl_box,
        )
        understanding["table_structure_engines"] = [
            {
                "provider_id": _sl.get("provider_id"),
                "model_version": _sl.get("model_version"),
                "executed": not _sl.get("error_kind"),
                "error_kind": _sl.get("error_kind"),
                "structure_score": (
                    (_sl.get("tables") or [{}])[0].get("structure_score")
                    if _sl.get("tables")
                    else None
                ),
                "row_count": (
                    (_sl.get("tables") or [{}])[0].get("row_count")
                    if _sl.get("tables")
                    else None
                ),
                "cells": _sl.get("cells"),
                "cell_count": len(_sl.get("cells") or []),
                "cells_with_text": sum(
                    1 for c in (_sl.get("cells") or [])
                    if c.get("normalized_text")
                ),
                "duration_ms": _sl.get("duration_ms"),
                "state": "CANDIDATE_GENERATED",
            }
        ]
    except Exception as _sl_exc:
        understanding["table_structure_engines"] = [
            {
                "provider_id": "table_structure_slanet",
                "executed": False,
                "error_kind": "UNAVAILABLE",
                "error_detail": str(_sl_exc),
                "state": "ENGINE_AVAILABLE",
            }
        ]
    return understanding, structure, best, tokens, _pdf_bytes


def _understanding_job_running(job) -> CallToolResult:
    return _ok(
        {
            "analysis_type": "product.drawing_understanding",
            "status": "RUNNING",
            "job_id": job.job_id,
            "result_ready": False,
            "retry": {
                "analysis_type": "product.drawing_understanding",
                "parameters": {
                    "product_code": job.product_code,
                    "job_id": job.job_id,
                },
            },
            "note": (
                "Leitura visual integral em execução prolongada; "
                "repita a chamada com o job_id retornado. "
                "Este envelope não é o relatório."
            ),
        },
        "Leitura visual em execução — consulte o job_id.",
    )


def _understanding_job_terminal(job) -> CallToolResult:
    if job.status == "FAILED":
        err = job.error or {}
        return _err(
            err.get("message") or "Execução da leitura falhou.",
            status_code=err.get("status_code", 500),
            code=err.get("code") or "analysis_incomplete",
        )
    payload = dict(job.result or {})
    payload["status"] = "COMPLETED"
    payload["job_id"] = job.job_id
    payload["result_ready"] = True
    return _ok(
        payload,
        "Interpretação estrutural candidata do desenho oficial.",
    )


async def _analyze_drawing_understanding(
    context, params: dict, question: str | None
) -> CallToolResult:
    """analyze(product.drawing_understanding) — R8 experimental.

    RES-01: a leitura síncrona de PDF longo era encerrada pelo cliente
    MCP (gateway HTTP 499, 0 bytes, sem exceção da aplicação). O mesmo
    AnalysisJobStore de DEC-VAL-030 devolve ``job_id`` na hora e o
    consumidor recupera ``COMPLETED`` ou ``FAILED`` tipado. Não há
    segunda fila.
    """
    import os

    code = str(params.get("product_code") or "").strip()
    if os.environ.get(_BENCHMARK_FLAG) != "true":
        return _err(
            "Benchmark experimental de desenho desabilitado neste "
            "ambiente.",
            status_code=403,
            code="feature_disabled",
        )
    if os.environ.get(_OCR_BENCHMARK_FLAG) != "true":
        return _err(
            "Perfil visual OCR experimental desabilitado neste "
            "ambiente.",
            status_code=403,
            code="feature_disabled",
            data={"required_flag": _OCR_BENCHMARK_FLAG},
        )
    if not code:
        return _err(
            "product_code obrigatório para product.drawing_understanding.",
            code="validation",
        )
    from engineering_app.application.drawing.analysis_jobs import (
        analysis_job_store,
    )
    from engineering_app.application.drawing.drawing_analysis_service import (  # noqa: E501
        DrawingAnalysisError,
    )
    import asyncio as _aio
    import hashlib as _hl
    import json as _js

    ctx = bridge._source_context(context)
    ident = _drawing_job_owner_fingerprint(ctx)
    params_fp = _hl.sha256(
        _js.dumps(
            {"kind": "product.drawing_understanding", "code": code},
            sort_keys=True,
        ).encode()
    ).hexdigest()[:20]
    store = analysis_job_store()
    requested = params.get("job_id")
    if requested:
        job = store.get_for_owner(str(requested), ident)
        if job is None or job.product_code != code:
            return _err(
                "job_id não encontrado ou expirado.",
                status_code=404,
                code="job_not_found",
            )
        if job.status == "RUNNING":
            return _understanding_job_running(job)
        return _understanding_job_terminal(job)
    job, created = store.get_or_start(
        product_code=code,
        identity_fingerprint=ident,
        params_fingerprint=params_fp,
    )
    if not created:
        if job.status == "RUNNING":
            return _understanding_job_running(job)
        return _understanding_job_terminal(job)

    async def _run_job() -> None:
        try:
            payload = await _execute_drawing_understanding(
                context, code, question
            )
            store.complete(
                job.job_id, _compact_report_for_consumer(payload)
            )
        except DrawingAnalysisError as exc:
            store.fail(
                job.job_id,
                exc.code,
                str(exc),
                status_code=exc.status_code,
            )
        except _aio.CancelledError:
            store.fail(
                job.job_id,
                "cancelled",
                "Execução cancelada.",
                status_code=499,
            )
            raise
        except Exception as exc:  # noqa: BLE001 — job nunca vaza 502
            logger.exception(
                "drawing_understanding_job_failed job_id=%s", job.job_id
            )
            store.fail(
                job.job_id,
                "analysis_incomplete",
                f"{type(exc).__name__}: {exc}",
                status_code=500,
            )

    _aio.create_task(_run_job())
    return _understanding_job_running(job)


async def _execute_drawing_understanding(
    context, code: str, question: str | None
) -> dict:
    """Produz o payload de understanding. Só roda dentro do job."""
    from engineering_app.application.drawing.document_benchmark_service import (  # noqa: E501
        run_official_document_benchmark,
    )
    from engineering_app.application.drawing.drawing_analysis_service import (  # noqa: E501
        flatten_bom_occurrences,
    )
    from engineering_app.application.drawing.drawing_contracts import (
        unwrap_delegated,
    )
    from engineering_app.application.drawing.object_profiles_builder import (
        build_object_profiles,
    )
    from engineering_app.application.drawing.understanding import (
        build_understanding,
    )

    understanding, structure, best, tokens, _pdf_bytes = (
        await _produce_drawing_understanding(context, code)
    )
    # Relatório candidato consolidado (R10) — seções A–H do doc 116-B,
    # montado dos dados já governados; additive, DRAFT/CANDIDATE.
    _comp = (understanding.get("component_table") or {}).get("rows") or []
    _sl_e = (understanding.get("table_structure_engines") or [{}])[0]
    understanding["report"] = {
        "kind": "drawing_analysis_report",
        "state": "DRAFT/CANDIDATE",
        "identification": {
            "product_code": code,
            "document_id": understanding.get("document"),
            "revision": understanding.get("revision"),
            "customer": understanding.get("customer"),
            "document_sha": best.get("document_hash"),
            "analyzed_at_source": best.get("provider_id"),
        },
        "summary": {
            "regions_identified": len(understanding.get("regions") or []),
            "component_rows": len(_comp),
            "slanet_cells": _sl_e.get("cell_count"),
            "slanet_cells_with_text": _sl_e.get("cells_with_text"),
            "slanet_executed": _sl_e.get("executed"),
            "structure_score": _sl_e.get("structure_score"),
        },
        "structure": {
            "regions": understanding.get("regions") or [],
            "title_block": understanding.get("title_block"),
            "revisions": understanding.get("revisions") or [],
            "notes": understanding.get("notes") or [],
        },
        "component_candidates": [
            {
                "item": r.get("item"),
                "quantity": r.get("quantity"),
                "component_code": r.get("component_code"),
                "description": r.get("description"),
                "region": r.get("region"),
                "cell_refs": r.get("cells") or [],
                "evidence": r.get("evidence"),
                "association_status": r.get("status", "CANDIDATE"),
            }
            for r in _comp
        ],
        "technical_information": {
            "dimensions": understanding.get("dimensions") or [],
            "state": "PENDING_ENGINEERING_VALIDATION",
            "limitations": (
                "cotas/tolerancias/materiais/simbolos ainda nao validados "
                "pela Engenharia (catalogo M3 pendente)"
            ),
        },
        "official_comparison": understanding.get("bom_comparison")
        or {"state": "NOT_CHECKED"},
        "structure_validation": {
            "state": "NOT_CHECKED",
            "engineering_approval": "NOT_APPROVED",
        },
        "alerts": {
            "ambiguous": understanding.get("ambiguous_fields") or [],
            "unassigned_tokens": (
                (_sl_e.get("association") or {}).get("unassigned") or []
            ),
            "conflicts": (
                (_sl_e.get("association") or {}).get("conflicts") or []
            ),
            "limitations": understanding.get("limitations") or [],
        },
        "evidence": {
            "document_sha": best.get("document_hash"),
            "page": 1,
            "engines": {
                "ocr": best.get("provider_id"),
                "table_structure": _sl_e.get("provider_id"),
                "model": _sl_e.get("model_version"),
            },
            "cell_bounding_boxes": [
                c.get("bounding_box_px")
                for c in (_sl_e.get("cells") or [])
            ],
        },
        "quality_gate": "EVAL_PENDING",
        "not_official": True,
    }
    # R11.1 — perfis reutilizáveis alimentados pela evidência visual
    # real desta execução (sem reprocessar OCR/SLANet): ocorrências BOM
    # (oficial, proveniência própria) + candidatos do understanding.
    # R12.1 — sem fonte oficial carregada a comparação é fail-closed:
    # sem occurrence_results nem unmatched_drawing_candidates.
    _bom_flat = flatten_bom_occurrences(structure, code)
    from engineering_app.application.drawing.drawing_investigation import (  # noqa: E501
        apply_localized_recovery,
    )
    from engineering_app.infrastructure.extraction.pdfium_adapter import (
        PdfiumExtractionAdapter,
    )
    from engineering_app.infrastructure.extraction.paddleocr_adapter import (
        PaddleOcrAdapter,
    )

    _prog = {
        "budget": {"max_crops": 8, "max_dpi": 300,
                   "max_pixels": 4_000_000},
        # R13 closure — ports reais do pipeline visual (lazy, sem
        # reprocessar por ocorrência; orçamento governado).
        "pdf_bytes": _pdf_bytes,
        "renderer": PdfiumExtractionAdapter(),
        "ocr": PaddleOcrAdapter(),
        "page": 1,
        "reference_dpi": int(best.get("dpi") or 200),
        "reference_dpi_by_page": _render_dpi_by_page(best),
    }
    # DEC-VAL-034 — o caminho product.drawing_understanding executa
    # build_object_profiles sem analyze_product_drawing: a recuperação
    # localizada precisa rodar aqui também, senão localized_recovery
    # nunca existe para a investigação guiada (causa do O0001
    # AMBIGUOUS reportado pelo consumidor).
    apply_localized_recovery(
        understanding,
        product_code=code,
        bom_component_codes=[
            str(it.get("component_code") or "").strip()
            for it in _bom_flat
        ],
        opts=_prog,
        tokens=tokens,
        pdf_sha256=understanding.get("document_hash_sha256"),
        source_revision=(
            (understanding.get("document") or {}).get(
                "drawing_library_revision"
            )
        ),
    )
    from engineering_app.application.drawing.bom_structure_comparator import (  # noqa: E501
        compare_bom_to_drawing,
    )

    _structure_ready = isinstance(structure, dict) and bool(structure)
    _cmp = compare_bom_to_drawing(
        product_code=code,
        bom_occurrences=_bom_flat if _structure_ready else None,
        component_table=understanding.get("component_table"),
        tokens=tokens,
        drawing_pages=(
            (understanding.get("page_coverage") or {}).get("pdf_page_count")
        ),
        code_contexts=understanding.get("code_contexts"),
        page_coverage=understanding.get("page_coverage"),
        bom_error=(
            None if _structure_ready else {"code": "structure_not_provided"}
        ),
    )
    understanding["bom_structure_comparison"] = _cmp
    understanding["report"]["structure_validation"] = _cmp.get(
        "validation_report"
    ) or {
        "state": "DRAFT/CANDIDATE",
        "engineering_approval": "NOT_APPROVED",
    }
    understanding["object_profiles"] = build_object_profiles(
        bom_occurrences=_bom_flat,
        visual_observations=[],
        understanding=understanding,
        document_sha=best.get("document_hash") or None,
        official_source_ref=f"api-delpi:/products/{code}/structure",
        official_source_state=(
            "NOT_PROVIDED"
            if not structure
            else ("EMPTY_CONFIRMED" if not _bom_flat else "AVAILABLE")
        ),
        product_code=code,
        progressive=_prog,
        include_investigations=True,
    )
    understanding["report"]["object_profiles"] = understanding[
        "object_profiles"
    ]
    return {
        "analysis_type": "product.drawing_understanding",
        "question": question,
        "document": understanding.get("document"),
        "same_document_verified": understanding.get(
            "same_document_verified"
        ),
        "understanding": understanding,
        "quality_gate": "EVAL_PENDING",
        "provenance": (
            "api-delpi product/drawing/pdf (identidade delegada) → "
            "PDFium render + local PaddleOCR (subprocess isolado) → "
            "drawing_understanding.v1 deterministic rules"
        ),
    }


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


def knowledge_topics() -> tuple[str, ...]:
    """Canonical closed vocabulary for ``knowledge.topic``.

    The versioned knowledge document is the single owner — only
    actually served topics are published (planned topics answer
    ``not_implemented`` honestly, never appear in the enum).
    """
    doc = _knowledge_document()
    return tuple(sorted((doc.get("topics") or {}).keys()))


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
