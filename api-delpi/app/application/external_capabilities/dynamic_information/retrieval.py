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
    ordered_tokens,
    tokenize,
)
def _quarantine_tokens() -> set[str]:
    payload = load_external_read_allowlist()
    raw = payload.get("retrievalQuarantineTokens") or []
    tokens: set[str] = set()
    for item in raw:
        tokens |= tokenize(str(item))
    return tokens


def _owned_quarantine_tokens_via_aliases(
    query: str,
    action: TechnicalAction,
    quarantine: set[str],
) -> set[str]:
    """Quarantine ownership comes from precise semantic aliases, not token bags.

    A bare quarantined token in summary/description/operationId/searchable_text
    does not grant ownership. Multiword aliases that actually appear in the
    query may own the quarantined tokens they contain.
    """
    owned: set[str] = set()
    for alias in action.semantic_aliases:
        alias_n = normalize_text(alias)
        alias_tokens = tokenize(alias)
        if not alias_n or not alias_tokens:
            continue
        quarantined_in_alias = alias_tokens & quarantine
        if not quarantined_in_alias:
            continue
        if len(alias_tokens) < 2:
            continue
        if _alias_matches_query(alias, query):
            owned |= quarantined_in_alias
    return owned


def _query_has_foreign_quarantine(query: str, action: TechnicalAction) -> bool:
    """True when query expresses a quarantined intent the action does not own."""
    q_tokens = tokenize(query)
    quarantine = _quarantine_tokens()
    foreign = q_tokens & quarantine
    if not foreign:
        return False
    owned = _owned_quarantine_tokens_via_aliases(query, action, quarantine)
    return bool(foreign - owned)


def _alias_matches_query(alias: str, query: str) -> bool:
    """True when alias appears as a contiguous token sequence in the query.

    Avoids false positives where short aliases like ``cliente`` match inside
    ``clientes`` via raw substring containment.
    """
    alias_tokens = ordered_tokens(alias)
    query_tokens = ordered_tokens(query)
    if not alias_tokens or not query_tokens:
        return False
    window = len(alias_tokens)
    if window > len(query_tokens):
        return False
    for idx in range(len(query_tokens) - window + 1):
        if query_tokens[idx : idx + window] == alias_tokens:
            return True
    return False


def score_action(query: str, action: TechnicalAction) -> float:
    if _query_has_foreign_quarantine(query, action):
        return 0.0

    q_tokens = tokenize(query)
    if not q_tokens:
        return 0.0

    hay_tokens = tokenize(action.searchable_text)
    if not hay_tokens:
        return 0.0

    # Phrase boost: full aliases as contiguous token sequences in the query.
    # Longer precise aliases outrank short ones so "OTD por cliente" beats bare
    # "cliente" without operationId hardcodes (generic retrieval quality).
    best_phrase_len = 0
    phrase_hits = 0
    for alias in action.semantic_aliases:
        alias_n = normalize_text(alias)
        if len(alias_n) < 4:
            continue
        if not _alias_matches_query(alias, query):
            continue
        phrase_hits += 1
        best_phrase_len = max(best_phrase_len, len(alias_n))

    overlap = q_tokens & hay_tokens
    if not overlap and phrase_hits == 0:
        text = normalize_text(action.searchable_text)
        partial = sum(1 for t in q_tokens if t in text)
        if partial == 0:
            return 0.0
        return min(0.84, float(partial) / float(len(q_tokens)) * 0.5)

    overlap_score = float(len(overlap)) / float(len(q_tokens)) if overlap else 0.0
    if phrase_hits:
        # Base from hit count, then prefer the longest matching alias.
        return min(
            1.0,
            0.86
            + 0.03 * min(phrase_hits, 3)
            + 0.002 * min(best_phrase_len, 48),
        )
    return min(0.84, overlap_score)


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
