"""Lexical retrieval over authorized DAVI-eligible technical actions."""

from __future__ import annotations

from collections.abc import Sequence

from app.application.external_capabilities.dynamic_information.catalog_builder import (
    TechnicalAction,
)
from app.application.external_capabilities.dynamic_information.content_loader import (
    load_external_read_allowlist,
)
from app.application.external_capabilities.dynamic_information.read_only_intent_guard import (
    has_explicit_write_intent,
)
from app.application.external_capabilities.dynamic_information.text_normalize import (
    normalize_text,
    tokenize,
)


def _quarantine_tokens() -> set[str]:
    payload = load_external_read_allowlist()
    raw = payload.get("retrievalQuarantineTokens") or []
    tokens: set[str] = set()
    for item in raw:
        tokens |= tokenize(str(item))
    return tokens


def _query_has_foreign_quarantine(query: str, action: TechnicalAction) -> bool:
    """True when query expresses a quarantined intent the action does not own."""
    q_tokens = tokenize(query)
    quarantine = _quarantine_tokens()
    foreign = q_tokens & quarantine
    if not foreign:
        return False
    action_tokens = tokenize(action.searchable_text)
    # Suppress only markers the action itself does not advertise.
    return bool(foreign - action_tokens)


def score_action(query: str, action: TechnicalAction) -> float:
    if _query_has_foreign_quarantine(query, action):
        return 0.0

    q_tokens = tokenize(query)
    if not q_tokens:
        return 0.0

    hay_tokens = tokenize(action.searchable_text)
    if not hay_tokens:
        return 0.0

    # Phrase boost: full normalized aliases / multi-word hints contained in query.
    norm_query = normalize_text(query)
    phrase_hits = 0
    for alias in action.semantic_aliases:
        alias_n = normalize_text(alias)
        if len(alias_n) >= 4 and alias_n in norm_query:
            phrase_hits += 1

    overlap = q_tokens & hay_tokens
    if not overlap and phrase_hits == 0:
        text = normalize_text(action.searchable_text)
        partial = sum(1 for t in q_tokens if t in text)
        if partial == 0:
            return 0.0
        return float(partial) / float(len(q_tokens)) * 0.5

    base = float(len(overlap)) / float(len(q_tokens)) if overlap else 0.0
    if phrase_hits:
        base = max(base, min(1.0, 0.55 + 0.15 * phrase_hits))
    return min(1.0, base)


def retrieve_eligible_actions(
    query: str,
    actions: Sequence[TechnicalAction],
    *,
    top_k: int,
) -> list[tuple[TechnicalAction, float]]:
    # Explicit mutation intent is semantically outside the READ broker.
    # This is not AuthZ — backend authorization remains authoritative.
    if has_explicit_write_intent(query):
        return []

    # Governance filter BEFORE ranking (eligible only).
    eligible = [a for a in actions if a.executable]
    scored = [(a, score_action(query, a)) for a in eligible]
    scored = [(a, s) for a, s in scored if s > 0]
    scored.sort(key=lambda pair: (-pair[1], pair[0].operation_id))
    return scored[: max(0, top_k)]
