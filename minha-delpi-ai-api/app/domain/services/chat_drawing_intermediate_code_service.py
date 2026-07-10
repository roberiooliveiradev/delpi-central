"""Códigos intermediários 50xx em desenhos DELPI — coleta e deduplicação OCR."""

from __future__ import annotations

from collections import Counter
from typing import Any

from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_pdf_bom_source_service import ChatPdfBomSourceService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


class ChatDrawingIntermediateCodeService:
    _OCR_CONFUSION_PAIRS = {
        ("9", "2"),
        ("2", "9"),
        ("0", "8"),
        ("8", "0"),
        ("0", "2"),
        ("2", "0"),
        ("1", "7"),
        ("7", "1"),
    }

    @classmethod
    def collect_codes(
        cls,
        *,
        full_text: str,
        bom_rows: list[dict[str, Any]],
        bom_sources: list[tuple[str, str]],
        product_code: str | None,
        revision_only_codes: set[str] | None = None,
    ) -> list[str]:
        exclude = ChatProductQueryIntentService.normalize_product_code(product_code or "")
        revision_only = revision_only_codes or set()
        found: list[str] = []

        for source_name, source_text in bom_sources:
            if source_name == "full_text":
                continue

            for match in ChatDrawingPatternsService.intermediate_code().finditer(
                str(source_text or "")
            ):
                cls._append_code(found, match.group(0), exclude=exclude, revision_only=revision_only)

        for row in bom_rows:
            cls._append_code(
                found,
                str(row.get("code") or ""),
                exclude=exclude,
                revision_only=revision_only,
            )

        for match in ChatDrawingPatternsService.intermediate_code().finditer(str(full_text or "")):
            cls._append_code(found, match.group(0), exclude=exclude, revision_only=revision_only)

        return cls.filter_ocr_duplicates(
            found,
            bom_sources=bom_sources,
            bom_rows=bom_rows,
        )

    @classmethod
    def filter_ocr_duplicates(
        cls,
        codes: list[str],
        *,
        bom_sources: list[tuple[str, str]],
        bom_rows: list[dict[str, Any]] | None = None,
    ) -> list[str]:
        trusted_rows = cls.trusted_row_codes(
            bom_rows or [],
            bom_sources=bom_sources,
        )
        bom_blob = ChatPdfBomSourceService.structured_source_blob(bom_sources)
        counts = Counter(
            ChatDrawingPatternsService.intermediate_code().findall(bom_blob)
        )
        filtered: list[str] = []

        for code in sorted(codes, key=lambda item: (-counts.get(item, 0), item)):
            if code in filtered:
                continue

            if any(
                cls.is_ocr_typo_duplicate(code, trusted)
                for trusted in trusted_rows
                if trusted != code and code not in trusted_rows
            ):
                continue

            code_counts = Counter(str(code))
            is_duplicate = False

            for other, count in counts.items():
                if other == code:
                    continue

                if Counter(other) == code_counts and count > counts.get(code, 0):
                    is_duplicate = True
                    break

                if cls.is_ocr_typo_duplicate(code, other) and count > counts.get(code, 0):
                    is_duplicate = True
                    break

            if not is_duplicate:
                filtered.append(code)

        return sorted(filtered)

    @classmethod
    def trusted_row_codes(
        cls,
        bom_rows: list[dict[str, Any]],
        *,
        bom_sources: list[tuple[str, str]] | None = None,
    ) -> set[str]:
        bom_blob = ChatPdfBomSourceService.structured_source_blob(bom_sources or [])
        counts = Counter(
            ChatDrawingPatternsService.intermediate_code().findall(bom_blob)
        )
        trusted: list[str] = []

        for row in bom_rows:
            code = ChatProductQueryIntentService.normalize_product_code(
                str(row.get("code") or "")
            )

            if code and ChatDrawingPatternsService.is_intermediate_family(code):
                trusted.append(code)

        refined: list[str] = []

        for code in sorted(set(trusted), key=lambda item: (-counts.get(item, 0), item)):
            if any(cls.is_ocr_typo_duplicate(code, kept) for kept in refined):
                continue

            refined.append(code)

        return set(refined)

    @classmethod
    def is_ocr_typo_duplicate(cls, left: str, right: str) -> bool:
        if (
            len(left) != len(right)
            or not ChatDrawingPatternsService.is_intermediate_family(left)
            or not ChatDrawingPatternsService.is_intermediate_family(right)
        ):
            return False

        differences = [
            (left_char, right_char)
            for left_char, right_char in zip(left, right)
            if left_char != right_char
        ]

        if len(differences) != 1:
            return False

        pair = differences[0]

        return pair in cls._OCR_CONFUSION_PAIRS or (pair[1], pair[0]) in cls._OCR_CONFUSION_PAIRS

    @classmethod
    def _append_code(
        cls,
        found: list[str],
        raw_code: str | None,
        *,
        exclude: str,
        revision_only: set[str],
    ) -> None:
        normalized = ChatProductQueryIntentService.normalize_product_code(raw_code or "")

        if (
            not normalized
            or normalized == exclude
            or normalized in revision_only
            or not ChatDrawingPatternsService.is_intermediate_family(normalized)
            or normalized in found
        ):
            return

        found.append(normalized)
