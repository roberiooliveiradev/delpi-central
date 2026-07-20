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
        r"\bexpedi(?:cao|ção)\b",
        r"\bexclusiv",
        r"\binspe[cç][aã]o\b",
        r"\bdescri[cç][aã]o\b",
        r"\bmais\s+informa",
        r"\bagora\b",
        r"\bdele\b",
        # «desse/dessa» sozinho casa «desse mês» (período) — só follow-up com âncora.
        r"\bdesse\s+(?:produto|item|c[oó]digo|componente|material)\b",
        r"\bdessa\s+(?:produto|op(?:ortunidade)?|ordem|estrutura|nota)\b",
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

        if re.search(r"\bexclusiv", normalized):
            if cls._looks_like_global_exclusive_catalog_listing(normalized):
                return None

            return "structure_exclusivity"

        if re.search(r"\bestrutura\b", normalized):
            return "structure"

        if re.search(r"\bexpedi(?:cao|ção)\b", normalized):
            return "shipping"

        if re.search(r"\broteiro\b", normalized):
            return "routing"

        if re.search(r"\bformato\b|\btabela\b", normalized):
            return "format_change"

        return "entity_reuse"

    @classmethod
    def _looks_like_global_exclusive_catalog_listing(cls, normalized: str) -> bool:
        """Listagem global (catálogo) — não follow-up de exclusividade do PA em foco."""
        text = str(normalized or "").strip().lower()

        if not text:
            return False

        if re.search(r"\bestrutura\b", text) and re.search(
            r"\b(desse|dessa|dele|dela|esse produto|esse item|desse produto|dessa estrutura)\b",
            text,
        ):
            return False

        global_markers = (
            "materia prima",
            "materia-prima",
            "matéria-prima",
            "matérias-primas",
            "materias-primas",
            "produtos com",
            "produtos tem",
            "pas com",
            "pa com",
            "catalogo de",
            "catálogo de",
        )

        return any(marker in text for marker in global_markers)
