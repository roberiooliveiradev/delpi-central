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
        normalized = cls._repair_glued_tolerance_cotas(cls._normalize_ocr_text(text))
        dimensions: dict[str, float | None] = {
            "totalLengthMm": None,
            "leftDecapeMm": None,
            "rightDecapeMm": None,
        }
        segment_lengths: list[float] = []
        cota_decape_values: list[float] = []

        if not normalized:
            return dimensions

        bom_contaminated = cls._is_bom_table_text(normalized)
        decape_values, segment_values = cls._extract_tolerance_cotas(normalized)
        indication: dict[str, bool] = {"left": False, "right": False}

        for value in decape_values:
            cota_decape_values.append(value)

        for value in segment_values:
            segment_lengths.append(cls._sanitize_chicote_length_mm(value, normalized))

        dimensions["totalLengthMm"] = cls._first_number(
            normalized,
            patterns=ChatDrawingPatternsService.length_patterns(),
            label_hints=ChatAssistantContentService.list(
                _BUNDLE,
                "dimensionLabels",
                "totalLength",
            ),
        )

        explicit_left = cls._first_number(
            normalized,
            patterns=ChatDrawingPatternsService.decape_left_patterns(),
        )

        if explicit_left is not None:
            dimensions["leftDecapeMm"] = explicit_left
            indication["left"] = True

        explicit_right = cls._first_number(
            normalized,
            patterns=ChatDrawingPatternsService.decape_right_patterns(),
        )

        if explicit_right is not None:
            dimensions["rightDecapeMm"] = explicit_right
            indication["right"] = True

        if dimensions["leftDecapeMm"] is None and dimensions["rightDecapeMm"] is None:
            if not bom_contaminated:
                generic = cls._first_number(
                    normalized,
                    patterns=(ChatDrawingPatternsService.generic_decape(),),
                )

                if generic is not None:
                    dimensions["rightDecapeMm"] = generic
                    indication["right"] = True

        if not bom_contaminated:
            note_decape = cls._first_number(
                normalized,
                patterns=(ChatDrawingPatternsService.decape_note(),),
            )

            if note_decape is not None:
                if dimensions["rightDecapeMm"] is None:
                    dimensions["rightDecapeMm"] = note_decape
                    indication["right"] = True

                if dimensions["leftDecapeMm"] is None and indication["left"]:
                    dimensions["leftDecapeMm"] = note_decape

        machine_decape = cls._first_number(
            normalized,
            patterns=(ChatDrawingPatternsService.decape_machine_side(),),
        )

        if machine_decape is not None:
            dimensions["leftDecapeMm"] = machine_decape
            indication["left"] = True

        cota_pattern = ChatDrawingPatternsService.cota_decape_length()
        max_segment = ChatDrawingPatternsService.max_segment_length_mm()
        max_decape = ChatDrawingPatternsService.max_decape_mm()

        for match in cota_pattern.finditer(normalized):
            decape = cls._parse_number(match.group(1))
            length = cls._parse_number(match.group(2))

            if decape is None or length is None:
                continue

            if decape > max_decape or length > max_segment:
                continue

            cota_decape_values.append(decape)

            if dimensions["leftDecapeMm"] is None:
                dimensions["leftDecapeMm"] = decape
                indication["left"] = True

            if dimensions["rightDecapeMm"] is None:
                dimensions["rightDecapeMm"] = decape
                indication["right"] = True

            segment_lengths.append(cls._sanitize_chicote_length_mm(length, normalized))

        cls._apply_unlabeled_decape_tolerance(
            dimensions,
            decape_values,
            indication=indication,
        )

        if cota_decape_values:
            dimensions["cotaDecapeValuesMm"] = list(dict.fromkeys(cota_decape_values))

        if segment_lengths:
            dimensions["segmentLengthsMm"] = segment_lengths

        if segment_lengths and dimensions["totalLengthMm"] is None:
            dimensions["totalLengthMm"] = max(segment_lengths)

        for key in ("totalLengthMm", "leftDecapeMm", "rightDecapeMm"):
            value = dimensions.get(key)

            if value is not None and key == "totalLengthMm":
                dimensions[key] = cls._sanitize_chicote_length_mm(float(value), normalized)

        dimensions["decapeIndication"] = indication

        return dimensions

    @classmethod
    def _apply_unlabeled_decape_tolerance(
        cls,
        dimensions: dict[str, Any],
        decape_values: list[float],
        *,
        indication: dict[str, bool],
    ) -> None:
        if not decape_values:
            return

        side = ChatDrawingPatternsService.unlabeled_decape_tolerance_side()
        key = "rightDecapeMm" if side == "right" else "leftDecapeMm"

        if dimensions.get(key) is None:
            dimensions[key] = decape_values[0]

        indication[side] = True

    @classmethod
    def merge_dimensions(
        cls,
        base: dict[str, Any] | None,
        *,
        region_text: str = "",
        fallback_text: str = "",
    ) -> dict[str, float | None]:
        merged = dict(base) if isinstance(base, dict) else {}
        region_dims = (
            cls.extract_dimensions(region_text) if region_text.strip() else {}
        )
        fallback_dims = (
            cls.extract_dimensions(fallback_text) if fallback_text.strip() else {}
        )
        region_bom = cls._is_bom_table_text(region_text) if region_text.strip() else False

        resolved: dict[str, float | None | list[float]] = {
            "totalLengthMm": merged.get("totalLengthMm"),
            "leftDecapeMm": merged.get("leftDecapeMm"),
            "rightDecapeMm": merged.get("rightDecapeMm"),
            "segmentLengthsMm": merged.get("segmentLengthsMm") or [],
            "cotaDecapeValuesMm": merged.get("cotaDecapeValuesMm") or [],
            "decapeIndication": cls._merge_decape_indication(
                merged,
                region_dims,
                fallback_dims,
            ),
        }

        for key in ("totalLengthMm", "leftDecapeMm", "rightDecapeMm"):
            if resolved[key] is None and region_dims.get(key) is not None:
                if not (region_bom and key in ("leftDecapeMm", "rightDecapeMm")):
                    resolved[key] = region_dims[key]

            if resolved[key] is None and fallback_dims.get(key) is not None:
                resolved[key] = fallback_dims[key]

            if (
                region_bom
                and key in ("leftDecapeMm", "rightDecapeMm")
                and fallback_dims.get(key) is not None
            ):
                resolved[key] = fallback_dims[key]

        if cls._length_value_implausible(resolved.get("totalLengthMm")) and fallback_dims.get(
            "totalLengthMm"
        ) is not None:
            resolved["totalLengthMm"] = fallback_dims["totalLengthMm"]

        if cls._segment_lengths_implausible(resolved.get("segmentLengthsMm")):
            for source in (fallback_dims, region_dims):
                segments = source.get("segmentLengthsMm") if isinstance(source, dict) else None

                if segments and not cls._segment_lengths_implausible(segments):
                    resolved["segmentLengthsMm"] = segments
                    break
        elif fallback_dims.get("segmentLengthsMm"):
            resolved_segments = list(resolved.get("segmentLengthsMm") or [])
            fallback_segments = list(fallback_dims.get("segmentLengthsMm") or [])

            if (
                resolved_segments
                and fallback_segments
                and max(resolved_segments) == max(fallback_segments)
                and len(fallback_segments) < len(resolved_segments)
            ):
                resolved["segmentLengthsMm"] = fallback_segments

        if not resolved["segmentLengthsMm"]:
            for source in (fallback_dims, region_dims):
                segments = source.get("segmentLengthsMm") if isinstance(source, dict) else None

                if segments:
                    resolved["segmentLengthsMm"] = segments
                    break

        if not resolved["cotaDecapeValuesMm"]:
            for source in (fallback_dims, region_dims):
                cota_values = (
                    source.get("cotaDecapeValuesMm") if isinstance(source, dict) else None
                )

                if cota_values:
                    resolved["cotaDecapeValuesMm"] = cota_values
                    break

        return resolved

    @classmethod
    def _merge_decape_indication(
        cls,
        base: dict[str, Any],
        region_dims: dict[str, Any],
        fallback_dims: dict[str, Any],
    ) -> dict[str, bool]:
        merged = {"left": False, "right": False}

        for source in (base, region_dims, fallback_dims):
            if not isinstance(source, dict):
                continue

            indication = source.get("decapeIndication")

            if not isinstance(indication, dict):
                continue

            merged["left"] = merged["left"] or bool(indication.get("left"))
            merged["right"] = merged["right"] or bool(indication.get("right"))

        return merged

    @classmethod
    def _extract_tolerance_cotas(
        cls,
        text: str,
    ) -> tuple[list[float], list[float]]:
        decape_values: list[float] = []
        segment_values: list[float] = []
        segment_spans: list[tuple[int, int]] = []

        for match in ChatDrawingPatternsService.segment_length_tolerance().finditer(text):
            length = cls._parse_number(match.group(1))

            if length is None:
                continue

            segment_values.append(length)
            segment_spans.append(match.span())

        for match in ChatDrawingPatternsService.decape_tolerance().finditer(text):
            if cls._span_overlaps(match.span(), segment_spans):
                continue

            decape = cls._parse_number(match.group(1))

            if decape is None or decape > ChatDrawingPatternsService.max_decape_mm():
                continue

            decape_values.append(decape)

        return decape_values, segment_values

    @classmethod
    def _repair_glued_tolerance_cotas(cls, text: str) -> str:
        return ChatDrawingPatternsService.glued_tolerance_cota().sub(
            r"\1±1\n\2±\3",
            str(text or ""),
        )

    @classmethod
    def _sanitize_chicote_length_mm(cls, value: float, text: str) -> float:
        max_segment = ChatDrawingPatternsService.max_segment_length_mm()

        if value <= max_segment:
            return value

        raw = str(int(value)) if float(value).is_integer() else str(value)

        if raw.startswith("11") and len(raw) == 5:
            candidate = raw[1:]

            if re.search(rf"\b{re.escape(candidate)}±", text):
                return float(candidate)

        if len(raw) == 6 and raw.endswith("22"):
            candidate = raw[:4]

            if re.search(rf"\b{re.escape(candidate)}±", text):
                return float(candidate)

        return value

    @classmethod
    def _length_value_implausible(cls, value: float | None) -> bool:
        if value is None:
            return False

        return float(value) > ChatDrawingPatternsService.max_segment_length_mm()

    @classmethod
    def _segment_lengths_implausible(cls, values: Any) -> bool:
        if not isinstance(values, list) or not values:
            return False

        return any(
            cls._length_value_implausible(float(value))
            for value in values
            if value is not None
        )

    @classmethod
    def _span_overlaps(
        cls,
        span: tuple[int, int],
        occupied: list[tuple[int, int]],
    ) -> bool:
        start, end = span

        for other_start, other_end in occupied:
            if start < other_end and end > other_start:
                return True

        return False

    @classmethod
    def _is_bom_table_text(cls, text: str) -> bool:
        normalized = str(text or "")

        if ChatDrawingPatternsService.bom_section().search(normalized):
            return True

        if ChatDrawingPatternsService.intermediate_segment().search(normalized):
            return True

        intermediate_hits = ChatDrawingPatternsService.intermediate_code().findall(
            normalized
        )

        return len(intermediate_hits) >= 2

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
