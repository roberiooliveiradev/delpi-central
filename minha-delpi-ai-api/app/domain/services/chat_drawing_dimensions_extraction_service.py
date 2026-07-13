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
            skip_suppressed_decape_context=True,
        )

        if explicit_left is not None:
            dimensions["leftDecapeMm"] = explicit_left
            indication["left"] = True

        explicit_right = cls._first_number(
            normalized,
            patterns=ChatDrawingPatternsService.decape_right_patterns(),
            skip_suppressed_decape_context=True,
        )

        if explicit_right is not None:
            dimensions["rightDecapeMm"] = explicit_right
            indication["right"] = True

        if dimensions["leftDecapeMm"] is None and dimensions["rightDecapeMm"] is None:
            if not bom_contaminated and not cls._should_skip_decape_in_context(normalized):
                generic = cls._first_number(
                    normalized,
                    patterns=(ChatDrawingPatternsService.generic_decape(),),
                    skip_suppressed_decape_context=True,
                )

                if generic is not None and cls._is_plausible_cable_decape(generic):
                    dimensions["rightDecapeMm"] = generic
                    indication["right"] = True

        if not bom_contaminated:
            note_decape = cls._first_number(
                normalized,
                patterns=(ChatDrawingPatternsService.decape_note(),),
                skip_suppressed_decape_context=True,
            )

            if (
                note_decape is not None
                and cls._is_plausible_cable_decape(note_decape)
                and not cls._should_skip_decape_in_context(normalized)
            ):
                if dimensions["rightDecapeMm"] is None:
                    dimensions["rightDecapeMm"] = note_decape
                    indication["right"] = True

                if dimensions["leftDecapeMm"] is None and indication["left"]:
                    dimensions["leftDecapeMm"] = note_decape

        machine_decape = cls._first_number(
            normalized,
            patterns=(ChatDrawingPatternsService.decape_machine_side(),),
            skip_suppressed_decape_context=True,
        )

        if machine_decape is not None:
            dimensions["leftDecapeMm"] = machine_decape
            indication["left"] = True

        cota_pattern = ChatDrawingPatternsService.cota_decape_length()
        max_segment = ChatDrawingPatternsService.max_segment_length_mm()
        max_decape = ChatDrawingPatternsService.max_decape_mm()

        for match in cota_pattern.finditer(normalized):
            if cls._should_skip_decape_in_context(normalized, start=match.start()):
                continue

            first = cls._parse_number(match.group(1))
            second = cls._parse_number(match.group(2))
            third = (
                cls._parse_number(match.group(3))
                if match.lastindex and match.lastindex >= 3
                else None
            )

            if first is None or second is None:
                continue

            if (
                third is not None
                and first <= max_decape
                and second <= max_segment
                and third <= max_decape
                and third >= 2
                and cls._is_plausible_cable_decape(first)
                and cls._is_plausible_cable_decape(third)
            ):
                length = second
                left_decape = first
                right_decape = third
                cota_decape_values.extend([left_decape, right_decape])

                if dimensions["leftDecapeMm"] is None:
                    dimensions["leftDecapeMm"] = left_decape
                    indication["left"] = True

                if dimensions["rightDecapeMm"] is None:
                    dimensions["rightDecapeMm"] = right_decape
                    indication["right"] = True

                segment_lengths.append(cls._sanitize_chicote_length_mm(length, normalized))
                continue

            if (
                third is not None
                and first <= max_segment
                and first > max_decape
                and third <= max_decape
            ):
                length = first
                decape = third
                side = "left"
            elif first <= max_decape and second <= max_segment:
                if second >= 100 and first <= ChatDrawingPatternsService.typical_cable_decape_mm():
                    segment_lengths.append(cls._sanitize_chicote_length_mm(second, normalized))
                    continue

                decape = first
                length = second
                side = None
            else:
                continue

            if not cls._is_plausible_cable_decape(decape):
                continue

            cota_decape_values.append(decape)

            if side == "left":
                if dimensions["leftDecapeMm"] is None:
                    dimensions["leftDecapeMm"] = decape
                    indication["left"] = True
            else:
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
            text=normalized,
        )

        if cota_decape_values:
            dimensions["cotaDecapeValuesMm"] = list(dict.fromkeys(cota_decape_values))

        if segment_lengths:
            dimensions["segmentLengthsMm"] = cls.filter_plausible_segment_lengths(
                segment_lengths
            )

        if dimensions.get("segmentLengthsMm") and dimensions["totalLengthMm"] is None:
            dimensions["totalLengthMm"] = max(dimensions["segmentLengthsMm"])

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
        text: str = "",
    ) -> None:
        if not decape_values:
            return

        side = cls._resolve_unlabeled_decape_side(text)
        key = "rightDecapeMm" if side == "right" else "leftDecapeMm"

        if dimensions.get(key) is None:
            candidate = decape_values[0]

            if not cls._is_plausible_cable_decape(candidate):
                return

            if cls._is_length_tolerance_decape_value(candidate, text):
                return

            dimensions[key] = candidate

        indication[side] = True

    @classmethod
    def _is_plausible_cable_decape(cls, value: float | None) -> bool:
        if value is None:
            return False

        return float(value) <= ChatDrawingPatternsService.typical_cable_decape_mm()

    @classmethod
    def only_implausible_global_decape(cls, dimensions: dict[str, Any]) -> bool:
        if not isinstance(dimensions, dict):
            return False

        values: list[float] = []

        for key in ("leftDecapeMm", "rightDecapeMm"):
            parsed = cls._parse_number(str(dimensions.get(key) or ""))

            if parsed is not None:
                values.append(parsed)

        for raw in dimensions.get("cotaDecapeValuesMm") or []:
            parsed = cls._parse_number(str(raw))

            if parsed is not None:
                values.append(parsed)

        if not values:
            return False

        return all(not cls._is_plausible_cable_decape(value) for value in values)

    @classmethod
    def _resolve_unlabeled_decape_side(cls, text: str) -> str:
        default_side = ChatDrawingPatternsService.unlabeled_decape_tolerance_side()
        normalized = str(text or "")

        if not normalized.strip():
            return default_side

        decape_pos: int | None = None
        segment_pos: int | None = None

        for match in ChatDrawingPatternsService.decape_tolerance().finditer(normalized):
            decape_pos = match.start()
            break

        for match in ChatDrawingPatternsService.segment_length_tolerance().finditer(normalized):
            segment_pos = match.start()
            break

        if decape_pos is not None and segment_pos is not None:
            if segment_pos < decape_pos:
                return "left"

            if decape_pos < segment_pos:
                return default_side

        return default_side

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

        if resolved.get("segmentLengthsMm"):
            resolved["segmentLengthsMm"] = cls.filter_plausible_segment_lengths(
                resolved.get("segmentLengthsMm")
            )

        if cls._segment_lengths_implausible(resolved.get("segmentLengthsMm")):
            for source in (fallback_dims, region_dims):
                segments = source.get("segmentLengthsMm") if isinstance(source, dict) else None
                plausible = cls.filter_plausible_segment_lengths(segments)

                if plausible:
                    resolved["segmentLengthsMm"] = plausible
                    break
        elif fallback_dims.get("segmentLengthsMm"):
            resolved_segments = list(resolved.get("segmentLengthsMm") or [])
            fallback_segments = cls.filter_plausible_segment_lengths(
                fallback_dims.get("segmentLengthsMm")
            )

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
                plausible = cls.filter_plausible_segment_lengths(segments)

                if plausible:
                    resolved["segmentLengthsMm"] = plausible
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
            tolerance = cls._parse_number(match.group(2))

            if decape is None or decape > ChatDrawingPatternsService.max_decape_mm():
                continue

            if (
                tolerance is not None
                and tolerance >= 100
                and decape <= ChatDrawingPatternsService.typical_cable_decape_mm()
            ):
                segment_values.append(tolerance)
                continue

            if not cls._is_plausible_cable_decape(decape):
                continue

            if cls._is_length_tolerance_decape_value(decape, text):
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
    def filter_plausible_segment_lengths(cls, values: Any) -> list[float]:
        """Remove cotas OCR implausíveis (ex.: 31008 mm) sem descartar a lista inteira."""
        if not isinstance(values, list) or not values:
            return []

        plausible: list[float] = []

        for value in values:
            if value is None:
                continue

            try:
                parsed = float(value)
            except (TypeError, ValueError):
                continue

            if cls._length_value_implausible(parsed):
                continue

            plausible.append(parsed)

        return plausible

    @classmethod
    def _segment_lengths_implausible(cls, values: Any) -> bool:
        """True quando a lista está vazia após sanitização (nada útil para cotas)."""
        if not isinstance(values, list):
            return False

        return not cls.filter_plausible_segment_lengths(values)

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
        grid = ChatDrawingPatternsService.revision_column_grid()
        lines = [
            line
            for line in collapsed.splitlines()
            if not grid.fullmatch(line.strip())
        ]
        collapsed = "\n".join(lines)
        return re.sub(r"\n{3,}", "\n\n", collapsed).strip()

    @classmethod
    def _first_number(
        cls,
        text: str,
        *,
        patterns: tuple[re.Pattern[str], ...],
        label_hints: list[str] | None = None,
        skip_suppressed_decape_context: bool = False,
    ) -> float | None:
        for pattern in patterns:
            for match in pattern.finditer(text):
                if skip_suppressed_decape_context and cls._should_skip_decape_in_context(
                    text,
                    start=match.start(),
                ):
                    continue

                if match.lastindex is None or match.lastindex < 1:
                    continue

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
    def detect_ambiguous_dimension_notes(cls, text: str) -> bool:
        normalized = cls._normalize_ocr_text(text).upper()

        if not normalized:
            return False

        has_decape = cls._text_has_note_markers(
            normalized,
            ChatDrawingPatternsService.dimension_note_context_markers("decape_cable"),
        )
        has_shrink = any(
            cls._text_has_note_markers(
                normalized,
                ChatDrawingPatternsService.dimension_note_context_markers(note_type),
            )
            for note_type in ChatDrawingPatternsService.dimension_note_types_suppressing_decape()
        )

        return has_decape and has_shrink

    @classmethod
    def summarize_ambiguous_dimension_notes(cls, text: str) -> str | None:
        if not cls.detect_ambiguous_dimension_notes(text):
            return None

        from app.domain.services.chat_drawing_validation_content_service import (
            ChatDrawingValidationContentService,
        )

        excerpt = cls._extract_ambiguous_dimension_excerpt(text)
        explanation = ChatDrawingValidationContentService.get(
            "presentation",
            "ambiguousNoteExplanation",
        )

        return ChatDrawingValidationContentService.evidence_format(
            "dimensionNoteAmbiguous",
            excerpt=excerpt,
            explanation=explanation,
        )

    @classmethod
    def _extract_ambiguous_dimension_excerpt(cls, text: str, *, max_len: int = 72) -> str:
        from app.domain.services.chat_drawing_validation_content_service import (
            ChatDrawingValidationContentService,
        )

        fallback = ChatDrawingValidationContentService.get(
            "presentation",
            "ambiguousNoteExcerptFallback",
            default="trecho dimensional ambíguo",
        )
        normalized = cls._normalize_ocr_text(text)

        if not normalized:
            return fallback

        shrink_markers: list[str] = []
        decape_markers: list[str] = []

        for note_type in ChatDrawingPatternsService.dimension_note_types_suppressing_decape():
            shrink_markers.extend(
                ChatDrawingPatternsService.dimension_note_context_markers(note_type)
            )

        decape_markers.extend(
            ChatDrawingPatternsService.dimension_note_context_markers("decape_cable")
        )

        best_line = ""
        best_score = -1

        for raw_line in normalized.splitlines():
            line = " ".join(raw_line.split()).strip()

            if not line:
                continue

            upper = line.upper()
            has_shrink = any(marker in upper for marker in shrink_markers if marker)
            has_decape = any(marker in upper for marker in decape_markers if marker)
            score = int(has_shrink) + int(has_decape)

            if score > best_score:
                best_score = score
                best_line = line

        if best_score < 2:
            window = cls._ambiguous_note_window(normalized, shrink_markers, decape_markers)

            if window:
                best_line = window

        if not best_line:
            return fallback

        if len(best_line) <= max_len:
            return best_line

        return best_line[: max_len - 1].rstrip() + "…"

    @classmethod
    def _ambiguous_note_window(
        cls,
        text: str,
        shrink_markers: list[str],
        decape_markers: list[str],
        *,
        radius: int = 90,
    ) -> str:
        upper = str(text or "").upper()
        anchor = -1

        for marker in shrink_markers + decape_markers:
            if not marker:
                continue

            idx = upper.find(marker)

            if idx >= 0 and (anchor < 0 or idx < anchor):
                anchor = idx

        if anchor < 0:
            return ""

        begin = max(0, anchor - radius)
        end = min(len(text), anchor + radius)
        snippet = " ".join(str(text[begin:end]).split()).strip()

        return snippet

    @classmethod
    def _should_skip_decape_in_context(cls, text: str, *, start: int = 0) -> bool:
        window = cls._context_window(text, start).upper()

        if any(
            cls._text_has_note_markers(
                window,
                ChatDrawingPatternsService.dimension_note_context_markers(note_type),
            )
            for note_type in ChatDrawingPatternsService.dimension_note_types_suppressing_decape()
        ):
            return True

        if cls._text_has_note_markers(
            window,
            ChatDrawingPatternsService.dimension_note_context_markers("decape_cable"),
        ):
            return False

        return False

    @classmethod
    def _context_window(cls, text: str, start: int, *, radius: int = 120) -> str:
        normalized = str(text or "")
        begin = max(0, start - radius)
        end = min(len(normalized), start + radius)

        return normalized[begin:end]

    @classmethod
    def _text_has_note_markers(cls, text: str, markers: tuple[str, ...]) -> bool:
        upper = str(text or "").upper()

        return any(marker in upper for marker in markers if marker)

    @classmethod
    def _is_length_tolerance_decape_value(cls, decape: float, text: str) -> bool:
        allowed = ChatDrawingPatternsService.length_tolerance_decape_values_mm()

        if float(decape) not in allowed:
            return False

        for match in ChatDrawingPatternsService.segment_length_tolerance().finditer(text):
            tolerance = cls._parse_number(match.group(2))

            if tolerance is not None and abs(float(tolerance) - float(decape)) < 0.01:
                return True

        return False

    @classmethod
    def _parse_number(cls, raw: str) -> float | None:
        compact = re.sub(r"\s+", "", str(raw or ""))
        return ChatDrawingToleranceService.parse_mm(compact)
