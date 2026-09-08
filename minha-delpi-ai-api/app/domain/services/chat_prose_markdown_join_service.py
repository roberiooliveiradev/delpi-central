"""Join prose sentence fragments without collapsing Markdown block structure."""

from __future__ import annotations

import re


class ChatProseMarkdownJoinService:
    """Sentence-level strip/dedupe often splits on `. `; rejoin must not glue headings/lists."""

    _BLOCK_START_RE = re.compile(
        r"^(?:"
        r"#{1,6}\s"  # ATGs
        r"|[-*+]\s"  # unordered list
        r"|\d+\.\s"  # ordered list
        r"|>\s"  # blockquote
        r"\|"  # table row
        r"|```"  # fence
        r")"
    )

    @classmethod
    def is_block_start(cls, text: str) -> bool:
        return bool(cls._BLOCK_START_RE.match(str(text or "").lstrip()))

    @classmethod
    def join_sentence_fragments(cls, fragments: list[str] | tuple[str, ...]) -> str:
        parts = [str(part or "").strip() for part in fragments if str(part or "").strip()]

        if not parts:
            return ""

        chunks: list[str] = [parts[0]]

        for part in parts[1:]:
            if cls.is_block_start(part):
                chunks.append(f"\n\n{part}")
            else:
                chunks.append(f" {part}")

        return "".join(chunks).strip()
