"""Fusão de texto OCR multi-motor por região de desenho."""

from __future__ import annotations

import re
from typing import Iterable

from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService


class ChatPdfRegionOcrFusionService:
    @classmethod
    def fuse(cls, texts: Iterable[str]) -> str:
        ordered: list[str] = []

        for text in texts:
            stripped = str(text or "").strip()

            if stripped:
                ordered.append(stripped)

        if not ordered:
            return ""

        if len(ordered) == 1:
            return ordered[0]

        lines: list[str] = []
        seen: set[str] = set()
        code_pattern = ChatDrawingPatternsService.component_code()

        def line_score(line: str) -> tuple[int, int]:
            codes = code_pattern.findall(line)
            return (len(codes), len(line))

        candidates: dict[str, str] = {}

        for source in ordered:
            for line in source.splitlines():
                token = line.strip()

                if not token:
                    continue

                key = re.sub(r"\s+", " ", token.upper())

                existing = candidates.get(key)

                if not existing or line_score(token) > line_score(existing):
                    candidates[key] = token

        for token in sorted(
            candidates.values(),
            key=lambda value: (-line_score(value)[0], -line_score(value)[1], value),
        ):
            key = re.sub(r"\s+", " ", token.upper())

            if key in seen:
                continue

            seen.add(key)
            lines.append(token)

        return "\n".join(lines)
