"""Saneamento de linhas BOM — fantasmas de produto e códigos aninhados em descrição."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_drawing_bom_reference_noise_service import (
    ChatDrawingBomReferenceNoiseService,
)
from app.domain.services.chat_drawing_component_code_normalization_service import (
    ChatDrawingComponentCodeNormalizationService,
)
from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


class ChatDrawingBomRowSanitizationService:
    @classmethod
    def sanitize_rows(
        cls,
        bom_rows: list[dict[str, Any]],
        *,
        product_code: str | None,
    ) -> list[dict[str, Any]]:
        product_norm = ChatProductQueryIntentService.normalize_product_code(
            product_code or ""
        )
        sanitized: list[dict[str, Any]] = []

        for row in bom_rows:
            if not isinstance(row, dict):
                continue

            code = ChatProductQueryIntentService.normalize_product_code(
                str(row.get("code") or "")
            )

            if not code:
                continue

            if product_norm and cls.is_product_code_ghost(code, product_norm):
                continue

            if product_norm and code == product_norm:
                continue

            if ChatDrawingBomReferenceNoiseService.is_client_reference_row(row):
                continue

            sanitized.append(row)

        return sanitized

    @classmethod
    def is_product_code_ghost(cls, code: str, product_code: str) -> bool:
        normalized = ChatProductQueryIntentService.normalize_product_code(code)
        product_norm = ChatProductQueryIntentService.normalize_product_code(product_code)

        if not normalized or not product_norm:
            return False

        if normalized == product_norm:
            return True

        if ChatDrawingPatternsService.is_nested_chicote_in_assembly_bom(normalized, product_norm):
            return False

        if ChatDrawingPatternsService.is_finished_product(
            normalized
        ) and ChatDrawingPatternsService.is_finished_product(product_norm):
            return True

        return False

    @classmethod
    def nested_component_codes(cls, bom_rows: list[dict[str, Any]]) -> list[str]:
        pattern = ChatDrawingComponentCodeNormalizationService.component_code_pattern()
        found: list[str] = []

        for row in bom_rows:
            if not isinstance(row, dict):
                continue

            row_code = ChatProductQueryIntentService.normalize_product_code(
                str(row.get("code") or "")
            )
            blob = " ".join(
                str(row.get(field) or "")
                for field in ("description", "quantity")
            )

            for match in pattern.finditer(blob):
                code = ChatDrawingComponentCodeNormalizationService.normalize_extracted(
                    ChatProductQueryIntentService.normalize_product_code(match.group(1))
                )

                if not code or code == row_code or code in found:
                    continue

                if cls._description_code_is_noise(blob, code):
                    continue

                found.append(code)

        return found

    @classmethod
    def dedupe_component_codes(cls, component_codes: list[str]) -> list[str]:
        resolved: list[str] = []

        for raw in component_codes:
            code = ChatDrawingComponentCodeNormalizationService.normalize_extracted(
                ChatProductQueryIntentService.normalize_product_code(str(raw or ""))
            )

            if not code or code in resolved:
                continue

            resolved.append(code)

        return resolved

    @classmethod
    def _description_code_is_noise(cls, description: str, code: str) -> bool:
        blob = str(description or "")

        if not blob or not code:
            return False

        for pattern in ChatDrawingPatternsService.bom_description_code_noise_patterns():
            if pattern.search(blob):
                return True

        return False
