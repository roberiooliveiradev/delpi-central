from __future__ import annotations

import hashlib
import html
import re
from typing import Protocol

from app.application.external_capabilities.dynamic_information.text_normalize import (
    normalize_text,
    ordered_tokens,
    tokenize,
    tokens_compatible,
)
from scripts.davi_governed_knowledge_bundle_lib import (
    LATEST_CORPUS_VERSION,
    PUBLISHED_CORPUS_VERSIONS,
)

# Subject addressability bounds (R7 contract): mirrors the concept-guard
# query budget. Deterministic lexical scoring only — no LLM, no index.
_SUBJECT_MAX_LEN = 240
# Minimum specificity of a matched term: document-ubiquitous tokens reach
# idf == 0, but a literal hit must still count as evidence.
_TERM_MIN_WEIGHT = 0.10
# PT function words ignored as subject evidence (content tokens only rank).
_SUBJECT_STOPWORDS = frozenset(
    {
        "a", "ao", "aos", "as", "com", "como", "da", "das", "de", "do",
        "dos", "e", "em", "na", "nas", "no", "nos", "o", "os", "ou",
        "para", "pela", "pelas", "pelo", "pelos", "por", "que", "se",
        "um", "uma", "umas", "uns", "qual", "quais", "me", "the", "of",
        "for", "and", "or", "in", "on", "to", "is", "are",
    }
)


class KnowledgeReadError(ValueError):
    def __init__(self, code: str, status_code: int):
        super().__init__(code)
        self.code = code
        self.status_code = status_code


class GovernedKnowledgeReader(Protocol):
    def load(self, corpus_version: int = 1) -> tuple[dict, dict, dict[str, bytes]]: ...


def _chunks(text: str) -> list[str]:
    text = html.escape(re.sub(r"[\x00-\x08\x0b-\x1f\x7f\u202a-\u202e\u2066-\u2069]", "", text), quote=False)
    raw = text.encode("utf-8")
    chunks = []
    while raw:
        piece = raw[:4096].decode("utf-8", errors="ignore")
        chunks.append(piece)
        raw = raw[len(piece.encode("utf-8")):]
    return chunks


def _excerpts(raw: bytes) -> list[dict]:
    lines = raw.decode("utf-8").splitlines(keepends=True)

    # Authorial intent heuristic (generic, document-derived): headings that
    # repeat in the document are structural part-headings ("Objetivo",
    # "Exemplo" appear once per family); unique headings name a family.
    # A repeated heading's context therefore keeps the last unique heading
    # it was nested under, restoring e.g. "Terminais (Genérico)" context to
    # its "Estrutura"/"Exemplo" leaf sections. Section ids stay the same
    # per-group sequence — only the provenance/context path is enriched.
    heading_counts: dict[str, int] = {}
    for line in lines:
        match = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if match:
            heading_counts[normalize_text(match.group(1))] = (
                heading_counts.get(normalize_text(match.group(1)), 0) + 1
            )

    groups = []
    heading = "Document"
    stack: dict[int, str] = {}
    last_unique: tuple[int, str, tuple[str, ...]] | None = None
    cur_level = 1
    start = 1
    body = []
    for number, line in enumerate(lines, 1):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match:
            level = len(match.group(1))
            if body:
                groups.append(
                    (heading, _heading_path(stack, heading, cur_level, heading_counts, last_unique), start, number - 1, "".join(body))
                )
                body = []
                start = number
            heading = match.group(2)
            cur_level = level
            stack = {k: v for k, v in stack.items() if k < level}
            stack[level] = heading
            if heading_counts[normalize_text(heading)] == 1:
                ancestors = tuple(
                    normalize_text(stack[k]) for k in sorted(stack) if k < level
                )
                last_unique = (level, heading, ancestors)
        body.append(line)
    if body:
        groups.append((heading, _heading_path(stack, heading, cur_level, heading_counts, last_unique), start, len(lines), "".join(body)))
    return [
        {"section": f"s{number:04d}", "heading": html.escape(heading[:160]),
         "heading_path": html.escape(path[:400]),
         "line_start": start, "line_end": end, "chunk": chunk_index,
         "text": text, "sanitized": True}
        for number, (heading, path, start, end, body) in enumerate(groups, 1)
        for chunk_index, text in enumerate(_chunks(body), 1)
    ]


def _heading_path(
    stack: dict[int, str], current: str, cur_level: int,
    heading_counts: dict[str, int],
    last_unique: tuple[int, str, tuple[str, ...]] | None,
) -> str:
    parts = [
        (level, stack[level]) for level in sorted(stack) if level < cur_level
    ]
    current_ancestors = tuple(normalize_text(name) for _, name in parts)
    in_path = set(current_ancestors)
    if (
        heading_counts.get(normalize_text(current), 0) > 1
        and last_unique is not None
        and last_unique[0] <= cur_level
        and last_unique[2] == current_ancestors
        and normalize_text(last_unique[1]) not in in_path
    ):
        parts.append((last_unique[0], last_unique[1]))
        parts.sort(key=lambda entry: entry[0])
    parts.append((cur_level, current))
    return " / ".join(name for _, name in parts)


def _subject_terms(subject: str) -> list[str]:
    """Durable content tokens of the subject; function words carry no evidence."""
    return [
        t for t in ordered_tokens(subject) if t not in _SUBJECT_STOPWORDS
    ]


def _section_idf(items: list[dict]) -> dict[str, float]:
    """Per-token specificity over the sections of ONE loaded document.

    Rare designations ("bala") dominate ubiquitous structure words
    ("terminais" appears under every family heading). Same deterministic
    ``log((N+1)/(df+1))`` profile as the action catalog — no manual weights.
    """
    import math
    from collections import Counter

    df = Counter()
    for item in items:
        df.update(tokenize(item["heading_path"] + " " + item["text"]))
    total = max(1, len(items))
    norm = math.log(total + 1)
    if norm <= 0:
        return {}
    return {
        token: math.log((total + 1) / (count + 1)) / norm
        for token, count in df.items()
    }


def _has_content(body: str) -> bool:
    """True when the section body carries text beyond its heading markup."""
    for line in body.splitlines():
        stripped = line.strip()
        if stripped and not re.match(r"^#{1,6}\s", stripped):
            return True
    return False


def _term_in_tokens(term: str, tokens: set[str]) -> bool:
    return any(tokens_compatible(term, candidate) for candidate in tokens)


def _section_relevance(
    terms: list[str], idf: dict[str, float], heading_path: str, body: str,
) -> float:
    """Deterministic section ranking over verified content only.

    Heading-path hits weigh 3x body hits; every hit is specificity-weighted
    so a rare designation outranks a generic family word. A contiguous
    multiword subject phrase earns a bounded bonus. Score in [0, 1]; zero
    means the section carries no evidence for the subject — it is dropped.
    """
    heading_tokens = tokenize(heading_path)
    body_tokens = tokenize(body)
    # A matched term can never contribute zero: tokens present in every
    # section reach idf == 0, yet a literal hit is still evidence. The
    # floor keeps ranking differences driven by heading hits and rarity.
    mass = sum(max(idf.get(t, 0.5), _TERM_MIN_WEIGHT) for t in terms) or 1.0
    score = 0.0
    for term in terms:
        spec = max(idf.get(term, 0.5), _TERM_MIN_WEIGHT)
        if _term_in_tokens(term, heading_tokens):
            score += 3.0 * spec
        if _term_in_tokens(term, body_tokens):
            score += spec
    if len(terms) >= 2:
        haystack = normalize_text(heading_path + " " + body)
        needle = " ".join(terms)
        if needle in haystack:
            score += 2.0 * mass
    return min(1.0, score / (4.5 * mass))


class ReadGovernedTechnicalKnowledgeUseCase:
    def __init__(self, repository: GovernedKnowledgeReader):
        self._repository = repository

    def execute(self, *, topic: str, section: str | None = None,
                corpus_version: int = LATEST_CORPUS_VERSION, page: int = 1, page_size: int = 3,
                subject: str | None = None) -> dict:
        if type(corpus_version) is not int or corpus_version not in PUBLISHED_CORPUS_VERSIONS:
            raise KnowledgeReadError("STALE_VERSION", 409)
        if type(page) is not int or type(page_size) is not int or not 1 <= page <= 10000 or not 1 <= page_size <= 3:
            raise KnowledgeReadError("VALIDATION_ERROR", 422)
        terms: list[str] | None = None
        if subject is not None:
            if type(subject) is not str or len(subject) > _SUBJECT_MAX_LEN:
                raise KnowledgeReadError("VALIDATION_ERROR", 422)
            terms = _subject_terms(subject)
            if not terms:
                raise KnowledgeReadError("VALIDATION_ERROR", 422)
        manifest, index, content = self._repository.load(corpus_version)
        selected = next((entry for entry in index["topics"] if entry["id"] == topic), None)
        if selected is None:
            raise KnowledgeReadError("NOT_FOUND", 404)
        source_path = selected["source_path"]
        raw = content[source_path]
        items = _excerpts(raw)
        if section is not None:
            items = [item for item in items if item["section"] == section]
            if not items:
                raise KnowledgeReadError("NOT_FOUND", 404)
        matched_terms: list[str] = []
        if terms is not None:
            # A section whose body is only its own heading carries no
            # substantive content — it cannot document a subject.
            candidates = [item for item in items if _has_content(item["text"])]
            idf = _section_idf(candidates)
            scored = [
                (idx, item, _section_relevance(
                    terms, idf, item["heading_path"], item["text"],
                ))
                for idx, item in enumerate(candidates)
            ]
            scored = [entry for entry in scored if entry[2] > 0]
            scored.sort(key=lambda entry: (-entry[2], entry[0]))
            items = [
                {**item, "relevance": round(score, 4)}
                for _, item, score in scored
            ]
            matched_tokens = set()
            for item in items:
                context = tokenize(item["heading_path"] + " " + item["text"])
                matched_tokens |= {
                    t for t in terms if _term_in_tokens(t, context)
                }
            matched_terms = sorted(matched_tokens, key=terms.index)
        offset = (page - 1) * page_size
        selected_items = items[offset:offset + page_size]
        response = {
            "knowledge_kind": "GUIDANCE", "authority": "GUIDANCE_NOT_DOMAIN_TRUTH",
            "trust_level": "UNTRUSTED_DOCUMENT_CONTENT", "content_format": "plain_text",
            "topic": topic, "corpus_version": manifest["corpus_version"],
            "corpus_id": manifest["corpus_id"], "manifest_identity": manifest["manifest_sha256"],
            "source_path": source_path, "source_git_sha": manifest["source_git_sha"],
            "source_sha256": hashlib.sha256(raw).hexdigest(),
            "items": selected_items, "page": page, "page_size": page_size,
            "total": len(items), "has_more": offset + page_size < len(items),
            "coverage": "PARTIAL" if len(selected_items) < len(items) else "COMPLETE_SELECTION",
            "selection": "section" if section else "document",
        }
        if terms is not None:
            response["subject"] = subject
            response["matched_terms"] = matched_terms
            response["unmatched_terms"] = [
                t for t in dict.fromkeys(terms) if t not in set(matched_terms)
            ]
            if not items:
                response["coverage"] = "NO_MATCH"
            response["selection"] = "subject+section" if section else "subject"
        return response
