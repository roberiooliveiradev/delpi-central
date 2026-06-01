"""Detecção de follow-up operacional (mensagem vaga que reutiliza contexto)."""

from __future__ import annotations

import re

from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


class ChatFollowUpIntentService:
    _FOLLOW_UP_PATTERNS = (
        r"\bfornecedores?\b",
        r"\bestoque\b",
        r"\bnotas?\s+fiscais?\b",
        r"\bnf(?:e)?\s+de\s+sa[ií]da\b",
        r"\broteiro\b",
        r"\bestrutura\b",
        r"\binspe[cç][aã]o\b",
        r"\bdescri[cç][aã]o\b",
        r"\bmais\s+informa",
        r"\bagora\b",
        r"\bdele\b",
        r"\bdesse\b",
        r"\bdessa\b",
        r"\besse\s+produto\b",
        r"\besse\s+item\b",
        r"\bisso\b",
        r"\banterior\b",
    )

    @classmethod
    def is_operational_follow_up(cls, message: str | None) -> bool:
        normalized = (message or "").strip().lower()

        if not normalized:
            return False

        if ChatProductQueryIntentService.extract_product_code(message):
            return False

        return any(re.search(pattern, normalized) for pattern in cls._FOLLOW_UP_PATTERNS)

    @classmethod
    def follow_up_type(cls, message: str | None) -> str | None:
        if not cls.is_operational_follow_up(message):
            return None

        normalized = (message or "").strip().lower()

        if re.search(r"\bfornecedores?\b", normalized):
            return "supplier"

        if re.search(r"\bnotas?\s+fiscais?\b", normalized) and re.search(
            r"\bsa[ií]da\b", normalized
        ):
            return "outbound_invoice"

        if re.search(r"\bestoque\b", normalized):
            return "stock"

        if re.search(r"\bestrutura\b", normalized):
            return "structure"

        if re.search(r"\broteiro\b", normalized):
            return "routing"

        if re.search(r"\bformato\b|\btabela\b", normalized):
            return "format_change"

        return "entity_reuse"
