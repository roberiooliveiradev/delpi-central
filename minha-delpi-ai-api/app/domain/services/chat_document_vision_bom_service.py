"""Extração heurística de BOM a partir de texto OCR — Onda 13.3.2 / região bom Onda 14.5."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.domain.services.chat_drawing_component_code_normalization_service import (
    ChatDrawingComponentCodeNormalizationService,
)
from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService


class ChatDocumentVisionBomService:
    @classmethod
    def score_bom_text(cls, text: str, *, exclude_product_code: str | None = None) -> int:
        normalized = str(text or "").strip()

        if not normalized:
            return -1

        exclude = ChatProductQueryIntentService.normalize_product_code(
            exclude_product_code or ""
        )
        rows = cls.extract_bom_rows(
            normalized,
            exclude_product_code=exclude,
            region_scoped=True,
        )
        codes = cls.meaningful_bom_component_codes(
            rows,
            exclude_product_code=exclude,
        )
        score = len(codes) * 10

        if ChatDrawingPatternsService.bom_section().search(normalized):
            score += 8

        if ChatDrawingPatternsService.bom_table_header().search(normalized):
            score += 12

        upper = normalized.upper()

        if "VISTA" in upper and not codes:
            score -= 25

        if len(normalized) < 40 and not codes:
            score -= 10

        if cls.is_stamp_layout_without_bom(normalized):
            score -= 40

        return score

    @classmethod
    def resolve_from_sources(
        cls,
        sources: list[tuple[str, str]],
        *,
        exclude_product_code: str | None = None,
    ) -> tuple[list[dict[str, Any]], list[str], str | None]:
        best_rows: list[dict[str, Any]] = []
        best_codes: list[str] = []
        best_source: str | None = None
        best_score = -1

        for source_name, text in sources:
            normalized = str(text or "").strip()

            if not normalized:
                continue

            rows = cls.extract_bom_rows(
                normalized,
                exclude_product_code=exclude_product_code,
                region_scoped=source_name != "full_text_section",
            )
            codes = cls.bom_component_codes(rows)

            if not codes and source_name == "full_text":
                rows = cls.extract_bom_rows(
                    normalized,
                    exclude_product_code=exclude_product_code,
                    region_scoped=False,
                )
                codes = cls.bom_component_codes(rows)

            score = cls.score_bom_text(
                normalized,
                exclude_product_code=exclude_product_code,
            )

            if score > best_score or (score == best_score and len(codes) > len(best_codes)):
                best_score = score
                best_rows = rows
                best_codes = codes
                best_source = source_name

        return best_rows, best_codes, best_source

    @classmethod
    def extract_bom_rows(
        cls,
        text: str,
        *,
        exclude_product_code: str | None = None,
        max_rows: int = 40,
        region_scoped: bool = False,
    ) -> list[dict[str, Any]]:
        normalized = str(text or "").strip()

        if not normalized:
            return []

        exclude = ChatProductQueryIntentService.normalize_product_code(
            exclude_product_code or ""
        )

        if region_scoped:
            return cls._parse_bom_lines(
                normalized,
                exclude=exclude,
                max_rows=max_rows,
            )

        if not ChatDrawingPatternsService.bom_section().search(normalized):
            return []

        section_start = cls._bom_section_offset(normalized)
        section_text = normalized[section_start:]

        return cls._parse_bom_lines(
            section_text,
            exclude=exclude,
            max_rows=max_rows,
        )

    @classmethod
    def bom_component_codes(cls, bom_rows: list[dict[str, Any]]) -> list[str]:
        codes: list[str] = []

        for row in bom_rows:
            code = ChatProductQueryIntentService.normalize_product_code(
                str(row.get("code") or "")
            )

            if code and code not in codes:
                codes.append(code)

        return codes

    @classmethod
    def meaningful_bom_component_codes(
        cls,
        bom_rows: list[dict[str, Any]],
        *,
        exclude_product_code: str | None = None,
    ) -> list[str]:
        exclude = ChatProductQueryIntentService.normalize_product_code(
            exclude_product_code or ""
        )
        codes: list[str] = []

        for row in bom_rows:
            code = ChatProductQueryIntentService.normalize_product_code(
                str(row.get("code") or "")
            )

            if not code or code == exclude or code in codes:
                continue

            if ChatDrawingPatternsService.is_nested_chicote_in_assembly_bom(code, exclude):
                codes.append(code)
                continue

            if ChatDrawingPatternsService.is_finished_product(code):
                continue

            if (
                ChatDrawingPatternsService.is_bom_component(code)
                or ChatDrawingPatternsService.is_intermediate_family(str(code))
            ):
                codes.append(code)

        return codes

    @classmethod
    def is_stamp_layout_without_bom(cls, text: str) -> bool:
        normalized = str(text or "").strip()

        if not normalized:
            return False

        upper = normalized.upper()

        if ChatDrawingPatternsService.bom_table_header().search(upper):
            return False

        if ChatDrawingPatternsService.bom_section().search(normalized):
            return False

        marker_hits = 0

        for pattern in ChatDrawingPatternsService.bom_stamp_layout_without_table_patterns():
            if pattern.search(upper):
                marker_hits += 1

        return marker_hits >= 2

    @classmethod
    def demote_bom_codes_in_candidates(
        cls,
        candidates: list[dict[str, Any]] | None,
        bom_codes: list[str] | None,
    ) -> list[dict[str, Any]]:
        if not candidates:
            return []

        bom_set = {
            ChatProductQueryIntentService.normalize_product_code(code)
            for code in (bom_codes or [])
            if code
        }
        demoted: list[dict[str, Any]] = []

        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue

            code = ChatProductQueryIntentService.normalize_product_code(
                str(candidate.get("code") or "")
            )
            confidence = float(candidate.get("confidence") or 0)

            cap = ChatDrawingPatternsService.extraction_limit_float(
                "bomCandidateConfidenceCap",
                0.5,
            )

            if code in bom_set and confidence > cap:
                demoted.append(
                    {
                        **candidate,
                        "code": code,
                        "confidence": cap,
                        "source": f"{candidate.get('source') or 'unknown'}_bom_demoted",
                    }
                )
                continue

            demoted.append(candidate)

        return demoted

    @classmethod
    def is_revision_noise_line(cls, line: str) -> bool:
        stripped = str(line or "").strip()

        if not stripped:
            return False

        for pattern in ChatDrawingPatternsService.bom_revision_noise_patterns():
            if pattern.search(stripped):
                return True

        return False

    @classmethod
    def codes_only_in_revision_lines(cls, text: str) -> set[str]:
        revision_codes: set[str] = set()
        clean_codes: set[str] = set()

        for line in str(text or "").splitlines():
            stripped = line.strip()

            if not stripped:
                continue

            matches = ChatDrawingPatternsService.component_code().findall(stripped)

            if not matches:
                continue

            normalized = {
                ChatProductQueryIntentService.normalize_product_code(match)
                for match in matches
            }
            normalized = {code for code in normalized if code}

            if cls.is_revision_noise_line(stripped):
                revision_codes.update(normalized)
                continue

            clean_codes.update(normalized)

        return {code for code in revision_codes if code not in clean_codes}

    @classmethod
    def _parse_bom_lines(
        cls,
        section_text: str,
        *,
        exclude: str,
        max_rows: int,
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        seen_codes: set[str] = set()

        for line in section_text.splitlines():
            if len(rows) >= max_rows:
                break

            if cls.is_revision_noise_line(line):
                continue

            row = cls._parse_bom_line(line, exclude=exclude, seen=seen_codes)

            if row:
                rows.append(row)
                seen_codes.add(str(row["code"]))
                continue

            cls._append_secondary_codes_from_line(
                line,
                exclude=exclude,
                seen=seen_codes,
                rows=rows,
                max_rows=max_rows,
            )

        return rows

    @classmethod
    def _append_secondary_codes_from_line(
        cls,
        line: str,
        *,
        exclude: str,
        seen: set[str],
        rows: list[dict[str, Any]],
        max_rows: int,
    ) -> None:
        for match in ChatDrawingPatternsService.component_code().finditer(str(line or "")):
            if len(rows) >= max_rows:
                return

            code = ChatProductQueryIntentService.normalize_product_code(match.group(1))

            if not code or code == exclude or code in seen:
                continue

            if ChatDrawingPatternsService.is_finished_product(code):
                continue

            if cls._line_code_is_description_noise(line, code):
                continue

            rows.append(
                {
                    "code": code,
                    "quantity": None,
                    "description": None,
                }
            )
            seen.add(code)

    @classmethod
    def _line_code_is_description_noise(cls, line: str, code: str) -> bool:
        blob = str(line or "")

        if not blob or not code:
            return False

        idx = blob.find(code)

        if idx <= 0:
            return False

        before = blob[:idx]
        upper_before = before.upper()

        if "PTC" not in upper_before and "TERMISTOR" not in upper_before:
            return False

        return bool(
            "°C" in before
            or "ºC" in before
            or "° C" in before
            or re.search(r"PTC\s*\d+", upper_before)
        )

    @classmethod
    def _bom_section_offset(cls, text: str) -> int:
        match = ChatDrawingPatternsService.bom_section().search(text)

        if not match:
            return 0

        return match.start()

    @classmethod
    def _quantity_before_code(cls, line: str, code_start: int) -> str | None:
        prefix = str(line or "")[: max(code_start, 0)].strip()

        if not prefix:
            return None

        tail = prefix.split("|")[-1].strip()

        if not tail:
            segments = [segment.strip() for segment in prefix.split("|") if segment.strip()]

            if segments:
                tail = segments[-1]

        qty_match = ChatDrawingPatternsService.bom_quantity().search(tail)

        if not qty_match and tail.isdigit():
            return tail.replace(",", ".")

        if qty_match:
            return qty_match.group(1).replace(",", ".")

        return None

    @classmethod
    def _parse_bom_line(
        cls,
        line: str,
        *,
        exclude: str,
        seen: set[str],
    ) -> dict[str, Any] | None:
        stripped = str(line or "").strip()

        if len(stripped) < 6:
            return None

        code_match = ChatDrawingPatternsService.component_code().search(stripped)

        if not code_match:
            return None

        code = ChatProductQueryIntentService.normalize_product_code(code_match.group(1))

        if not code or code == exclude or code in seen:
            return None

        remainder = stripped[code_match.end() :].strip()
        qty = cls._quantity_before_code(stripped, code_match.start())
        description = remainder

        qty_match = ChatDrawingPatternsService.bom_quantity().search(remainder)

        if qty_match:
            qty = qty_match.group(1).replace(",", ".")
            description = remainder[qty_match.end() :].strip(" -|\t")

        if ChatDrawingPatternsService.is_finished_product(code) and not qty:
            return None

        if cls._line_code_is_description_noise(stripped, code):
            return None

        return {
            "code": code,
            "quantity": qty,
            "description": (description or "")[:120] or None,
        }

    @classmethod
    def merge_component_codes_from_rows(
        cls,
        component_codes: list[str],
        bom_rows: list[dict[str, Any]],
    ) -> list[str]:
        merged = list(component_codes or [])

        for row in bom_rows:
            code = str(row.get("code") or "").strip()

            if code and code not in merged:
                merged.append(code)

        return merged
