from __future__ import annotations

import hashlib
import html
import re
from typing import Protocol

from scripts.davi_governed_knowledge_bundle_lib import (
    LATEST_CORPUS_VERSION,
    PUBLISHED_CORPUS_VERSIONS,
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
    groups = []
    heading = "Document"
    start = 1
    body = []
    for number, line in enumerate(lines, 1):
        match = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if match and body:
            groups.append((heading, start, number - 1, "".join(body)))
            body = []
            start = number
        if match:
            heading = match.group(1)
        body.append(line)
    if body:
        groups.append((heading, start, len(lines), "".join(body)))
    return [
        {"section": f"s{number:04d}", "heading": html.escape(heading[:160]),
         "line_start": start, "line_end": end, "chunk": chunk_index,
         "text": text, "sanitized": True}
        for number, (heading, start, end, body) in enumerate(groups, 1)
        for chunk_index, text in enumerate(_chunks(body), 1)
    ]


class ReadGovernedTechnicalKnowledgeUseCase:
    def __init__(self, repository: GovernedKnowledgeReader):
        self._repository = repository

    def execute(self, *, topic: str, section: str | None = None,
                corpus_version: int = LATEST_CORPUS_VERSION, page: int = 1, page_size: int = 3) -> dict:
        if type(corpus_version) is not int or corpus_version not in PUBLISHED_CORPUS_VERSIONS:
            raise KnowledgeReadError("STALE_VERSION", 409)
        if type(page) is not int or type(page_size) is not int or not 1 <= page <= 10000 or not 1 <= page_size <= 3:
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
        offset = (page - 1) * page_size
        selected_items = items[offset:offset + page_size]
        return {
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
