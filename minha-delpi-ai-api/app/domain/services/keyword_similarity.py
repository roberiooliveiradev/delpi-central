import math
import re
from collections import Counter


_TOKEN_PATTERN = re.compile(r"[a-z0-9áàâãéêíóôõúç]+", re.IGNORECASE)


def tokenize(value: str) -> list[str]:
    return [token.lower() for token in _TOKEN_PATTERN.findall(str(value or "")) if len(token) >= 3]


def significant_query_tokens(
    query: str,
    *,
    stopwords: set[str] | frozenset[str] | None = None,
    max_terms: int = 8,
) -> list[str]:
    """Tokens úteis para FTS/ILIKE — remove stopwords de pergunta (dizem, sobre, …)."""
    stopped = {str(item).strip().lower() for item in (stopwords or ()) if str(item).strip()}
    seen: set[str] = set()
    out: list[str] = []
    for token in tokenize(query):
        if token in stopped or token in seen:
            continue
        seen.add(token)
        out.append(token)
        if len(out) >= max(1, int(max_terms)):
            break
    return out


def keyword_overlap_score(query: str, content: str) -> float:
    query_tokens = tokenize(query)

    if not query_tokens:
        return 0.0

    content_tokens = Counter(tokenize(content))
    # Cobertura de termos distintos (não frequência) — evita doc longo com 1 token
    # comum (ex.: «delpi») vencer o documento que cobre «normas»+«técnicas».
    hits = sum(1 for token in query_tokens if content_tokens.get(token, 0) > 0)

    if hits <= 0:
        return 0.0

    return hits / (hits + math.log1p(len(query_tokens) * 4))


def keyword_overlap_score_significant(
    query: str,
    content: str,
    *,
    stopwords: set[str] | frozenset[str] | None = None,
) -> float:
    """Overlap só com tokens significativos (melhor ranking documental)."""
    query_tokens = significant_query_tokens(query, stopwords=stopwords, max_terms=16)

    if not query_tokens:
        return keyword_overlap_score(query, content)

    content_tokens = Counter(tokenize(content))
    hits = sum(1 for token in query_tokens if content_tokens.get(token, 0) > 0)

    if hits <= 0:
        return 0.0

    return hits / (hits + math.log1p(len(query_tokens) * 4))
