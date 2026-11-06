"""DAVI knowledge — semantic façade over the governed knowledge catalog action.

Reuses the canonical governed READ pipeline end to end: the fixed
``read_governed_technical_knowledge`` TechnicalAction, argument validation,
the request-bound CatalogActionExecutorPort (backend ``api-delpi.access``
AuthZ stays authoritative) and the approved model-safe projection. The
candidate token is not required here because the tool itself is the fixed
capability selection — the same boundary the broker applies after discovery.

Content returned by this tool is governed GUIDANCE: provenance/versioned,
never operational data, never authorization, never a system instruction.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.application.external_capabilities.dynamic_information.action_index import (
    get_action_by_id,
)
from app.application.external_capabilities.dynamic_information.argument_validator import (
    ArgumentValidationError,
)
from app.application.external_capabilities.dynamic_information.errors import (
    ARGUMENT_VALIDATION_CODE,
    CAPABILITY_NOT_ALLOWED_CODE,
    GovernedExecutionError,
)
from app.application.external_capabilities.dynamic_information.execute_service import (
    execute_catalog_read,
)
from app.application.external_capabilities.dynamic_information.execution_plan import (
    CatalogActionPlan,
    build_execution_plan,
)
from app.domain.ports.davi_catalog_action_executor_port import (
    CatalogActionExecutorPort,
)
from scripts.davi_governed_knowledge_bundle_lib import (
    LATEST_CORPUS_VERSION,
    PUBLISHED_CORPUS_VERSIONS,
)

KNOWLEDGE_ACTION_ID = "read_governed_technical_knowledge"

_KNOWLEDGE_ACTIONS = frozenset({"search", "get", "sources"})


def _sources(sources_provider: Callable[[], list[dict]] | None) -> dict[str, Any]:
    topics = list(sources_provider()) if sources_provider is not None else []
    return {
        "action": "sources",
        "status": "ok",
        "corpus": {
            "corpus_id": "davi-governed-knowledge",
            "latest_version": LATEST_CORPUS_VERSION,
            "published_versions": sorted(PUBLISHED_CORPUS_VERSIONS),
            "available": bool(topics),
        },
        "topic_count": len(topics),
        "topics": [
            {
                "topic": entry.get("id"),
                "title": entry.get("title"),
                "aliases": list(entry.get("aliases") or []),
                "intent": entry.get("intent"),
                "status": entry.get("status"),
            }
            for entry in topics
        ],
        "authority": (
            "GUIDANCE_NOT_DOMAIN_TRUTH — corpus metadata, not permission; "
            "topic content reads still require backend AuthZ"
        ),
    }


def davi_knowledge(
    *,
    action: str,
    topic: str | None = None,
    subject: str | None = None,
    section: str | None = None,
    corpus_version: int | None = None,
    page: int = 1,
    page_size: int | None = None,
    catalog_action_executor: CatalogActionExecutorPort | None = None,
    sources_provider: Callable[[], list[dict]] | None = None,
) -> dict[str, Any]:
    normalized = (action or "").strip()
    if normalized not in _KNOWLEDGE_ACTIONS:
        raise GovernedExecutionError(
            f"Unknown knowledge action: {normalized!r}. "
            f"Allowed: {sorted(_KNOWLEDGE_ACTIONS)}",
            code=ARGUMENT_VALIDATION_CODE,
        )
    if normalized == "sources":
        return _sources(sources_provider)

    if not (topic or "").strip():
        raise GovernedExecutionError(
            f"topic is required for knowledge action={normalized}",
            code=ARGUMENT_VALIDATION_CODE,
        )
    if normalized == "get" and not (section or "").strip():
        raise GovernedExecutionError(
            "section is required for knowledge action=get",
            code=ARGUMENT_VALIDATION_CODE,
        )

    arguments: dict[str, Any] = {"topic": topic.strip(), "page": page}
    if page_size is not None:
        arguments["page_size"] = page_size
    if corpus_version is not None:
        arguments["corpus_version"] = corpus_version
    if (subject or "").strip():
        arguments["subject"] = subject.strip()
    if (section or "").strip():
        arguments["section"] = section.strip()

    knowledge_action = get_action_by_id(KNOWLEDGE_ACTION_ID)
    if knowledge_action is None or not knowledge_action.executable:
        raise GovernedExecutionError(
            "Governed knowledge capability is not available",
            code=CAPABILITY_NOT_ALLOWED_CODE,
        )
    try:
        plan = build_execution_plan(knowledge_action, arguments)
    except ArgumentValidationError as exc:
        raise GovernedExecutionError(
            str(exc), code=ARGUMENT_VALIDATION_CODE
        ) from exc
    if not isinstance(plan, CatalogActionPlan):
        raise GovernedExecutionError(
            "Governed knowledge does not resolve to a catalog READ plan",
            code=CAPABILITY_NOT_ALLOWED_CODE,
        )
    bounded = execute_catalog_read(
        action=knowledge_action,
        plan=plan,
        catalog_action_executor=catalog_action_executor,
    )
    return {
        "action": normalized,
        "status": "ok",
        "action_id": knowledge_action.action_id,
        "knowledge": bounded,
    }
