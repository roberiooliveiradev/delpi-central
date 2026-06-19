"""Resolução de código de produto em PDF de desenho DELPI — carimbo, arquivo, BOM."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_drawing_product_code_resolution_service import (
    ChatDrawingProductCodeResolutionService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


class ChatDrawingPdfProductContextService:
    @classmethod
    def resolve_product_code(
        cls,
        *,
        stamp_extract: dict[str, Any],
        full_text: str,
        metadata: dict[str, Any] | None,
    ) -> tuple[str | None, str | None]:
        stamp_text = str((metadata or {}).get("stampText") or "").strip()
        product_code = stamp_extract.get("productCode")
        stamp_source = stamp_extract.get("productCodeSource")

        if not product_code and not stamp_text:
            product_code = cls._extract_fallback_from_text(full_text)

        if not product_code:
            product_code = ChatDrawingProductCodeResolutionService.extract_product_code_from_filename(
                str((metadata or {}).get("filename") or "")
            )

            if product_code:
                stamp_source = stamp_source or "filename"

        bom_text = str((metadata or {}).get("bomText") or "").strip()

        if not product_code and bom_text:
            product_code = cls._extract_fallback_from_text(bom_text)
            stamp_source = stamp_source or "bom_region"

        return product_code, stamp_source

    @classmethod
    def _extract_fallback_from_text(cls, text: str) -> str | None:
        codes_90 = ChatDrawingPatternsService.finished_product_code().findall(text)

        if codes_90:
            return ChatProductQueryIntentService.normalize_product_code(codes_90[0])

        product_code = ChatProductQueryIntentService.extract_product_code(text)

        if product_code and ChatDrawingPatternsService.finished_product_code_anchor().match(
            product_code
        ):
            return product_code

        codes_50 = ChatDrawingPatternsService.intermediate_code().findall(text)

        if codes_50:
            return ChatProductQueryIntentService.normalize_product_code(codes_50[0])

        return None
