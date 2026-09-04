"""Loader canônico do bundle ``user_query_improvement``."""

from __future__ import annotations

import re
from functools import lru_cache

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "user_query_improvement"


class ChatUserQueryImprovementContentService:
    BUNDLE = _BUNDLE

    @classmethod
    def enabled(cls) -> bool:
        node = ChatAssistantContentService.get_node(_BUNDLE)
        if not isinstance(node, dict):
            return True
        return bool(node.get("enabled", True))

    @classmethod
    def limit_int(cls, key: str, default: int) -> int:
        node = ChatAssistantContentService.get_node(_BUNDLE, "limits")
        if not isinstance(node, dict):
            return default
        try:
            return int(node.get(key, default))
        except (TypeError, ValueError):
            return default

    @classmethod
    def limit_float(cls, key: str, default: float) -> float:
        node = ChatAssistantContentService.get_node(_BUNDLE, "limits")
        if not isinstance(node, dict):
            return default
        try:
            return float(node.get(key, default))
        except (TypeError, ValueError):
            return default

    @classmethod
    def system_prompt(cls) -> str:
        return str(
            ChatAssistantContentService.get(_BUNDLE, "systemPrompt", default="") or ""
        ).strip()

    @classmethod
    def format_user_prompt(cls, *, message: str) -> str:
        template = str(
            ChatAssistantContentService.get(
                _BUNDLE,
                "userPromptTemplate",
                default="Pergunta do usuário:\n{message}\n\nPergunta corrigida:",
            )
            or ""
        )
        return template.format(message=str(message or "").strip())

    @classmethod
    def broken_operational_stems(cls) -> tuple[str, ...]:
        return tuple(
            str(item).strip().lower()
            for item in ChatAssistantContentService.list(
                _BUNDLE, "gate", "brokenOperationalStems"
            )
            if str(item).strip()
        )

    @classmethod
    def cadastro_verb_stems(cls) -> tuple[str, ...]:
        return tuple(
            str(item).strip().lower()
            for item in ChatAssistantContentService.list(
                _BUNDLE, "gate", "cadastroVerbStems"
            )
            if str(item).strip()
        )

    @classmethod
    def product_code_min_digits(cls) -> int:
        node = ChatAssistantContentService.get_node(_BUNDLE, "gate")
        if not isinstance(node, dict):
            return 5
        try:
            return max(5, int(node.get("productCodeMinDigits", 5)))
        except (TypeError, ValueError):
            return 5

    @classmethod
    @lru_cache(maxsize=8)
    def compile_skip_pattern(cls, key: str) -> re.Pattern[str] | None:
        source = ChatAssistantContentService.get(
            _BUNDLE, "skipPatterns", key, default=""
        )
        if not str(source or "").strip():
            return None
        return re.compile(str(source), re.IGNORECASE | re.MULTILINE)

    @classmethod
    def reason(cls, key: str) -> str:
        return str(
            ChatAssistantContentService.get(_BUNDLE, "reasons", key, default=key) or key
        ).strip()
