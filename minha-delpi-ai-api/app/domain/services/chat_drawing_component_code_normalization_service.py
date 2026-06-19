"""Normalização e reconciliação de códigos de componente extraídos por OCR."""

from __future__ import annotations

from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


class ChatDrawingComponentCodeNormalizationService:
    @classmethod
    def component_code_pattern(cls):
        return ChatDrawingPatternsService.component_code()

    @classmethod
    def normalize_extracted(cls, raw_code: str) -> str | None:
        code = ChatProductQueryIntentService.normalize_product_code(str(raw_code or ""))

        if not code:
            return None

        if ChatDrawingPatternsService.ocr_connector_typo_pattern().fullmatch(code):
            prefix = str(
                ChatDrawingPatternsService.ocr_normalization(
                    "connectorReplacementPrefix",
                    "10",
                )
            )
            return f"{prefix}{code[2:]}"

        short_len = int(ChatDrawingPatternsService.ocr_normalization("shortTermoLength", 7))
        short_prefix = str(
            ChatDrawingPatternsService.ocr_normalization("shortTermoPrefix", "101")
        )

        if len(code) == short_len and code.isdigit() and code.startswith(short_prefix):
            return f"{code[:5]}0{code[5:]}"

        return code

    @classmethod
    def reconcile_with_known(cls, raw_code: str, known_codes: set[str]) -> str | None:
        code = cls.normalize_extracted(raw_code)

        if not code:
            return None

        if code in known_codes:
            return code

        if ChatDrawingPatternsService.ocr_connector_typo_pattern().fullmatch(code):
            prefix = str(
                ChatDrawingPatternsService.ocr_normalization(
                    "connectorReplacementPrefix",
                    "10",
                )
            )
            alt = f"{prefix}{code[2:]}"

            if alt in known_codes:
                return alt

        short_len = int(ChatDrawingPatternsService.ocr_normalization("shortTermoLength", 7))
        full_len = int(ChatDrawingPatternsService.ocr_normalization("fullTermoLength", 8))

        if len(code) == short_len and code.isdigit():
            prefix_matches = sorted(
                candidate
                for candidate in known_codes
                if len(candidate) == full_len and candidate.startswith(code[:5])
            )

            if len(prefix_matches) == 1:
                return prefix_matches[0]

            padded = f"{code[:5]}0{code[5:]}"

            if padded in known_codes:
                return padded

        return code
