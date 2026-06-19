"""Extração de cotas e decapes com tolerância a ruído OCR — Onda 14.6."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_drawing_tolerance_service import ChatDrawingToleranceService

_BUNDLE = "drawing_stamp"


class ChatDrawingDimensionsExtractionService:
    @classmethod
    def extract_dimensions(cls, text: str) -> dict[str, float | None]:
        normalized = cls._normalize_ocr_text(text)
        dimensions: dict[str, float | None] = {
            "totalLengthMm": None,
            "leftDecapeMm": None,
            "rightDecapeMm": None,
        }
        segment_lengths: list[float] = []
        cota_decape_values: list[float] = []

        if not normalized:
            return dimensions

        dimensions["totalLengthMm"] = cls._first_number(
            normalized,
            patterns=ChatDrawingPatternsService.length_patterns(),
            label_hints=ChatAssistantContentService.list(
                _BUNDLE,
                "dimensionLabels",
                "totalLength",
            ),
        )
        dimensions["leftDecapeMm"] = cls._first_number(
            normalized,
            patterns=ChatDrawingPatternsService.decape_left_patterns(),
        )
        dimensions["rightDecapeMm"] = cls._first_number(
            normalized,
            patterns=ChatDrawingPatternsService.decape_right_patterns(),
        )

        if dimensions["leftDecapeMm"] is None and dimensions["rightDecapeMm"] is None:
            generic = cls._first_number(
                normalized,
                patterns=(ChatDrawingPatternsService.generic_decape(),),
            )

            if generic is not None:
                dimensions["leftDecapeMm"] = generic

        note_decape = cls._first_number(
            normalized,
            patterns=(ChatDrawingPatternsService.decape_note(),),
        )

        if note_decape is not None:
            if dimensions["leftDecapeMm"] is None:
                dimensions["leftDecapeMm"] = note_decape

            if dimensions["rightDecapeMm"] is None:
                dimensions["rightDecapeMm"] = note_decape

        machine_decape = cls._first_number(
            normalized,
            patterns=(ChatDrawingPatternsService.decape_machine_side(),),
        )

        if machine_decape is not None:
            dimensions["leftDecapeMm"] = machine_decape

        cota_pattern = ChatDrawingPatternsService.cota_decape_length()

        for match in cota_pattern.finditer(normalized):
            decape = cls._parse_number(match.group(1))
            length = cls._parse_number(match.group(2))

            if decape is not None:
                cota_decape_values.append(decape)

            if decape is not None and dimensions["leftDecapeMm"] is None:
                dimensions["leftDecapeMm"] = decape

            if decape is not None and dimensions["rightDecapeMm"] is None:
                dimensions["rightDecapeMm"] = decape

            if length is not None:
                segment_lengths.append(length)

        if cota_decape_values:
            dimensions["cotaDecapeValuesMm"] = list(dict.fromkeys(cota_decape_values))

        if segment_lengths and dimensions["totalLengthMm"] is None:
            dimensions["totalLengthMm"] = max(segment_lengths)

        if segment_lengths:
            dimensions["segmentLengthsMm"] = segment_lengths

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

        resolved: dict[str, float | None | list[float]] = {
            "totalLengthMm": merged.get("totalLengthMm"),
            "leftDecapeMm": merged.get("leftDecapeMm"),
            "rightDecapeMm": merged.get("rightDecapeMm"),
            "segmentLengthsMm": merged.get("segmentLengthsMm") or [],
            "cotaDecapeValuesMm": merged.get("cotaDecapeValuesMm") or [],
        }

        for key in ("totalLengthMm", "leftDecapeMm", "rightDecapeMm"):
            if resolved[key] is None and region_dims.get(key) is not None:
                resolved[key] = region_dims[key]

            if resolved[key] is None and fallback_dims.get(key) is not None:
                resolved[key] = fallback_dims[key]

        if not resolved["segmentLengthsMm"]:
            for source in (region_dims, fallback_dims):
                segments = source.get("segmentLengthsMm") if isinstance(source, dict) else None

                if segments:
                    resolved["segmentLengthsMm"] = segments
                    break

        if not resolved["cotaDecapeValuesMm"]:
            for source in (region_dims, fallback_dims):
                cota_values = (
                    source.get("cotaDecapeValuesMm") if isinstance(source, dict) else None
                )

                if cota_values:
                    resolved["cotaDecapeValuesMm"] = cota_values
                    break

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
            tail_pattern = ChatDrawingPatternsService.hint_number_tail()

            for label in label_hints:
                idx = upper.find(label.upper())

                if idx < 0:
                    continue

                tail = text[idx : idx + 80]
                number_match = tail_pattern.search(tail)

                if number_match:
                    parsed = cls._parse_number(number_match.group(1))

                    if parsed is not None:
                        return parsed

        return None

    @classmethod
    def _parse_number(cls, raw: str) -> float | None:
        compact = re.sub(r"\s+", "", str(raw or ""))
        return ChatDrawingToleranceService.parse_mm(compact)
