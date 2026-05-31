"""Detecta mensagens geradas pelos chips «Próximos passos» (consulta explícita)."""

from __future__ import annotations

import re
from functools import lru_cache

from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.infrastructure.content.content_service import ContentService

_PRODUCT_CODE_RE = re.compile(r"\b\d{5,9}\b")


@lru_cache(maxsize=1)
def _query_templates() -> tuple[str, ...]:
    playbook = ContentService.personality_playbook()
    raw = playbook.get("followUpQueries") or {}

    templates: list[str] = []

    for template in raw.values():
        normalized = str(template or "").strip().lower()

        if not normalized or "{product_code}" not in normalized:
            continue

        templates.append(normalized)

    return tuple(templates)


class ChatFollowUpChipQueryService:
    @classmethod
    def is_explicit_chip_query(cls, message: str | None) -> bool:
        normalized = cls._normalize(message)

        if not normalized:
            return False

        if not ChatProductQueryIntentService.extract_product_code(message):
            return False

        for template in _query_templates():
            if cls._matches_template(normalized, template):
                return True

        return cls._matches_operational_shortcuts(normalized)

    @classmethod
    def _normalize(cls, message: str | None) -> str:
        return re.sub(r"\s+", " ", str(message or "").strip().lower())

    @classmethod
    def _matches_template(cls, normalized: str, template: str) -> bool:
        parts = template.split("{product_code}")

        if len(parts) != 2:
            return False

        prefix, suffix = parts
        pattern = rf"^{re.escape(prefix)}(\d{{5,9}}){re.escape(suffix)}$"

        return re.match(pattern, normalized) is not None

    @classmethod
    def _matches_operational_shortcuts(cls, normalized: str) -> bool:
        if not _PRODUCT_CODE_RE.search(normalized):
            return False

        markers = (
            r"\bqual o estoque do produto\b",
            r"\bliste os fornecedores do produto\b",
            r"\bmostre a estrutura do produto\b",
            r"\bmostre o faturamento do produto\b",
            r"\bonde o produto\b.*\bé usado\b",
            r"\bme fale do produto\b",
        )

        return any(re.search(marker, normalized) for marker in markers)
