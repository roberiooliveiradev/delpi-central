"""Normalização de códigos extraídos do PDF — apenas formato do token lido."""

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
        return code or None
