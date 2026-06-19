"""Extração de cotas e decapes com tolerância a ruído OCR — Onda 14.6."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_drawing_tolerance_service import ChatDrawingToleranceService

_BUNDLE = "drawing_stamp"

_LENGTH_PATTERNS = (
    re.compile(
        r"COMPR(?:IMENTO)?\s*(?:TOTAL)?\s*[:.]?\s*(\d[\d\s,.]*)\s*M{0,2}",
        re.IGNORECASE,
    ),
    re.compile(
        r"C\s*O\s*M\s*P\s*R(?:\s*I\s*M\s*E\s*N\s*T\s*O)?\s*(?:TOTAL)?\s*[:.]?\s*(\d[\d\s,.]*)\s*M{0,2}",
        re.IGNORECASE,
    ),
    re.compile(r"LENGTH\s*[:.]?\s*(\d[\d\s,.]*)\s*M{0,2}", re.IGNORECASE),
)

_DECAPE_LEFT_PATTERNS = (
    re.compile(
        r"DEC[A4@]PE?\s*E(?:SQUERD[OA])?\s*[:.]?\s*(\d[\d\s,.]*)",
        re.IGNORECASE,
    ),
    re.compile(
        r"D\s*E\s*C\s*A\s*P\s*E\s*E(?:SQUERD[OA])?\s*[:.]?\s*(\d[\d\s,.]*)",
        re.IGNORECASE,
    ),
)

_DECAPE_RIGHT_PATTERNS = (
    re.compile(
        r"DEC[A4@]PE?\s*D(?:IREIT[OA])?\s*[:.]?\s*(\d[\d\s,.]*)",
        re.IGNORECASE,
    ),
    re.compile(
        r"D\s*E\s*C\s*A\s*P\s*E\s*D(?:IREIT[OA])?\s*[:.]?\s*(\d[\d\s,.]*)",
        re.IGNORECASE,
    ),
)

_GENERIC_DECAPE_RE = re.compile(
    r"DEC[A4@]PE?\s*[:.]?\s*(\d[\d\s,.]*)\s*M{0,2}",
    re.IGNORECASE,
)


class ChatDrawingDimensionsExtractionService:
    @classmethod
    def extract_dimensions(cls, text: str) -> dict[str, float | None]:
        normalized = cls._normalize_ocr_text(text)
        dimensions: dict[str, float | None] = {
            "totalLengthMm": None,
            "leftDecapeMm": None,
            "rightDecapeMm": None,
        }

        if not normalized:
            return dimensions

        dimensions["totalLengthMm"] = cls._first_number(
            normalized,
            patterns=_LENGTH_PATTERNS,
            label_hints=ChatAssistantContentService.list(
                _BUNDLE,
                "dimensionLabels",
                "totalLength",
            ),
        )
        dimensions["leftDecapeMm"] = cls._first_number(
            normalized,
            patterns=_DECAPE_LEFT_PATTERNS,
        )
        dimensions["rightDecapeMm"] = cls._first_number(
            normalized,
            patterns=_DECAPE_RIGHT_PATTERNS,
        )

        if dimensions["leftDecapeMm"] is None and dimensions["rightDecapeMm"] is None:
            generic = cls._first_number(normalized, patterns=(_GENERIC_DECAPE_RE,))

            if generic is not None:
                dimensions["leftDecapeMm"] = generic

        return dimensions

    @classmethod
    def merge_dimensions(
        cls,
        base: dict[str, Any] | None,
        *,
        region_text: str = "",
        fallback_text: str = "",
    ) -> dict[str, float | None]:
        merged = dict(base) if isinstance(base, dict) else {}
        region_dims = cls.extract_dimensions(region_text) if region_text.strip() else {}
        fallback_dims = (
            cls.extract_dimensions(fallback_text)
            if fallback_text.strip() and not region_dims
            else {}
        )

        resolved: dict[str, float | None] = {
            "totalLengthMm": merged.get("totalLengthMm"),
            "leftDecapeMm": merged.get("leftDecapeMm"),
            "rightDecapeMm": merged.get("rightDecapeMm"),
        }

        for key in resolved:
            if resolved[key] is None and region_dims.get(key) is not None:
                resolved[key] = region_dims[key]

            if resolved[key] is None and fallback_dims.get(key) is not None:
                resolved[key] = fallback_dims[key]

        return resolved

    @classmethod
    def _normalize_ocr_text(cls, text: str) -> str:
        collapsed = re.sub(r"[ \t]+", " ", str(text or ""))
        return re.sub(r"\n{3,}", "\n\n", collapsed).strip()

    @classmethod
    def _first_number(
        cls,
        text: str,
        *,
        patterns: tuple[re.Pattern[str], ...],
        label_hints: list[str] | None = None,
    ) -> float | None:
        for pattern in patterns:
            match = pattern.search(text)

            if match:
                parsed = cls._parse_number(match.group(1))

                if parsed is not None:
                    return parsed

        if label_hints:
            upper = text.upper()

            for label in label_hints:
                idx = upper.find(label.upper())

                if idx < 0:
                    continue

                tail = text[idx : idx + 80]
                number_match = re.search(r"(\d[\d\s,.]*)\s*M{0,2}", tail, re.IGNORECASE)

                if number_match:
                    parsed = cls._parse_number(number_match.group(1))

                    if parsed is not None:
                        return parsed

        return None

    @classmethod
    def _parse_number(cls, raw: str) -> float | None:
        compact = re.sub(r"\s+", "", str(raw or ""))
        return ChatDrawingToleranceService.parse_mm(compact)
