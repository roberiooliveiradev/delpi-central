"""Detecta instruções de comportamento persistentes na mensagem do usuário."""

from __future__ import annotations

import re

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)


class ChatBehaviorInstructionService:
    _TABLE_PATTERNS = (
        r"\bem\s+tabela\b",
        r"\bformato\s+tabela\b",
        r"\bresponda\s+em\s+tabela\b",
        r"\bsempre\s+em\s+tabela\b",
    )
    _DIRECT_PATTERNS = (
        r"\bseja\s+direto\b",
        r"\bresposta\s+direta\b",
        r"\bsem\s+enrola",
        r"\bobjetivo\b",
    )
    _SIMPLE_PATTERNS = (
        r"\blinguagem\s+simples\b",
        r"\bexplique\s+simples\b",
        r"\bsem\s+jarg",
    )
    _PERSISTENT_MARKERS = (
        r"\bdaqui\s+pra\s+frente\b",
        r"\bde\s+agora\s+em\s+diante\b",
        r"\bsempre\b",
        r"\bnas\s+pr[oó]ximas\b",
    )
    _FINAL_ONLY_PATTERNS = (
        r"\bs[oó]\s+a\s+vers[aã]o\s+final\b",
        r"\bapenas\s+a\s+vers[aã]o\s+corrigida\b",
        r"\bsem\s+explica[cç][aã]o\b",
    )

    @classmethod
    def detect(cls, message: str | None) -> dict[str, str]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message or "")

        if not normalized:
            return {}

        instructions: dict[str, str] = {}
        persistent = any(re.search(pattern, normalized) for pattern in cls._PERSISTENT_MARKERS)

        if any(re.search(pattern, normalized) for pattern in cls._TABLE_PATTERNS):
            instructions["responseFormat"] = "table"

        if any(re.search(pattern, normalized) for pattern in cls._DIRECT_PATTERNS):
            instructions["tone"] = "direct"

        if any(re.search(pattern, normalized) for pattern in cls._SIMPLE_PATTERNS):
            instructions["tone"] = "simple"

        if any(re.search(pattern, normalized) for pattern in cls._FINAL_ONLY_PATTERNS):
            instructions["finalVersionOnly"] = "true"

        if persistent and instructions:
            instructions["scope"] = "session"

        return instructions
