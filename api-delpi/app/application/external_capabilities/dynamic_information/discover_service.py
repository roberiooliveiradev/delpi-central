"""Discover DELPI information — semantic retrieval over eligible technical actions."""

from __future__ import annotations

from typing import Any

from app.application.external_capabilities.dynamic_information.action_index import (
    get_technical_actions,
)
from app.application.external_capabilities.dynamic_information.candidate_token import (
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
        required = [
            p.get("name")
            for p in action.parameters
            if isinstance(p, dict) and p.get("required") and p.get("name")
        ]
        # Path params always required even when OpenAPI parameters omitted (baseline).
        for segment in action.path.split("/"):
            if segment.startswith("{") and segment.endswith("}"):
                name = segment[1:-1]
                if name not in required:
                    required.append(name)

        arg_schema: dict[str, Any] = {
            "type": "object",
            "additionalProperties": False,
            "properties": {},
            "required": required,
        }
        for name in required:
            arg_schema["properties"][name] = {"type": "string"}
        for p in action.parameters:
            if not isinstance(p, dict):
                continue
            name = p.get("name")
            if not name or name in arg_schema["properties"]:
                continue
            arg_schema["properties"][name] = {"type": "string"}

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
                    "supports_page": "page" in arg_schema["properties"],
                    "supports_page_size": "page_size" in arg_schema["properties"],
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
