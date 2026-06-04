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
    _SHORT_ANSWER_PATTERNS = (
        r"\bresponda\s+curto\b",
        r"\brespostas?\s+curtas?\b",
        r"\bseja\s+conciso\b",
        r"\bresumo\s+curto\b",
    )
    _FORMAL_TONE_PATTERNS = (
        r"\btom\s+formal\b",
        r"\buse\s+tom\s+formal\b",
        r"\bsempre\s+formal\b",
    )
    _TOPICS_PATTERNS = (
        r"\bem\s+t[oó]picos\b",
        r"\bresponda\s+em\s+t[oó]picos\b",
    )
    _TEXT_FORMAT_PATTERNS = (
        r"\bsempre\s+em\s+txt\b",
        r"\bsempre\s+em\s+texto\b",
        r"\bresponda\s+em\s+texto\b",
        r"\bresponda\s+em\s+txt\b",
        r"\bsempre\s+s[oó]\s+texto\b",
        r"\bsempre\s+s[oó]\s+em\s+texto\b",
    )
    _TREE_FORMAT_PATTERNS = (
        r"\bsempre\s+em\s+[áa]rvore\b",
        r"\bresponda\s+em\s+[áa]rvore\b",
        r"\bformato\s+[áa]rvore\b",
        r"\bprefer[io]\s+[áa]rvore\b",
    )
    _CHART_FORMAT_PATTERNS = (
        r"\bsempre\s+em\s+gr[aá]fico\b",
        r"\bresponda\s+em\s+gr[aá]fico\b",
        r"\bformato\s+gr[aá]fico\b",
        r"\bprefer[io]\s+gr[aá]fico\b",
    )
    # «não use ferramentas sem eu pedir» — preferência inerentemente persistente.
    _TOOLS_ON_REQUEST_PATTERNS = (
        r"\bn[aã]o\s+use\s+ferramentas?\s+sem\s+eu\s+pedir\b",
        r"\bn[aã]o\s+use\s+ferramentas?\s+sem\s+pedir\b",
        r"\bn[aã]o\s+chame\s+ferramentas?\s+sem\s+eu\s+pedir\b",
        r"\bn[aã]o\s+consulte\s+sem\s+eu\s+pedir\b",
        r"\bn[aã]o\s+use\s+ferramentas?\s+sem\s+autoriza",
        r"\bs[oó]\s+use\s+ferramentas?\s+(?:quando|se)\s+eu\s+pedir\b",
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

        if any(re.search(pattern, normalized) for pattern in cls._SHORT_ANSWER_PATTERNS):
            instructions["answerLength"] = "short"

        if any(re.search(pattern, normalized) for pattern in cls._FORMAL_TONE_PATTERNS):
            instructions["tone"] = "formal"

        if any(re.search(pattern, normalized) for pattern in cls._TOPICS_PATTERNS):
            instructions["responseFormat"] = "topics"

        if any(re.search(pattern, normalized) for pattern in cls._TEXT_FORMAT_PATTERNS):
            instructions["responseFormat"] = "text"

        if any(re.search(pattern, normalized) for pattern in cls._TREE_FORMAT_PATTERNS):
            instructions["responseFormat"] = "tree"

        if any(re.search(pattern, normalized) for pattern in cls._CHART_FORMAT_PATTERNS):
            instructions["responseFormat"] = "chart"

        if any(re.search(pattern, normalized) for pattern in cls._TOOLS_ON_REQUEST_PATTERNS):
            instructions["toolsPolicy"] = "on_request"
            persistent = True

        if persistent and instructions:
            instructions["scope"] = "session"

        return instructions
