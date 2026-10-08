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
    # Shared 6-char prefix covers gerund/flexion families (entregando/entrega,
    # consultando/consulta) without uncontrolled stemming on short tokens.
    if len(left) >= 6 and len(right) >= 6 and left[:6] == right[:6]:
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


def _bounded_subsequence_match(
    needle: list[str], haystack: list[str], *, max_gap: int = 1
) -> bool:
    """Ordered subsequence match with bounded content-token gaps.

    Every alias token must appear in order; consecutive matches may be
    separated by at most ``max_gap`` intervening content tokens, covering
    natural PT-BR modifiers inserted inside a phrase (``estoque atual do
    produto`` vs alias ``estoque do produto``) without skipping arbitrary
    content indefinitely.
    """
    pos = 0
    for idx, token in enumerate(needle):
        limit = (
            len(haystack) if idx == 0 else min(pos + max_gap + 1, len(haystack))
        )
        found = None
        for j in range(pos, limit):
            if _tokens_compatible(token, haystack[j]):
                found = j
                break
        if found is None:
            return False
        pos = found + 1
    return True


def _filler_tolerant_match(alias_tokens: list[str], query_tokens: list[str]) -> bool:
    """Match alias content tokens in order, allowing PT fillers between them.

    Alias and query are reduced to non-filler tokens so articles/prepositions
    inside aliases (``de``, ``dos``) do not block natural paraphrases.
    A bounded-gap ordered subsequence tolerates at most two intervening
    content tokens between consecutive alias terms; arbitrary content is
    never skipped.
    """
    alias_content = [t for t in alias_tokens if t not in _PHRASE_FILLERS]
    query_content = [t for t in query_tokens if t not in _PHRASE_FILLERS]
    if len(alias_content) < 2 or not query_content:
        return False
    if _exact_window_match(alias_content, query_content):
        return True
    return _bounded_subsequence_match(alias_content, query_content)

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


def _catalog_idf(actions: Sequence[TechnicalAction]) -> dict[str, float]:
    """Deterministic per-token specificity over the eligible catalog.

    Document frequency counts in how many actions a token appears (searchable
    text + semantic aliases). Specificity is ``log((N+1)/(df+1))`` normalized
    to [0, 1]: ubiquitous tokens such as ``produto`` score near 0, rare
    domain tokens such as ``otd`` near 1. No manual token weights.
    """
    import math
    from collections import Counter

    docs: list[set[str]] = []
    for action in actions:
        tokens = tokenize(action.searchable_text)
        for alias in action.semantic_aliases:
            tokens |= tokenize(alias)
        docs.append(tokens)
    total = max(1, len(docs))
    df = Counter()
    for doc in docs:
        df.update(doc)
    norm = math.log(total + 1)
    if norm <= 0:
        return {}
    return {
        token: math.log((total + 1) / (count + 1)) / norm
        for token, count in df.items()
    }


def score_action(
    query: str,
    action: TechnicalAction,
    token_idf: dict[str, float] | None = None,
) -> float:
    if _query_has_foreign_quarantine(query, action):
        return 0.0

    # Trusted negative phrases: an action may declare multiword intents outside
    # its semantic scope (e.g. row-record access on metadata actions). Only
    # multiword phrases are honored so normal single Portuguese tokens can
    # never be banned per-action.
    for negative in action.negative_aliases:
        if (
            len(ordered_tokens(negative)) >= 2
            and _alias_matches_query(negative, query)
        ):
            return 0.0

    q_tokens = tokenize(query)
    if not q_tokens:
        return 0.0

    hay_tokens = tokenize(action.searchable_text)
    if not hay_tokens:
        return 0.0

    idf = token_idf or {}
    specificity = lambda t: idf.get(t, 0.5)  # noqa: E731 - bounded local use

    # Pure filler tokens (da/os/me/mostre/…) appear in almost every haystack.
    # A candidate whose overlap is ONLY filler tokens is lexical noise, not a
    # semantic match, so it is suppressed below without altering the scoring
    # of queries that share at least one durable content token.

    # Phrase boost: full aliases as ordered semantic phrases in the query.
    # Longer precise aliases outrank short ones so "OTD por cliente" beats bare
    # "cliente" without operationId hardcodes (generic retrieval quality).
    best_multiword_len = 0
    multiword_hits = 0
    best_single_len = 0
    best_single_spec = 0.0
    single_hits = 0
    for alias in action.semantic_aliases:
        alias_n = normalize_text(alias)
        if len(alias_n) < 3:
            continue
        if not _alias_matches_query(alias, query):
            continue
        alias_tok_count = len(ordered_tokens(alias))
        if alias_tok_count <= 1:
            single_hits += 1
            best_single_len = max(best_single_len, len(alias_n))
            best_single_spec = max(
                best_single_spec, max(specificity(t) for t in tokenize(alias))
            )
        else:
            multiword_hits += 1
            best_multiword_len = max(best_multiword_len, len(alias_n))

    overlap = q_tokens & hay_tokens
    if not (overlap - _PHRASE_FILLERS) and multiword_hits == 0 and single_hits == 0:
        if overlap:
            # Filler-only overlap: suppress instead of emitting a junk candidate.
            return 0.0
        text = normalize_text(action.searchable_text)
        partial = sum(1 for t in q_tokens if t in text)
        # Substring-level traces alone are noise below half coverage.
        if float(partial) / float(len(q_tokens)) < 0.5:
            return 0.0
        return min(0.84, float(partial) / float(len(q_tokens)) * 0.5)

    # Specificity-weighted coverage: generic overlap (``produto``, ``dados``)
    # counts little; rare domain tokens carry the evidence. Unsupported
    # requests whose coverage is only generic fall below the admission floor.
    if overlap:
        # Intent mass comes from durable content tokens only; function words
        # (liste/os/de) are rare in catalog text, which would inflate the
        # denominator and wrongly depress real coverage.
        content_tokens = q_tokens - _PHRASE_FILLERS
        q_mass = sum(specificity(t) for t in content_tokens)
        if q_mass <= 0:
            # Degenerate specificity (tiny/uniform catalog): fall back to
            # plain coverage instead of dividing by a meaningless mass.
            denom = float(len(content_tokens) or len(q_tokens))
            overlap_score = float(len(overlap - _PHRASE_FILLERS)) / denom
        else:
            overlap_score = (
                sum(specificity(t) for t in overlap - _PHRASE_FILLERS) / q_mass
            )
    else:
        overlap_score = 0.0

    if multiword_hits:
        # Prefer the longest matching multiword alias; same-length ties fall
        # through to the deterministic operation_id ordering.
        return min(
            1.0,
            0.86 + 0.0025 * min(best_multiword_len, 72),
        )
    if single_hits:
        # A lone generic alias token with otherwise-uncovered query content is
        # noise, not intent ("saldo da conta corrente" is not product stock).
        if overlap_score < 0.25:
            return 0.0
        # An action that claims the token via a governed alias must not rank
        # below one that merely contains the token in searchable text.
        alias_score = min(0.78, 0.62 + 0.16 * best_single_spec)
        return max(alias_score, min(0.84, overlap_score))
    if overlap_score < 0.50:
        # Weak generic-token noise only: not enough specific evidence to
        # surface the action as a candidate.
        return 0.0
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
    token_idf = _catalog_idf(eligible)
    scored = [(a, score_action(query, a, token_idf)) for a in eligible]
    scored = [(a, s) for a, s in scored if s > 0]
    scored.sort(
        key=lambda pair: (
            -pair[1],
            -_best_multiword_alias_len(query, pair[0]),
            pair[0].operation_id,
        )
    )
    return scored[: max(0, top_k)]
