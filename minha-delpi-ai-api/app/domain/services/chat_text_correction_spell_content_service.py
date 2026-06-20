"""Configuração declarativa do preflight LanguageTool na correção textual."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "text_correction_spell_check"


class ChatTextCorrectionSpellContentService:
    @classmethod
    def bundle(cls) -> dict[str, Any]:
        payload = ChatAssistantContentService.get_node(_BUNDLE)

        return payload if isinstance(payload, dict) else {}

    @classmethod
    def catalog_enabled(cls) -> bool:
        return bool(cls.bundle().get("enabled", True))

    @classmethod
    def limit_int(cls, key: str, default: int) -> int:
        value = cls.bundle().get(key)

        if isinstance(value, int) and value > 0:
            return value

        return default

    @classmethod
    def ignored_rule_ids(cls) -> frozenset[str]:
        raw = cls.bundle().get("ignoredRuleIds")

        if not isinstance(raw, list):
            return frozenset()

        return frozenset(str(item).strip() for item in raw if str(item).strip())

    @classmethod
    def ignored_categories(cls) -> frozenset[str]:
        raw = cls.bundle().get("ignoredCategories")

        if not isinstance(raw, list):
            return frozenset()

        return frozenset(str(item).strip() for item in raw if str(item).strip())

    @classmethod
    def protected_patterns(cls) -> tuple[re.Pattern[str], ...]:
        raw = cls.bundle().get("protectedPatterns")

        if not isinstance(raw, list):
            return ()

        compiled: list[re.Pattern[str]] = []

        for item in raw:
            pattern = str(item or "").strip()

            if not pattern:
                continue

            compiled.append(re.compile(pattern, re.IGNORECASE))

        return tuple(compiled)

    @classmethod
    def prompt_text(cls, *path: str, default: str = "") -> str:
        node: Any = cls.bundle().get("prompt") or {}

        for key in path:
            if not isinstance(node, dict):
                return default

            node = node.get(key)

        return str(node or default).strip() or default

    @classmethod
    def metrics_engine_label(cls) -> str:
        metrics = cls.bundle().get("metrics")

        if isinstance(metrics, dict):
            label = str(metrics.get("engine") or "").strip()

            if label:
                return label

        return "languagetool"

    @classmethod
    def format(cls, template_key: str, **values: object) -> str:
        template = cls.prompt_text(template_key)

        if not template:
            return ""

        try:
            return template.format(**values)
        except (KeyError, ValueError):
            return template
