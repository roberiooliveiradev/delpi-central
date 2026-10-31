"""CAIO semantic MCP bridge — six stable tools over a typed registry.

The public surface is exactly six tools — ``get_context``, ``read``,
``analyze``, ``knowledge``, ``execute``, ``delete``. Every call
dispatches on ``(entity, action)`` from the allowlist registry; no
URL, HTTP method, SQL or model-supplied handler names. All handlers
delegate to the same official use cases as the REST routes — parity,
not reimplementation.

Governance model:
- ``read``/``analyze``/``knowledge`` — human principal + commercial
  permission (``commercial.access``/``commercial.manage``), same gate
  as the REST routes, portfolio scope by the official resolver.
- ``execute`` — authorized creates/updates run directly through the
  official owner use cases (no repetitive confirmations); contracts
  not activated answer ``not_implemented`` honestly.
- ``delete`` — destructive operations only via sealed
  ``prepare → commit``: server-side proposal bound to actor,
  capability, target, TTL and single-use, claimed atomically under
  the store lock before the executor runs.
"""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from pathlib import Path
from typing import Any

from mcp.types import CallToolResult

from delpi_mcp.errors import mcp_tool_result

from commercial_app.application.caio.caio_agent_service import CaioAgentService
from commercial_app.application.caio.semantic_registry import (
    PLANNED_SEMANTIC_ACTIONS,
    SEMANTIC_ACTIONS,
    SEMANTIC_CATALOG_VERSION,
    SEMANTIC_TOOL_NAMES,
    actions_for_entity,
    entities_summary,
    semantic_action,
)
from commercial_app.application.caio import proposal_store
from commercial_app.interface.mcp import tool_bridge as bridge
from commercial_app.interface.mcp import tool_bridge_parity as parity
from commercial_app.interface.mcp.branding import CAIO_FULL_NAME
from commercial_app.interface.mcp.constants import SEMANTIC_TOOL_CLASS

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
    result payload; underlying success/error semantics preserved."""
    payload = dict(getattr(result, "structured_content", None) or {})
    payload.setdefault("entity", entity)
    payload.setdefault("action", action)
    return mcp_tool_result(payload, is_error=bool(result.is_error))


def _handle_error(exc: Exception) -> CallToolResult:
    return bridge.handle_tool_error(exc)


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
    pagination → only the keys the capability contract declares
    (``entry.fields``). Unknown keys are rejected as typed validation
    errors — never forwarded to handlers that cannot accept them
    (which previously surfaced as a masked 502)."""
    merged: dict[str, Any] = {}
    for key, value in (filters or {}).items():
        if key not in entry.fields:
            return {}, _err(
                f"Campo '{key}' não é filtro de {entry.capability}.",
                code="validation",
                data={"allowed_fields": list(entry.fields)},
            )
        merged[key] = value
    if pagination:
        declared = set(entry.fields)
        supported = {"page", "page_size", "limit", "cursor"}
        for key, value in pagination.items():
            if key not in supported:
                return {}, _err(
                    f"Campo de paginação '{key}' não suportado.",
                    code="validation",
                    data={"supported_pagination": sorted(supported)},
                )
            if key not in declared:
                return {}, _err(
                    f"Operação {entry.capability} não suporta "
                    f"paginação '{key}'.",
                    code="validation",
                    data={
                        "capability": entry.capability,
                        "pagination_fields": sorted(
                            declared & supported
                        ),
                        "allowed_fields": list(entry.fields),
                    },
                )
            merged[key] = value
    missing = [
        f for f in entry.required_fields if merged.get(f) is None
    ]
    if missing:
        return {}, _err(
            f"Campos obrigatórios ausentes para "
            f"{entry.capability}: {', '.join(missing)}.",
            code="validation",
            data={
                "missing_fields": missing,
                "required_fields": list(entry.required_fields),
            },
        )
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
        context = bridge._require_commercial_human()
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
        user = context.user
        data: dict[str, Any] = {
            "assistant": CAIO_FULL_NAME,
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
            "act_enabled": True,
            "commercial_capabilities": {
                "access": bool(
                    getattr(user, "is_superadmin", False)
                    or bridge.has_access(user)
                ),
                "manage": bool(
                    getattr(user, "is_superadmin", False)
                    or bridge.has_manage(user)
                ),
                "billing_notify": bool(
                    getattr(user, "is_superadmin", False)
                    or bridge.has_billing_notify(user)
                ),
            },
            "confirmation_model": {
                "read_analyze_knowledge": "executam imediatamente.",
                "execute": (
                    "Criações e atualizações autorizadas executam "
                    "diretamente — sem confirmações repetitivas. A "
                    "autorização efetiva e as políticas de consentimento "
                    "do backend permanecem soberanas."
                ),
                "delete": (
                    "Exclusões exigem proposta selada "
                    "phase=prepare → phase=commit com o proposal_ref "
                    "exato — confirmação explícita por alvo e efeito."
                ),
            },
            "selected_ref": selected_ref,
            "agent_directives": CaioAgentService.agent_directives(),
            "planned_actions": list(PLANNED_SEMANTIC_ACTIONS),
            "required_permission": "commercial.access",
            "notes": [
                "Contexto não concede permissão — a autorização "
                "efetiva é verificada pela Core a cada chamada.",
                "Estados honestos: unavailable/forbidden indicam "
                "falha ou falta de autorização na fonte — nunca "
                "'sem dados'.",
                "Escopo de carteira segue o resolver oficial: "
                "membros veem apenas clientes autorizados.",
            ],
        }
        return _ok(data, "Contexto semântico do CAIO.")
    except Exception as exc:
        return _handle_error(exc)


# --- read -----------------------------------------------------------------


def tool_read(
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
    try:
        bridge._require_commercial_human()
    except Exception as exc:
        return _handle_error(exc)
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
        result = handler(args)
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
    ("portfolio", "me"): lambda a: bridge.tool_portfolio_me(),
    ("portfolio", "get"): lambda a: parity.tool_portfolio_get(**a),
    ("portfolio", "list"): lambda a: parity.tool_portfolio_list(**a),
    ("portfolio", "audit"): lambda a: parity.tool_portfolio_audit(**a),
    ("portfolio", "coverage_audit"): (
        lambda a: parity.tool_portfolio_coverage_audit()
    ),
    ("portfolio", "load_summary"): (
        lambda a: parity.tool_portfolio_load_summary(**a)
    ),
    ("portfolio", "customer_coverage"): (
        lambda a: parity.tool_portfolio_customer_coverage(**a)
    ),
    ("customer", "list"): lambda a: bridge.tool_customer_list(**a),
    ("customer", "search"): lambda a: parity.tool_customer_search(**a),
    ("customer", "enrichment"): (
        lambda a: parity.tool_customer_enrichment(**a)
    ),
    ("customer", "billing_series"): (
        lambda a: parity.tool_customer_billing_series(**a)
    ),
    ("customer", "center_assignments"): (
        lambda a: parity.tool_customer_center_assignments()
    ),
    ("customer", "outbound_invoices"): (
        lambda a: parity.tool_customer_outbound_invoices(**a)
    ),
    ("customer", "outbound_invoice"): (
        lambda a: parity.tool_customer_outbound_invoice(**a)
    ),
    ("customer", "open_orders"): (
        lambda a: parity.tool_customer_open_orders(**a)
    ),
    ("customer", "contacts"): (
        lambda a: parity.tool_customer_contacts(**a)
    ),
    ("customer", "account_audit"): (
        lambda a: parity.tool_customer_account_audit(**a)
    ),
    ("customer_center", "list"): (
        lambda a: parity.tool_customer_center_list(**a)
    ),
    ("open_order", "list"): lambda a: bridge.tool_open_order_list(**a),
    ("open_order", "recently_closed"): (
        lambda a: bridge.tool_open_order_recently_closed(**a)
    ),
    ("open_order", "open_ops"): lambda a: parity.tool_open_ops(),
    ("proposal", "list"): lambda a: bridge.tool_proposal_list(**a),
    ("proposal", "get"): lambda a: parity.tool_proposal_get(**a),
    ("proposal", "analytics_list"): (
        lambda a: parity.tool_proposal_analytics_list(**a)
    ),
    ("proposal", "analytics_get"): (
        lambda a: parity.tool_proposal_analytics_get(**a)
    ),
    ("proposal", "history_events"): (
        lambda a: parity.tool_proposal_history_events(**a)
    ),
    ("worklist", "mine"): lambda a: parity.tool_worklist_mine(**a),
    ("worklist", "done"): lambda a: parity.tool_worklist_done(**a),
    ("task", "list"): lambda a: parity.tool_task_list(**a),
    ("activity", "list"): lambda a: parity.tool_activity_list(**a),
    ("group", "list"): lambda a: parity.tool_group_list(**a),
    ("group", "get"): lambda a: parity.tool_group_get(**a),
    ("sla_policy", "list"): lambda a: parity.tool_sla_policy_list(**a),
    ("home_favorite", "list"): lambda a: parity.tool_home_favorite_list(),
    ("team", "roster"): lambda a: parity.tool_team_roster(),
    ("attachment", "list"): lambda a: parity.tool_attachment_list(**a),
    ("interaction_room", "list"): (
        lambda a: parity.tool_interaction_room_list(**a)
    ),
    ("interaction_room", "get"): (
        lambda a: parity.tool_interaction_room_get(**a)
    ),
    ("interaction_room", "members"): (
        lambda a: parity.tool_interaction_room_members(**a)
    ),
    ("interaction_room", "messages"): (
        lambda a: parity.tool_interaction_room_messages(**a)
    ),
    ("interaction_room", "shared_items"): (
        lambda a: parity.tool_interaction_room_shared_items(**a)
    ),
    ("interaction_room", "pins"): (
        lambda a: parity.tool_interaction_room_pins(**a)
    ),
    ("interaction_room", "mention_suggest"): (
        lambda a: parity.tool_interaction_mention_suggest(**a)
    ),
    ("interaction_room", "entity_preview"): (
        lambda a: parity.tool_interaction_entity_preview(**a)
    ),
    ("production", "order"): lambda a: parity.tool_production_order(**a),
    ("production", "appointments"): (
        lambda a: parity.tool_production_appointments(**a)
    ),
    ("production", "product_status"): (
        lambda a: parity.tool_product_factory_status(**a)
    ),
    ("production", "product_structure"): (
        lambda a: parity.tool_product_structure(**a)
    ),
    ("product", "search"): lambda a: parity.tool_product_search(**a),
    ("product", "summary"): lambda a: parity.tool_product_summary(**a),
    ("product", "customers"): (
        lambda a: parity.tool_product_customers(**a)
    ),
    ("product", "filter_options"): (
        lambda a: parity.tool_product_filter_options(**a)
    ),
    ("user_profile", "get"): lambda a: parity.tool_user_profile_get(**a),
}

# --- analyze --------------------------------------------------------------


def tool_analyze(
    *,
    analysis_type: str,
    subject_refs: list | None = None,
    question: str | None = None,
    parameters: dict | None = None,
) -> CallToolResult:
    """Semantic ANALYZE — grounded compositions over official facts."""
    try:
        bridge._require_commercial_human()
        kind = (analysis_type or "").strip().lower()
        params = dict(parameters or {})
        handler = _ANALYZE_DISPATCH.get(kind)
        if handler is None:
            return _err(
                f"analysis_type '{kind}' não implementado.",
                status_code=501,
                code="not_implemented",
                data={
                    "available": sorted(_ANALYZE_DISPATCH.keys()),
                },
            )
        unknown = set(params) - _ANALYZE_ALLOWED_PARAMS
        if unknown:
            return _err(
                f"Parâmetros não suportados: {sorted(unknown)}.",
                code="validation",
            )
        params["question"] = question
        return handler(params)
    except Exception as exc:
        return _handle_error(exc)


def _analyze_proxy(kind: str):
    path, allowed, required = parity.ANALYZE_PROXY_MAP[kind]

    def handler(p: dict) -> CallToolResult:
        missing = [key for key in required if not p.get(key)]
        if missing:
            return _err(
                f"Parâmetros obrigatórios ausentes em '{kind}': "
                f"{missing}.",
                code="validation",
                data={
                    "analysis_type": kind,
                    "required": list(required),
                    "allowed": list(allowed),
                },
            )
        upstream = {
            key: p.get(key) for key in allowed if p.get(key) is not None
        }
        scope_keys = (
            "seller_id", "portfolio_id", "scope_mode",
            "account_customer_code", "customer_codes", "question",
        )
        scope_args = {
            key: p.get(key) for key in scope_keys if p.get(key) is not None
        }
        return parity.analyze_proxy(
            path=path,
            analysis_label=kind,
            **scope_args,
            **upstream,
        )

    return handler


_ANALYZE_DISPATCH = {
    "portfolio.open_summary": (
        lambda p: bridge.analyze_open_portfolio_summary(**p)
    ),
    "portfolio.open_horizon": (
        lambda p: bridge.analyze_open_portfolio_horizon(**p)
    ),
    "rol.summary": lambda p: bridge.analyze_rol_summary(**p),
    "portfolio.billing_share": (
        lambda p: parity.analyze_billing_share(**p)
    ),
    "portfolio.billing_ranking": (
        lambda p: parity.analyze_billing_ranking(**p)
    ),
    "sales_order_otd.line_detail": (
        lambda p: parity.analyze_otd_line_detail(**p)
    ),
    "dashboard.department_idd": (
        lambda p: parity.analyze_department(
            analysis_label="dashboard.department_idd", idd=True, **p
        )
    ),
    "dashboard.department_indicators": (
        lambda p: parity.analyze_department(
            analysis_label="dashboard.department_indicators",
            idd=False,
            **p,
        )
    ),
    **{
        kind: _analyze_proxy(kind)
        for kind in parity.ANALYZE_PROXY_MAP
    },
}

_ANALYZE_ALLOWED_PARAMS: set[str] = {
    "seller_id", "portfolio_id", "scope_mode", "customer_codes",
    "account_customer_code", "start_date", "end_date", "branch",
    "customer_segment", "customer_centers", "granularity", "nature",
    "status", "product_codes", "product_groups", "market", "group_by",
    "limit", "order", "include_others", "department_id", "competence",
    "order_number", "line_item",
}

# --- knowledge ------------------------------------------------------------


_KNOWLEDGE_PATH = (
    Path(__file__).resolve().parents[2]
    / "content"
    / "caio_commercial_knowledge.json"
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


_KNOWLEDGE_COLLECTIONS = ("topics", "methods", "playbooks")
_SELECTION_CAP = 5


def _fold(text: str) -> str:
    """Case + accent fold for knowledge selection matching."""
    return "".join(
        ch
        for ch in unicodedata.normalize("NFKD", (text or "").lower())
        if not unicodedata.combining(ch)
    )


# Portuguese function words / interrogatives that carry no retrieval
# signal — filtered out of the query terms (accent-folded forms).
_SELECTION_STOPWORDS = frozenset({
    "que", "qual", "quais", "como", "quando", "onde", "quem",
    "porque", "pois", "para", "pra", "sobre", "entre", "ser",
    "sao", "estao", "esta", "foi", "era", "sera", "tem", "ter",
    "seus", "suas", "seu", "sua", "meu", "minha", "nosso", "nossa",
    "muito", "pouco", "todo", "toda", "todos", "todas", "tudo",
    "este", "esta", "isso", "isto", "outro", "outra", "outros",
    "outras", "cada", "mais", "menos", "maior", "menor", "melhor",
    "pior", "entao", "assim", "tambem", "apenas", "vai", "vao",
    "vem", "fazer", "feito", "faz", "pode", "podem", "deve",
    "devem", "quer", "quero", "queremos", "gostaria", "preciso",
    "mostre", "mostrar", "liste", "listar", "traga", "trazer",
    "mes", "meses", "ano", "anos", "dia", "dias", "hoje", "ontem",
    "agora", "ainda", "sendo", "novo", "nova", "ver", "saber",
    "entender", "explique", "explicar", "diga", "fale", "falar",
    "sobre", "algum", "alguma", "alguns", "algumas", "algo",
})


def _knowledge_entry(doc: dict[str, Any], key: str):
    """Resolve a knowledge id across collections.

    Accepts the plain key (``commercial.proposals``), the namespaced
    form (``method.abc_pareto`` / ``playbook.order_health``) or the
    bare id of a method/playbook."""
    for collection in _KNOWLEDGE_COLLECTIONS:
        entries = doc.get(collection) or {}
        if key in entries:
            return collection, entries[key]
        prefix = f"{collection[:-1]}."
        if key.startswith(prefix) and key[len(prefix):] in entries:
            return collection, entries[key[len(prefix):]]
        if key in {f"{collection[:-1]}.{i}" for i in entries}:
            return collection, entries[key.split(".", 1)[1]]
    return None, None


def _knowledge_select(
    doc: dict[str, Any], query: str | None
) -> CallToolResult:
    """Contextual selection over the authorized corpus.

    Scores topics/methods/playbooks by keyword match on title,
    keywords and trigger questions; returns a minimal package with
    provenance — never the whole corpus. All entries share the same
    internal access classification enforced by the human gate above,
    so selection cannot leak cross-scope data (it returns guidance,
    not records)."""
    # Short domain acronyms (OV, OP, PV) score only when declared as
    # corpus keywords — data-driven, no hardcoded acronym list in the
    # mechanism.
    short_terms = {
        kw.strip().lower()
        for collection in _KNOWLEDGE_COLLECTIONS
        for entry in (doc.get(collection) or {}).values()
        if isinstance(entry, dict)
        for kw in (entry.get("keywords") or [])
        if 0 < len(kw.strip()) < 3
    }
    terms = {
        t
        for t in re.split(r"[^\wÀ-ÿ]+", (query or "").lower())
        if len(t) >= 3 or t in short_terms
    }
    # Light plural normalization: "compras"/"pedidos" also try the
    # singular form against the corpus haystack.
    terms |= {
        t[:-1] for t in set(terms) if len(t) > 3 and t.endswith("s")
    }
    # Accent-insensitive matching: Portuguese queries vary diacritics
    # ("previsão" vs corpus keyword "previsao") — normalize both sides,
    # then drop function words that carry no retrieval signal.
    terms = {_fold(t) for t in terms} - _SELECTION_STOPWORDS
    ranked: list[tuple[int, str, str, dict[str, Any]]] = []
    for collection in _KNOWLEDGE_COLLECTIONS:
        kind = collection[:-1]  # topic|method|playbook
        for entry_id, entry in (doc.get(collection) or {}).items():
            if not isinstance(entry, dict):
                continue
            curated_hay = _fold(
                " ".join(entry.get("keywords") or [])
                + " "
                + " ".join(entry.get("trigger_questions") or [])
            )
            text_hay = _fold(
                f"{entry.get('title', '')} {entry.get('objective', '')}"
            )
            # Curated fields (keywords/trigger_questions) weigh double —
            # they exist precisely to route selection.
            score = sum(
                (2 if t in curated_hay else 1)
                for t in terms
                if t in curated_hay or t in text_hay
            )
            if score:
                ranked.append((score, kind, entry_id, entry))
    ranked.sort(key=lambda item: (-item[0], item[1], item[2]))
    if not ranked:
        return _err(
            "Nenhum conteúdo de conhecimento corresponde à consulta.",
            status_code=404,
            code="not_found",
            data={
                "available_ids": {
                    c: sorted((doc.get(c) or {}).keys())
                    for c in _KNOWLEDGE_COLLECTIONS
                },
            },
        )
    items = []
    for score, kind, entry_id, entry in ranked[:_SELECTION_CAP]:
        items.append(
            {
                "id": f"{kind}.{entry_id}",
                "type": kind,
                "title": entry.get("title"),
                "objective": entry.get("objective"),
                "source": entry.get("source"),
                "owner": entry.get("owner", doc.get("owner")),
                "version": entry.get("version", doc.get("version")),
                "access_classification": entry.get(
                    "access_classification"
                ),
                "external_reference": entry.get(
                    "external_reference", False
                ),
                "status": entry.get("status"),
                "related_capabilities": entry.get(
                    "related_capabilities"
                ),
                "related_entries": entry.get("related_entries"),
                "limitations": entry.get("limitations"),
                "conversation_relevance": score,
            }
        )
    return _ok(
        {
            "selection": items,
            "retrieval": (
                "fetch full guidance via knowledge topic=<id> — "
                "methods are external references, never DELPI rules; "
                "playbooks compose official use cases only."
            ),
            "knowledge_version": doc.get("version"),
        },
        "Seleção contextual de conhecimento.",
    )


def tool_knowledge(
    *,
    topic: str | None = None,
    task: str | None = None,
    query: str | None = None,
) -> CallToolResult:
    """Versioned owner-authorized Commercial guidance.

    ``topic`` fetches one entry (``topic``/``method``/``playbook``
    id); an empty topic or ``"*"`` with ``query`` selects the
    relevant entries for the question (contextual selection)."""
    try:
        bridge._require_commercial_human()
        key = (topic or "").strip().lower()
        doc = _knowledge_document()
        if not key or key in {"*", "select", "search"}:
            return _knowledge_select(doc, query or task)
        collection, entry = _knowledge_entry(doc, key)
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
                    "available_ids": {
                        c: sorted((doc.get(c) or {}).keys())
                        for c in _KNOWLEDGE_COLLECTIONS
                    },
                    "planned_topics": sorted(planned),
                },
            )
        return _ok(
            {
                "topic": key,
                "type": collection[:-1],
                "task": task,
                "query": query,
                "knowledge_version": doc.get("version"),
                "owner": entry.get("owner", doc.get("owner")),
                **entry,
            },
            "Conhecimento comercial versionado.",
        )
    except Exception as exc:
        return _handle_error(exc)


# --- execute (governed writes — direct, backend-authorized) -------------------

_EXECUTE_DISPATCH = {
    ("portfolio", "create"): parity.execute_portfolio_create,
    ("portfolio", "update"): parity.execute_portfolio_update,
    ("portfolio", "customers_replace"): (
        parity.execute_portfolio_customers_replace
    ),
    ("portfolio", "customer_add"): parity.execute_portfolio_customer_add,
    ("portfolio", "customer_remove"): (
        parity.execute_portfolio_customer_remove
    ),
    ("portfolio", "members_replace"): (
        parity.execute_portfolio_members_replace
    ),
    ("portfolio", "member_add"): parity.execute_portfolio_member_add,
    ("portfolio", "member_remove"): parity.execute_portfolio_member_remove,
    ("portfolio", "owner_set"): parity.execute_portfolio_owner_set,
    ("portfolio", "transfer"): parity.execute_portfolio_transfer,
    ("portfolio", "transfer_bulk"): parity.execute_portfolio_transfer_bulk,
    ("task", "create"): parity.execute_task_create,
    ("task", "update"): parity.execute_task_update,
    ("task", "complete"): parity.execute_task_complete,
    ("task", "defer"): parity.execute_task_defer,
    ("task", "reassign"): parity.execute_task_reassign,
    ("task", "from_message"): parity.execute_task_from_message,
    ("activity", "create"): parity.execute_activity_create,
    ("group", "create"): parity.execute_group_create,
    ("group", "rename"): parity.execute_group_rename,
    ("group", "members_replace"): parity.execute_group_members_replace,
    ("group", "member_add"): parity.execute_group_member_add,
    ("group", "member_remove"): parity.execute_group_member_remove,
    ("sla_policy", "create"): parity.execute_sla_policy_create,
    ("sla_policy", "update"): parity.execute_sla_policy_update,
    ("home_favorite", "put"): parity.execute_home_favorite_put,
    ("contact", "create"): parity.execute_contact_create,
    ("contact", "update"): parity.execute_contact_update,
    ("user_profile", "update"): parity.execute_user_profile_update,
    ("interaction_room", "resolve"): parity.execute_room_resolve,
    ("interaction_room", "rename"): parity.execute_room_rename,
    ("interaction_room", "member_add"): parity.execute_room_member_add,
    ("interaction_room", "member_remove"): (
        parity.execute_room_member_remove
    ),
    ("interaction_room", "mark_read"): parity.execute_room_mark_read,
    ("interaction_message", "post"): parity.execute_message_post,
    ("interaction_message", "update"): parity.execute_message_update,
    ("interaction_message", "reaction_set"): (
        lambda **kw: parity.execute_message_reaction(**kw)
    ),
    ("interaction_message", "reaction_clear"): (
        lambda **kw: parity.execute_message_reaction(clear=True, **kw)
    ),
    ("interaction_message", "pin"): (
        lambda **kw: parity.execute_message_pin(**kw)
    ),
    ("interaction_message", "unpin"): (
        lambda **kw: parity.execute_message_pin(unpin=True, **kw)
    ),
}


def tool_execute(
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
) -> CallToolResult:
    """Semantic ACT — governed writes via the official use cases.

    Same authorization as the REST routes: human principal +
    ``commercial.access``/``commercial.manage`` re-checked per call;
    manage-gated actions fail with 403. Executions run directly when
    authorized — no repetitive conversational confirmations. Backend
    consent/approval policies of each owner contract still apply.
    """
    entry, error = _resolve(entity, action, tool="execute")
    if error:
        return error
    try:
        bridge._require_commercial_human()
        merged: dict[str, Any] = {}
        for source in (payload, changes):
            for key, value in (source or {}).items():
                if key not in entry.fields:
                    return _err(
                        f"Campo '{key}' não é argumento de "
                        f"{entry.capability}.",
                        code="validation",
                        data={"allowed_fields": list(entry.fields)},
                    )
                merged[key] = value
        if entry.ref_arg:
            if not (target_ref or "").strip():
                return _err(
                    f"target_ref ({entry.ref_arg}) é obrigatório "
                    f"para {entry.capability}.",
                    code="validation",
                )
            merged[entry.ref_arg] = target_ref.strip()
        missing = [
            f
            for f in entry.required_fields
            if merged.get(f) is None
        ]
        if missing:
            return _err(
                f"Campos obrigatórios ausentes para "
                f"{entry.capability}: {', '.join(missing)}.",
                code="validation",
                data={
                    "missing_fields": missing,
                    "required_fields": list(entry.required_fields),
                },
            )
        handler = _EXECUTE_DISPATCH.get((entry.entity, entry.action))
        if handler is None:
            return _err(
                f"Ação '{entry.capability}' não possui contrato de "
                "escrita ativado nesta superfície.",
                status_code=501,
                code="not_implemented",
                data={"capability": entry.capability},
            )
        data = handler(**merged)
        result: dict[str, Any] = {
            "entity": entry.entity,
            "action": entry.action,
            "executed": True,
            "data": data,
            "write_policy": (
                "backend_authorized; audit trail do owner; "
                "notifications oficiais preservadas"
            ),
        }
        if idempotency_key is not None or expected_version is not None:
            result["concurrency"] = {
                "idempotency_key_received": (
                    idempotency_key is not None
                ),
                "expected_version_received": (
                    expected_version is not None
                ),
                "enforcement": (
                    "owner_contract — o MCP não adiciona camada "
                    "própria de idempotência/versionamento; "
                    "garantias seguem o use case oficial."
                ),
            }
        return _ok(result, "Operação executada.")
    except Exception as exc:
        return _handle_error(exc)


# --- delete (sealed prepare→commit only) ----------------------------------------

# capability → (impact_builder, executor). The prepare phase loads the
# entity through the owner use case to compute an honest impact; commit
# re-validates the sealed proposal before executing.
_DELETE_SPEC: dict[str, tuple[Any, Any]] = {
    "portfolio.deactivate": (
        lambda target: parity.portfolio_delete_impact(
            capability="portfolio.deactivate", portfolio_id=target
        ),
        lambda target, args: parity.delete_portfolio_deactivate(
            portfolio_id=target
        ),
    ),
    "portfolio.purge": (
        lambda target: parity.portfolio_delete_impact(
            capability="portfolio.purge", portfolio_id=target
        ),
        lambda target, args: parity.delete_portfolio_purge(
            portfolio_id=target
        ),
    ),
    "group.delete": (
        lambda target: parity.group_delete_impact(group_id=target),
        lambda target, args: parity.delete_group(group_id=target),
    ),
    "task.delete": (
        lambda target: parity.task_delete_impact(task_id=target),
        lambda target, args: parity.delete_task(task_id=target),
    ),
    "interaction_room.delete": (
        lambda target: parity.room_delete_impact(room_id=target),
        lambda target, args: parity.delete_room(room_id=target),
    ),
    "interaction_message.delete": (
        lambda target: parity.message_delete_impact(
            room_id=(args_of(target).get("room_id") or ""),
            message_id=(args_of(target).get("message_id") or ""),
        ),
        lambda target, args: parity.delete_message(
            room_id=args["room_id"],
            message_id=args["message_id"],
        ),
    ),
    "contact.delete": (
        lambda target: {
            "contact_id": args_of(target).get("contact_id"),
            "customer_code": args_of(target).get("customer_code"),
            "customer_store": args_of(target).get("customer_store"),
            "effect": "Exclusão (soft) do contato da conta.",
        },
        lambda target, args: parity.delete_contact(
            contact_id=args["contact_id"],
            customer_code=args["customer_code"],
            customer_store=args["customer_store"],
        ),
    ),
    "sla_policy.deactivate": (
        lambda target: parity.sla_policy_delete_impact(policy_id=target),
        lambda target, args: parity.delete_sla_policy_deactivate(
            policy_id=target
        ),
    ),
    "attachment.delete": (
        lambda target: parity.attachment_delete_impact(
            attachment_id=target
        ),
        lambda target, args: parity.delete_attachment(
            attachment_id=target
        ),
    ),
    "user_profile.photo_delete": (
        lambda target: parity.user_profile_photo_delete_impact(
            user_id=target
        ),
        lambda target, args: parity.delete_user_profile_photo(
            user_id=target
        ),
    ),
}


def args_of(target_ref: str) -> dict[str, str]:
    """Parse compound target refs ``key=value&key=value`` — never a
    URL, never arbitrary identifiers."""
    out: dict[str, str] = {}
    for part in (target_ref or "").split("&"):
        if "=" in part:
            key, _, value = part.partition("=")
            out[key.strip()] = value.strip()
    return out


def _delete_args(
    capability: str, target_ref: str
) -> tuple[str, dict[str, str]]:
    """Resolve the concrete target + extra args for a delete."""
    if capability in {
        "interaction_message.delete",
        "contact.delete",
    }:
        args = args_of(target_ref)
        return target_ref, args
    return target_ref, {}


def tool_delete(
    *,
    entity: str,
    action: str | None = None,
    target_ref: str,
    proposal_ref: str | None = None,
    phase: str | None = None,
) -> CallToolResult:
    """Semantic destructive ACT — sealed prepare→commit only.

    ``phase=prepare`` validates the target through the owner use case
    and returns a sealed, actor-bound, expiring, single-use
    ``proposal_ref`` plus the honest impact. ``phase=commit`` executes
    only with the exact handle — ``confirmed=true`` model-side is
    never proof.
    """
    act = (action or "delete").strip().lower()
    entry, error = _resolve(entity, act, tool="delete")
    if error:
        return error
    capability = entry.capability
    spec = _DELETE_SPEC.get(capability)
    if spec is None:
        return _err(
            f"Ação '{capability}' não possui contrato de exclusão "
            "ativado nesta superfície.",
            status_code=501,
            code="not_implemented",
            data={"capability": capability},
        )
    if not (target_ref or "").strip():
        return _err(
            "target_ref é obrigatório para exclusões.",
            code="validation",
        )
    impact_builder, executor = spec
    normalized_phase = (phase or "").strip().lower()
    try:
        bridge._require_commercial_human()
        request = bridge.build_mcp_request()
        actor = bridge.actor_sub_from_request(request) or ""
        if not actor:
            raise PermissionError("Unauthorized")

        if normalized_phase == "commit":
            # Atomic claim under the store lock: validate + consume in
            # one critical section — a concurrent/replayed commit of
            # the same handle can never pass twice. The executor runs
            # strictly after the claim so the destructive call can
            # never execute before single-use is enforced.
            proposal = proposal_store.claim_valid_proposal(
                proposal_handle=proposal_ref or "",
                actor_id=actor,
                expected_capability=capability,
                expected_target_ref=target_ref.strip(),
            )
            args = dict(proposal.meta.get("args") or {})
            logger.info(
                "caio_delete_commit capability=%s proposal_id=%s "
                "actor=%s target=%s",
                capability,
                proposal.proposal_id,
                actor,
                proposal.target_ref,
            )
            data = executor(target_ref.strip(), args)
            logger.info(
                "caio_delete_committed capability=%s proposal_id=%s",
                capability,
                proposal.proposal_id,
            )
            return _ok(
                {
                    "entity": entry.entity,
                    "action": entry.action,
                    "deleted": True,
                    "data": data,
                    "proposal_id": proposal.proposal_id,
                    "write_policy": (
                        "sealed_proposal_commit; backend_authorized"
                    ),
                },
                "Exclusão executada.",
            )

        # Default / prepare: seal the proposal for the exact target.
        target, args = _delete_args(capability, target_ref.strip())
        impact = impact_builder(target)
        proposal, handle = proposal_store.seal_proposal(
            capability=capability,
            actor_id=actor,
            target_ref=target_ref.strip(),
            change={
                "capability": capability,
                "target_ref": target_ref.strip(),
            },
            impact=impact,
            expected_postcondition={"deleted": True},
            meta={"args": args},
        )
        return _ok(
            {
                "entity": entry.entity,
                "action": entry.action,
                "phase": "prepare",
                "proposal_ref": handle,
                "proposal": proposal.to_public_dict(),
            },
            "Proposta de exclusão selada — confirme com phase=commit.",
        )
    except proposal_store.CaioProposalError as exc:
        return _err(
            str(exc),
            status_code=exc.status_code,
            code=exc.code,
            data=exc.detail,
        )
    except Exception as exc:
        return _handle_error(exc)
