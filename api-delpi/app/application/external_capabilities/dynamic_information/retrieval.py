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

# Portuguese function/filler words that often appear between durable semantic
# tokens in natural questions without changing phrase identity.
# Intentionally excludes content markers such as ``por`` (OTD por cliente) and
# ``mais`` (clientes mais faturaram).
_PHRASE_FILLERS = frozenset(
    {
        "a",
        "ao",
        "aos",
        "as",
        "com",
        "como",
        "da",
        "das",
        "de",
        "do",
        "dos",
        "e",
        "em",
        "essa",
        "esse",
        "esta",
        "este",
        "estes",
        "estas",
        "esta",
        "estao",
        "foi",
        "foram",
        "ja",
        "lhe",
        "liste",
        "longo",
        "me",
        "mostre",
        "na",
        "nas",
        "neste",
        "nesta",
        "no",
        "nos",
        "nossa",
        "nossas",
        "nosso",
        "nossos",
        "o",
        "os",
        "ou",
        "para",
        "pela",
        "pelas",
        "pelo",
        "pelos",
        "que",
        "quero",
        "se",
        "sem",
        "sua",
        "suas",
        "um",
        "uma",
        "umas",
        "uns",
        "ver",
        "veio",
        "vieram",
    }
)


def _quarantine_tokens() -> set[str]:
    payload = load_external_read_allowlist()
    raw = payload.get("retrievalQuarantineTokens") or []
    tokens: set[str] = set()
    for item in raw:
        tokens |= tokenize(str(item))
    return tokens


def _tokens_compatible(left: str, right: str) -> bool:
    """Conservative PT singular/plural and shared-stem compatibility."""
    if left == right:
        return True
    if len(left) > 3 and len(right) > 3:
        left_stem = left[:-1] if left.endswith("s") and not left.endswith("ss") else left
        right_stem = (
            right[:-1] if right.endswith("s") and not right.endswith("ss") else right
        )
        if left_stem == right_stem:
            return True
    # Verb/noun derivation pairs (faturamos/faturamento, evoluiu/evolucao).
    if len(left) >= 5 and len(right) >= 5 and left[:5] == right[:5]:
        suffixes = ("mos", "ram", "iu", "ou", "cao", "sao", "mento", "veis")
        if any(left.endswith(suf) or right.endswith(suf) for suf in suffixes):
            return True
    return False


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


def _exact_window_match(needle: list[str], haystack: list[str]) -> bool:
    window = len(needle)
    if window == 0 or window > len(haystack):
        return False
    for idx in range(len(haystack) - window + 1):
        chunk = haystack[idx : idx + window]
        if all(_tokens_compatible(a, b) for a, b in zip(needle, chunk, strict=True)):
            return True
    return False


def _filler_tolerant_match(alias_tokens: list[str], query_tokens: list[str]) -> bool:
    """Match alias content tokens in order, allowing PT fillers between them.

    Alias and query are reduced to non-filler tokens so articles/prepositions
    inside aliases (``de``, ``dos``) do not block natural paraphrases.
    Does not skip arbitrary content tokens.
    """
    alias_content = [t for t in alias_tokens if t not in _PHRASE_FILLERS]
    query_content = [t for t in query_tokens if t not in _PHRASE_FILLERS]
    if len(alias_content) < 2 or not query_content:
        return False
    return _exact_window_match(alias_content, query_content)

def _alias_matches_query(alias: str, query: str) -> bool:
    """True when alias appears as an ordered semantic phrase in the query.

    Prefers contiguous token windows, then allows Portuguese fillers/stopwords
    between durable alias tokens. Avoids raw substring false positives.
    """
    alias_tokens = ordered_tokens(alias)
    query_tokens = ordered_tokens(query)
    if not alias_tokens or not query_tokens:
        return False
    if _exact_window_match(alias_tokens, query_tokens):
        return True
    if len(alias_tokens) < 2:
        return False
    return _filler_tolerant_match(alias_tokens, query_tokens)


def score_action(query: str, action: TechnicalAction) -> float:
    if _query_has_foreign_quarantine(query, action):
        return 0.0

    q_tokens = tokenize(query)
    if not q_tokens:
        return 0.0

    hay_tokens = tokenize(action.searchable_text)
    if not hay_tokens:
        return 0.0

    # Phrase boost: full aliases as ordered semantic phrases in the query.
    # Longer precise aliases outrank short ones so "OTD por cliente" beats bare
    # "cliente" without operationId hardcodes (generic retrieval quality).
    best_multiword_len = 0
    multiword_hits = 0
    best_single_len = 0
    single_hits = 0
    for alias in action.semantic_aliases:
        alias_n = normalize_text(alias)
        if len(alias_n) < 4:
            continue
        if not _alias_matches_query(alias, query):
            continue
        alias_tok_count = len(ordered_tokens(alias))
        if alias_tok_count <= 1:
            single_hits += 1
            best_single_len = max(best_single_len, len(alias_n))
        else:
            multiword_hits += 1
            best_multiword_len = max(best_multiword_len, len(alias_n))

    overlap = q_tokens & hay_tokens
    if not overlap and multiword_hits == 0 and single_hits == 0:
        text = normalize_text(action.searchable_text)
        partial = sum(1 for t in q_tokens if t in text)
        if partial == 0:
            return 0.0
        return min(0.84, float(partial) / float(len(q_tokens)) * 0.5)

    overlap_score = float(len(overlap)) / float(len(q_tokens)) if overlap else 0.0
    if multiword_hits:
        # Prefer the longest matching multiword alias. Hit-count is only a light
        # tie-breaker so several short overlaps cannot beat one precise phrase.
        return min(
            1.0,
            0.86
            + 0.0025 * min(best_multiword_len, 72)
            + 0.005 * min(multiword_hits, 2),
        )
    if single_hits:
        # Cap one-token alias boosts so generic tokens like "estoque"/"produtos"
        # do not outrank multiword analytic intents on natural questions.
        return min(
            0.78,
            0.70 + 0.002 * min(best_single_len, 24),
        )
    return min(0.84, overlap_score)


def _best_multiword_alias_len(query: str, action: TechnicalAction) -> int:
    best = 0
    for alias in action.semantic_aliases:
        alias_n = normalize_text(alias)
        if len(ordered_tokens(alias)) <= 1:
            continue
        if len(alias_n) < 4:
            continue
        if _alias_matches_query(alias, query):
            best = max(best, len(alias_n))
    return best


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
    scored.sort(
        key=lambda pair: (
            -pair[1],
            -_best_multiword_alias_len(query, pair[0]),
            pair[0].operation_id,
        )
    )
    return scored[: max(0, top_k)]
