"""Deterministic capability retrieval over the projected surface
(doc 217, T2). BM25-style scoring over name/description/owner —
eval-scoped, library-neutral; LlamaIndex NOT_ADOPTED (not installed;
BM25 baseline is the required first comparator).
"""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import Iterable, Mapping, NamedTuple

_TOKEN = re.compile(r"[a-z0-9_]{2,}", re.IGNORECASE)


def _tokens(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN.findall(text or "")]


class RankedCapability(NamedTuple):
    group_key: str
    capability_id: str
    remote_name: str
    score: float


def _doc_text(group, capability) -> str:
    return " ".join(
        str(p)
        for p in (
            capability.remote_name,
            capability.description or "",
            group.display_name or "",
            group.owner_ref or "",
        )
        if p
    )


def rank_capabilities(
    query: str,
    surface: Iterable[tuple[str, object]],
    groups: Mapping[str, object],
    *,
    top_k: int = 8,
) -> list[tuple[str, object]]:
    """BM25-style rank of (group_key, ProviderCapability) pairs.

    Deterministic, corpus-free; multi-tool recall preserved via
    top_k bound (never forced to top-1).
    """
    items = list(surface)
    if not items:
        return []
    docs = [_tokens(_doc_text(groups[gk], cap)) for gk, cap in items]
    query_terms = set(_tokens(query))
    if not query_terms:
        return items[:top_k]
    n_docs = len(docs)
    df = Counter()
    for doc in docs:
        for t in set(doc):
            df[t] += 1
    avg_len = sum(len(d) for d in docs) / max(n_docs, 1)
    k1, b = 1.5, 0.75
    scored: list[tuple[float, int]] = []
    for idx, doc in enumerate(docs):
        tf = Counter(doc)
        score = 0.0
        for t in query_terms:
            if t not in tf:
                continue
            idf = math.log(
                1 + (n_docs - df[t] + 0.5) / (df[t] + 0.5)
            )
            score += idf * (tf[t] * (k1 + 1)) / (
                tf[t] + k1 * (1 - b + b * len(doc) / max(avg_len, 1))
            )
        scored.append((score, idx))
    scored.sort(key=lambda x: (-x[0], x[1]))
    top = [i for i, (s, _) in enumerate(scored) if s > 0]
    keep = scored if not top else scored[: max(min(top_k, len(top)), 3)]
    return [items[i] for _, i in keep[:top_k]]
