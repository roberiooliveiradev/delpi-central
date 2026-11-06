"""DAVI get_context — bounded context/catalog projection (semantic entry point).

Catalog/context metadata only: availability, versions, limits and schemas.
It never grants permission — backend AuthZ remains the authority for every
execution, and planned-but-unimplemented tools are reported as unavailable.
"""

from __future__ import annotations

from typing import Any

from app.application.external_capabilities.constants import (
    MCP_TOOL_CLASSES,
    MCP_TOOL_DISCOVER_DELPI_INFORMATION,
    MCP_TOOL_EXECUTE_DELPI_INFORMATION,
    MCP_TOOL_GET_CONTEXT,
    MCP_TOOL_KNOWLEDGE,
    MCP_TOOL_READ,
)
from app.application.external_capabilities.davi_agent_intelligence_service import (
    DaviAgentIntelligenceService,
)
from app.application.external_capabilities.dynamic_information.action_index import (
    get_action_by_id,
    get_technical_actions,
)
from app.application.external_capabilities.dynamic_information.argument_validator import (
    build_argument_json_schema,
)
from app.application.external_capabilities.dynamic_information.content_loader import (
    load_dynamic_read_budgets,
    load_external_read_allowlist,
)
from app.application.external_capabilities.dynamic_information.errors import (
    ARGUMENT_VALIDATION_CODE,
    GovernedExecutionError,
)
from scripts.davi_governed_knowledge_bundle_lib import (
    LATEST_CORPUS_VERSION,
    PUBLISHED_CORPUS_VERSIONS,
)

_CONTEXT_ACTIONS = frozenset({"context", "catalog", "schema"})

_AVAILABLE_TOOLS = (
    MCP_TOOL_GET_CONTEXT,
    MCP_TOOL_KNOWLEDGE,
    MCP_TOOL_READ,
    MCP_TOOL_DISCOVER_DELPI_INFORMATION,
    MCP_TOOL_EXECUTE_DELPI_INFORMATION,
)
# Sibling-pattern tools decided for later waves — reported honestly as
# unavailable so the model never invents them.
_PLANNED_TOOLS = ("analyze", "execute", "delete")

_BUDGET_KEYS = (
    "discover_default_top_k",
    "discover_max_top_k",
    "candidate_token_ttl_seconds",
    "execute_max_items",
    "execute_max_response_bytes",
    "default_page_size",
    "max_page_size",
    "projection_max_depth",
    "execute_max_resultsets",
    "execute_max_result_columns",
)


def _catalog_version() -> Any:
    return load_external_read_allowlist().get("version")


def _limits() -> dict[str, Any]:
    budgets = load_dynamic_read_budgets()
    return {key: budgets.get(key) for key in _BUDGET_KEYS if key in budgets}


def _context(actor_id: str | None) -> dict[str, Any]:
    return {
        "action": "context",
        "status": "ok",
        "identity": {
            "specialist": "DAVI — Especialista em Dados e Informações DELPI",
            "server": "api-delpi",
            "mission": (
                "consultar informações autorizadas da DELPI respeitando a "
                "identidade e as permissões do usuário"
            ),
        },
        "actor": {
            "authenticated": bool(actor_id),
            "id": actor_id or None,
        },
        "authority": {
            "model": "backend_first_authz",
            "catalog_is_not_permission": True,
            "note": (
                "Context and catalog are availability metadata only. Backend "
                "AuthZ decides every execution; nothing in this response "
                "grants access."
            ),
        },
        "tools": {
            "available": [
                {"name": name, "class": MCP_TOOL_CLASSES[name]}
                for name in _AVAILABLE_TOOLS
            ],
            "unavailable": [
                {"name": name, "status": "PLANNED_NOT_IMPLEMENTED"}
                for name in _PLANNED_TOOLS
            ],
        },
        "versions": {
            "catalog_allowlist": _catalog_version(),
            "agent_intelligence": DaviAgentIntelligenceService.version(),
            "knowledge_corpus_latest": LATEST_CORPUS_VERSION,
            "knowledge_corpus_published": sorted(PUBLISHED_CORPUS_VERSIONS),
        },
        "limits": _limits(),
        "capability_surface": DaviAgentIntelligenceService.capability_surface(),
    }


def _catalog() -> dict[str, Any]:
    actions = get_technical_actions()
    eligible = sorted(
        (a for a in actions if a.executable),
        key=lambda a: (str(a.entity or ""), a.action_id),
    )
    return {
        "action": "catalog",
        "status": "ok",
        "catalog_version": _catalog_version(),
        "indexed_action_count": len(actions),
        "eligible_action_count": len(eligible),
        "actions": [
            {
                "action_id": a.action_id,
                "description": a.summary or a.operation_id,
                "entity": a.entity,
                "shape": a.shape,
                "tags": list(a.tags),
            }
            for a in eligible
        ],
        "schema_on_demand": (
            "get_context action=schema with capability=<action_id> returns "
            "the governed argument schema; discover_delpi_information "
            "resolves natural-language needs into candidate tokens."
        ),
        "authority": "catalog metadata — not permission",
    }


def _capability_schema(capability: str | None) -> dict[str, Any]:
    requested = (capability or "").strip()
    if not requested:
        raise GovernedExecutionError(
            "capability is required for action=schema",
            code=ARGUMENT_VALIDATION_CODE,
        )
    action = get_action_by_id(requested)
    capability_payload: dict[str, Any] = {"id": requested}
    payload: dict[str, Any] = {
        "action": "schema",
        "status": "ok",
        "capability": capability_payload,
    }
    if action is None or not action.executable:
        capability_payload.update(
            {
                "available": False,
                "davi_status": action.davi_status if action is not None else "UNKNOWN",
                "message": (
                    "capability is not available on the governed DAVI surface"
                ),
            }
        )
        return payload
    argument_schema = build_argument_json_schema(action)
    capability_payload.update(
        {
            "available": True,
            "davi_status": action.davi_status,
            "entity": action.entity,
            "shape": action.shape,
            "description": action.summary or action.operation_id,
            "required_arguments": list(argument_schema.get("required") or []),
            "argument_schema": argument_schema,
        }
    )
    return payload


def davi_get_context(
    *,
    action: str = "context",
    capability: str | None = None,
    actor_id: str | None = None,
) -> dict[str, Any]:
    normalized = (action or "context").strip()
    if normalized not in _CONTEXT_ACTIONS:
        raise GovernedExecutionError(
            f"Unknown get_context action: {normalized!r}. "
            f"Allowed: {sorted(_CONTEXT_ACTIONS)}",
            code=ARGUMENT_VALIDATION_CODE,
        )
    if normalized == "schema":
        return _capability_schema(capability)
    if normalized == "catalog":
        return _catalog()
    return _context(actor_id)
