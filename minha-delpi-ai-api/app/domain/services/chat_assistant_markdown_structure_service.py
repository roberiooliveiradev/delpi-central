"""Normalize delivered assistant Markdown so block markers are line-start ATX/GFM."""

from __future__ import annotations

import re


class ChatAssistantMarkdownStructureService:
    """Single owner for structural Markdown repair before persist/composition/MFE render.

    Sentence-level strip/dedupe and LLM mid-line headings must not leave
    ``text. ## Heading`` (ATX only renders when ``##`` starts a line).
    """

    _FENCE_RE = re.compile(r"(```[\s\S]*?```|~~~[\s\S]*?~~~)")
    # Mid-line ATX: any non-newline/non-hash before the run (covers ``. ##`` and ``—##``).
    # ``(?<![#\n])`` / lookbehind excludes already-valid line-start ``##`` and the 2nd ``#``.
    _INLINE_HEADING_RE = re.compile(r"(?<=[^\n#])[ \t]*(#{1,6}[ \t]+\S)")
    # Lists: only after sentence/clause punctuation (avoids ``a - b`` prose dashes).
    _INLINE_UL_RE = re.compile(r"(?<=[.!?:;])[ \t]+([-*+][ \t]+\S)")
    _INLINE_OL_RE = re.compile(r"(?<=[.!?:;])[ \t]+(\d+\.[ \t]+\S)")
    _MULTI_BLANK_RE = re.compile(r"\n{3,}")

    @classmethod
    def has_inline_block_marker(cls, text: str | None) -> bool:
        body = str(text or "")

        if not body:
            return False

        for chunk in cls._iter_non_fence_chunks(body):
            if cls._INLINE_HEADING_RE.search(chunk):
                return True

            if cls._INLINE_UL_RE.search(chunk):
                return True

            if cls._INLINE_OL_RE.search(chunk):
                return True

        return False

    @classmethod
    def normalize_delivered_markdown(cls, text: str | None) -> str:
        body = str(text or "")

        if not body.strip():
            return body.strip()

        parts: list[str] = []
        cursor = 0

        for match in cls._FENCE_RE.finditer(body):
            parts.append(cls._normalize_prose_chunk(body[cursor : match.start()]))
            parts.append(match.group(0))
            cursor = match.end()

        parts.append(cls._normalize_prose_chunk(body[cursor:]))
        normalized = "".join(parts)
        normalized = cls._MULTI_BLANK_RE.sub("\n\n", normalized)

        return normalized.strip()

    @classmethod
    def _iter_non_fence_chunks(cls, text: str):
        cursor = 0

        for match in cls._FENCE_RE.finditer(text):
            if match.start() > cursor:
                yield text[cursor : match.start()]

            cursor = match.end()

        if cursor < len(text):
            yield text[cursor:]

    @classmethod
    def _normalize_prose_chunk(cls, chunk: str) -> str:
        if not chunk:
            return chunk

        out = cls._INLINE_HEADING_RE.sub(r"\n\n\1", chunk)
        out = cls._INLINE_UL_RE.sub(r"\n\n\1", out)
        out = cls._INLINE_OL_RE.sub(r"\n\n\1", out)

        return out
