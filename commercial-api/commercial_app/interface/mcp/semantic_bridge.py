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
- ``execute``/``delete`` — public tools with a deny-by-default
  internal surface in v1: no write contract is activated yet, so
  every operation answers ``not_implemented`` honestly.
"""

from __future__ import annotations

import json
import logging
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
from commercial_app.interface.mcp import tool_bridge as bridge
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
        if key not in {"page", "page_size"}:
            return {}, _err(
                f"Campo de paginação '{key}' não suportado.",
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
            "act_enabled": False,
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
                    "Operações de escrita exigem contrato governado "
                    "ativado pelo owner — em v1 não há operação ativa "
                    "e a resposta é not_implemented honesta."
                ),
                "delete": (
                    "Exclusões sempre exigirão proposta selada "
                    "prepare→commit quando contratos forem ativados — "
                    "em v1 respondem not_implemented."
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
    ("customer", "list"): lambda a: bridge.tool_customer_list(**a),
    ("open_order", "list"): lambda a: bridge.tool_open_order_list(**a),
    ("open_order", "recently_closed"): (
        lambda a: bridge.tool_open_order_recently_closed(**a)
    ),
    ("proposal", "list"): lambda a: bridge.tool_proposal_list(**a),
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
        unknown = set(params) - {
            "seller_id", "portfolio_id", "scope_mode", "customer_codes",
            "start_date", "end_date", "branch", "customer_segment",
            "customer_centers",
        }
        if unknown:
            return _err(
                f"Parâmetros não suportados: {sorted(unknown)}.",
                code="validation",
            )
        params["question"] = question
        return handler(params)
    except Exception as exc:
        return _handle_error(exc)


_ANALYZE_DISPATCH = {
    "portfolio.open_summary": (
        lambda p: bridge.analyze_open_portfolio_summary(**p)
    ),
    "portfolio.open_horizon": (
        lambda p: bridge.analyze_open_portfolio_horizon(**p)
    ),
    "rol.summary": lambda p: bridge.analyze_rol_summary(**p),
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


def tool_knowledge(
    *,
    topic: str,
    task: str | None = None,
    query: str | None = None,
) -> CallToolResult:
    """Versioned owner-authorized Commercial guidance."""
    try:
        bridge._require_commercial_human()
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
            "Conhecimento comercial versionado.",
        )
    except Exception as exc:
        return _handle_error(exc)


# --- execute / delete (deny-by-default v1) -----------------------------------


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
    """Semantic ACT — deny-by-default until write contracts activate."""
    entry, error = _resolve(entity, action, tool="execute")
    if error:
        return error
    # Unreachable in v1: no execute action is status=proven.
    return _err(
        f"Ação '{entry.capability}' não possui contrato de escrita "
        "ativado nesta superfície.",
        status_code=501,
        code="not_implemented",
        data={"capability": entry.capability},
    )


def tool_delete(
    *,
    entity: str,
    target_ref: str,
    proposal_ref: str | None = None,
    phase: str | None = None,
) -> CallToolResult:
    """Semantic destructive ACT — deny-by-default in v1."""
    entry, error = _resolve(entity, "delete", tool="delete")
    if error:
        return error
    # Unreachable in v1: no delete action is status=proven.
    return _err(
        f"Ação '{entry.capability}' não possui contrato de exclusão "
        "ativado nesta superfície.",
        status_code=501,
        code="not_implemented",
        data={"capability": entry.capability},
    )
