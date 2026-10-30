"""SURI governed knowledge surface (S5).

Corpus: ``app/content/suri_knowledge.json`` — curated items derived from
the authorized Portal Suprimentos user manual and help content
(``plugins/supplies/src/content/userManualContent.ts`` et al.), each
item carrying verifiable citation (source file + locator) and evidence
classification. Read-only, deterministic, offline-searchable.
"""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

KNOWLEDGE_PATH = (
    Path(__file__).resolve().parents[2] / "content" / "suri_knowledge.json"
)

_EVIDENCE_CLASSES = {"PROVEN", "OWNER_REPORTED", "TO_INVENTORY"}


@lru_cache(maxsize=1)
def load_corpus() -> dict[str, Any]:
    raw = json.loads(KNOWLEDGE_PATH.read_text(encoding="utf-8"))
    items = raw.get("items") or []
    return {
        "corpus_version": int(raw.get("corpus_version") or 1),
        "corpus_sha256": hashlib.sha256(
            KNOWLEDGE_PATH.read_bytes()
        ).hexdigest(),
        "sources": raw.get("sources") or [],
        "items": [item for item in items if isinstance(item, dict)],
    }


def list_knowledge_sources() -> dict[str, Any]:
    corpus = load_corpus()
    return {
        "corpus_version": corpus["corpus_version"],
        "corpus_sha256": corpus["corpus_sha256"],
        "sources": corpus["sources"],
        "item_count": len(corpus["items"]),
    }


def get_knowledge_item(knowledge_id: str) -> dict[str, Any] | None:
    wanted = (knowledge_id or "").strip()
    if not wanted:
        return None
    for item in load_corpus()["items"]:
        if item.get("knowledge_id") == wanted:
            return _with_corpus_meta(item)
    return None


def search_knowledge(
    *,
    query: str | None = None,
    topic: str | None = None,
    limit: int = 8,
) -> dict[str, Any]:
    """Deterministic token-overlap search — no embeddings, no LLM."""
    corpus = load_corpus()
    topic_filter = (topic or "").strip().lower()
    terms = [
        token
        for token in (query or "").strip().lower().split()
        if len(token) >= 2
    ]
    scored: list[tuple[int, dict[str, Any]]] = []
    for item in corpus["items"]:
        if topic_filter and str(item.get("topic") or "").lower() != topic_filter:
            continue
        if not terms:
            scored.append((0, item))
            continue
        haystack = " ".join(
            str(item.get(key) or "")
            for key in ("title", "summary", "content", "topic")
        ).lower() + " " + " ".join(
            str(k) for k in (item.get("keywords") or [])
        ).lower()
        score = sum(haystack.count(term) for term in terms)
        if score > 0:
            scored.append((score, item))
    scored.sort(key=lambda pair: (-pair[0], str(pair[1].get("knowledge_id"))))
    capped = max(1, min(int(limit or 8), 20))
    hits = [
        {
            "knowledge_id": item.get("knowledge_id"),
            "title": item.get("title"),
            "summary": item.get("summary"),
            "topic": item.get("topic"),
            "evidence_class": item.get("evidence_class"),
            "source": item.get("source"),
        }
        for _score, item in scored[:capped]
    ]
    return {
        "corpus_version": corpus["corpus_version"],
        "corpus_sha256": corpus["corpus_sha256"],
        "query": query or "",
        "topic": topic or None,
        "total_matches": len(scored),
        "items": hits,
    }


def _with_corpus_meta(item: dict[str, Any]) -> dict[str, Any]:
    corpus = load_corpus()
    result = dict(item)
    result.setdefault("evidence_class", "OWNER_REPORTED")
    if result["evidence_class"] not in _EVIDENCE_CLASSES:
        result["evidence_class"] = "OWNER_REPORTED"
    result["corpus_version"] = corpus["corpus_version"]
    result["corpus_sha256"] = corpus["corpus_sha256"]
    return result
