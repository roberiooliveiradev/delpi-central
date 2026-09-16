"""Lexical retrieval over authorized DAVI-eligible technical actions."""

from __future__ import annotations

import re
from collections.abc import Sequence

from app.application.external_capabilities.dynamic_information.catalog_builder import (
    TechnicalAction,
)

_TOKEN_RE = re.compile(r"[a-z0-9_]+", re.IGNORECASE)


def _tokens(text: str) -> set[str]:
    return {t.lower() for t in _TOKEN_RE.findall(text or "") if len(t) > 1}


def score_action(query: str, action: TechnicalAction) -> float:
    q_tokens = _tokens(query)
    if not q_tokens:
        return 0.0
    hay = _tokens(action.searchable_text)
    if not hay:
        return 0.0
    overlap = q_tokens & hay
    if not overlap:
        # soft partial: substring of query words in searchable text
        text = action.searchable_text
        partial = sum(1 for t in q_tokens if t in text)
        return float(partial) / float(len(q_tokens)) * 0.5
    return float(len(overlap)) / float(len(q_tokens))


def retrieve_eligible_actions(
    query: str,
    actions: Sequence[TechnicalAction],
    *,
    top_k: int,
) -> list[tuple[TechnicalAction, float]]:
    eligible = [a for a in actions if a.executable]
    scored = [(a, score_action(query, a)) for a in eligible]
    scored = [(a, s) for a, s in scored if s > 0]
    scored.sort(key=lambda pair: (-pair[1], pair[0].operation_id))
    return scored[: max(0, top_k)]
