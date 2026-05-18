import math
import re
from collections import Counter


_TOKEN_PATTERN = re.compile(r"[a-z0-9áàâãéêíóôõúç]+", re.IGNORECASE)


def tokenize(value: str) -> list[str]:
    return [token.lower() for token in _TOKEN_PATTERN.findall(str(value or "")) if len(token) >= 3]


def keyword_overlap_score(query: str, content: str) -> float:
    query_tokens = tokenize(query)

    if not query_tokens:
        return 0.0

    content_tokens = Counter(tokenize(content))
    hits = sum(content_tokens.get(token, 0) for token in query_tokens)

    if hits <= 0:
        return 0.0

    return hits / (hits + math.log1p(len(query_tokens) * 4))
