"""Discover DELPI information — semantic retrieval over eligible technical actions."""

from __future__ import annotations

from typing import Any

from app.application.external_capabilities.dynamic_information.action_index import (
    get_technical_actions,
)
from app.application.external_capabilities.dynamic_information.argument_validator import (
    build_argument_json_schema,
)
from app.application.external_capabilities.dynamic_information.candidate_token import (
    CandidateTokenError,
    mint_candidate_token,
)
from app.application.external_capabilities.dynamic_information.content_loader import (
    candidate_token_secret,
    load_dynamic_read_budgets,
)
from app.application.external_capabilities.dynamic_information.retrieval import (
    retrieve_eligible_actions,
)


def discover_delpi_information(
    *,
    query: str,
    top_k: int | None = None,
    actor_id: str | None = None,
) -> dict[str, Any]:
    if not (query or "").strip():
        raise ValueError("query is required")
    if not (actor_id or "").strip():
        raise CandidateTokenError("actor_id is required")

    budgets = load_dynamic_read_budgets()
    default_k = int(budgets.get("discover_default_top_k") or 5)
    max_k = int(budgets.get("discover_max_top_k") or 10)
    ttl = int(budgets.get("candidate_token_ttl_seconds") or 300)
    requested = default_k if top_k is None else int(top_k)
    safe_k = max(1, min(requested, max_k))

    actions = get_technical_actions()
    ranked = retrieve_eligible_actions(query, actions, top_k=safe_k)
    secret = candidate_token_secret()

    candidates: list[dict[str, Any]] = []
    for action, score in ranked:
        arg_schema = build_argument_json_schema(action)
        required = list(arg_schema.get("required") or [])

        token = mint_candidate_token(
            action_id=action.action_id,
            actor_id=actor_id,
            secret=secret,
            ttl_seconds=ttl,
        )
        candidates.append(
            {
                "candidate_token": token,
                "description": action.summary or action.operation_id,
                "semantic_hints": {
                    "entity": action.entity,
                    "shape": action.shape,
                    "tags": list(action.tags),
                },
                "required_arguments": required,
                "argument_schema": arg_schema,
                "pagination_hints": {
                    "supports_page": "page" in (arg_schema.get("properties") or {}),
                    "supports_page_size": "page_size"
                    in (arg_schema.get("properties") or {}),
                },
                "retrieval_score": round(float(score), 4),
                # Technical ids for observability only — not for free selection.
                "action_id": action.action_id,
            }
        )

    return {
        "query": query.strip(),
        "top_k": safe_k,
        "candidate_count": len(candidates),
        "eligible_action_count": sum(1 for a in actions if a.executable),
        "candidates": candidates,
    }
