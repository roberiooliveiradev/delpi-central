# app/infrastructure/persistence/totvs/product_repositories/product_description_matching.py

"""Bounded industrial-description matching for the TOTVS SB1 catalog.

Task: DELIA-C3-API-DELPI-PRODUCT-SEARCH-REMEDIATION-01 (doc 203
owner-remediation). Replaces substring OR-matching with:

- AND semantics: every significant query token must match.
- Word-prefix matching: a token matches only at a word boundary
  (description start or after a non-alphanumeric character), so
  ``BALA`` cannot reach interior substrings.
- Controlled abbreviation bridging: a small domain-approved
  equivalence table maps tokens to alternate surface forms
  (e.g. TERMINAL <-> TERM). Abbreviated members require an
  exact-word match so ``TERM`` never prefix-matches ``TERMO*``.
- Relevance scoring favors exact-word and phrase-prefix matches.
"""

_WORD_BOUNDARY = "[^A-Z0-9]"
_EDGE_PUNCT = ".,;:/()_-\"'"
_ESCAPE = "\\"

# Domain-approved equivalence table (both directions). Keep this map
# small and reviewed; members with the ``exact`` style only match as a
# whole word, which is what protects abbreviations like TERM from
# colliding with TERMO*, TERMINALO, etc.
_ABBREVIATION_MEMBERS = {
    "TERM": (("TERM", "exact"), ("TERMINAL", "prefix")),
    "TERMINAL": (("TERMINAL", "prefix"), ("TERM", "exact")),
}

# Portuguese connectives with no product-identity meaning. Dropped from
# multi-token queries so connectors cannot force impossible AND clauses.
_QUERY_STOPWORDS = frozenset(
    {"DE", "DA", "DO", "DAS", "DOS", "E", "EM", "PARA", "COM", "SEM",
     "POR", "OU", "A", "O"}
)


def _escape_like(term: str) -> str:
    return (
        term.replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
        .replace("[", "\\[")
    )


def normalize_description_tokens(description: str) -> list[str]:
    """Uppercase, strip edge punctuation, drop stopwords (with fallback)."""
    tokens = [
        t.strip(_EDGE_PUNCT).upper() for t in description.strip().split()
    ]
    tokens = [t for t in tokens if t]
    significant = [t for t in tokens if t not in _QUERY_STOPWORDS]
    return significant or tokens


def _word_prefix_clause(col: str) -> str:
    # Leading pad turns the description start into a word boundary, so
    # one LIKE covers both positions.
    return f"(CONCAT(' ', {col}) LIKE ? ESCAPE '{_ESCAPE}')"


def _word_prefix_params(term: str) -> list[str]:
    return [f"%{_WORD_BOUNDARY}{_escape_like(term)}%"]


def _exact_word_clause(col: str) -> str:
    # Padding both ends makes start/end of field behave as boundaries;
    # a single LIKE then covers start, middle, end and whole-field.
    return f"(CONCAT(' ', {col}, ' ') LIKE ? ESCAPE '{_ESCAPE}')"


def _exact_word_params(term: str) -> list[str]:
    p = _escape_like(term)
    b = _WORD_BOUNDARY
    return [f"%{b}{p}{b}%"]


def _token_members(token: str) -> tuple[tuple[str, str], ...]:
    return _ABBREVIATION_MEMBERS.get(token, ((token, "prefix"),))


def build_description_matching(
    description: str, column: str = "SB1.B1_DESC"
) -> tuple[str, list[str], str, list[str]] | None:
    """Build the WHERE clause and relevance score for a description.

    Returns ``(where_clause, where_params, score_sql, score_params)`` or
    ``None`` when the description carries no usable token.
    """
    tokens = normalize_description_tokens(description)
    if not tokens:
        return None

    col = f"{column} COLLATE Latin1_General_CI_AI"
    where_parts: list[str] = []
    where_params: list[str] = []
    score_parts: list[str] = []
    score_params: list[str] = []

    # Phrase bonuses apply only to multi-token phrases and require a
    # word boundary after the phrase. For a single token, "description
    # starts with token" is indistinguishable from word-prefix noise
    # (BALANCA outranking BALA) — exact-word scoring must decide alone.
    if len(tokens) > 1:
        raw_phrase = _escape_like(description.strip())
        score_parts.append(
            f"CASE WHEN {col} LIKE ? ESCAPE '{_ESCAPE}' "
            f"OR {col} LIKE ? ESCAPE '{_ESCAPE}' THEN 100 ELSE 0 END"
        )
        score_params.append(f"{raw_phrase}{_WORD_BOUNDARY}%")
        score_params.append(raw_phrase)

        normalized_phrase = " ".join(tokens)
        score_parts.append(
            f"CASE WHEN REPLACE({col}, '.', '') LIKE ? ESCAPE '{_ESCAPE}' "
            f"OR REPLACE({col}, '.', '') LIKE ? ESCAPE '{_ESCAPE}' "
            "THEN 60 ELSE 0 END"
        )
        score_params.append(
            f"{_escape_like(normalized_phrase)}{_WORD_BOUNDARY}%"
        )
        score_params.append(_escape_like(normalized_phrase))

    for token in tokens:
        members = _token_members(token)
        token_alts: list[str] = []
        exact_alts: list[str] = []
        prefix_alts: list[str] = []
        for word, style in members:
            if style == "exact":
                token_alts.append(_exact_word_clause(col))
                exact_alts.append(_exact_word_clause(col))
            else:
                token_alts.append(_word_prefix_clause(col))
                prefix_alts.append(_word_prefix_clause(col))
        where_parts.append("(" + " OR ".join(token_alts) + ")")
        for word, style in members:
            if style == "exact":
                where_params.extend(_exact_word_params(word))
            else:
                where_params.extend(_word_prefix_params(word))

        # Score: exact-word hits outrank mere word-prefix hits.
        exact_test_alts = list(
            dict.fromkeys([token] + [w for w, _ in members])
        )
        exact_tests = " OR ".join(
            _exact_word_clause(col) for _ in exact_test_alts
        )
        score_parts.append(
            f"CASE WHEN {exact_tests} THEN 30 ELSE 0 END"
        )
        for word in exact_test_alts:
            score_params.extend(_exact_word_params(word))
        if prefix_alts:
            score_parts.append(
                f"CASE WHEN ({' OR '.join(prefix_alts)}) THEN 15 ELSE 0 END"
            )
            for word, style in members:
                if style == "prefix":
                    score_params.extend(_word_prefix_params(word))

    return (
        " AND ".join(where_parts),
        where_params,
        " + ".join(score_parts),
        score_params,
    )
