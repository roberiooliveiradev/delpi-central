"""Vocabulário PT de intenção/refinamento SQL — bundle ``sql_intent_vocabulary.json``."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "sql_intent_vocabulary"


class ChatSqlIntentVocabularyService:
    @classmethod
    def terms(cls, *path: str) -> tuple[str, ...]:
        return tuple(ChatAssistantContentService.list(_BUNDLE, *path))

    @classmethod
    def node(cls, *path: str) -> Any:
        return ChatAssistantContentService.get_node(_BUNDLE, *path)

    @classmethod
    def synonym_map(cls, *path: str) -> dict[str, tuple[str, ...]]:
        raw = cls.node(*path)

        if not isinstance(raw, dict):
            return {}

        resolved: dict[str, tuple[str, ...]] = {}

        for key, value in raw.items():
            if isinstance(value, list):
                resolved[str(key)] = tuple(str(item) for item in value if str(item).strip())

        return resolved

    @classmethod
    def mode_pattern_map(cls) -> dict[str, tuple[str, ...]]:
        raw = cls.node("advancedSqlSpecialist", "modePatterns")

        if not isinstance(raw, dict):
            return {}

        return {
            str(mode): tuple(str(item) for item in triggers if str(item).strip())
            for mode, triggers in raw.items()
            if isinstance(triggers, list)
        }

    @classmethod
    def planner_hints(cls) -> tuple[tuple[tuple[str, ...], str], ...]:
        raw = cls.node("advancedSqlSpecialist", "plannerHints")

        if not isinstance(raw, list):
            return ()

        hints: list[tuple[tuple[str, ...], str]] = []

        for item in raw:
            if not isinstance(item, dict):
                continue

            triggers = tuple(
                str(token)
                for token in (item.get("triggers") or [])
                if str(token).strip()
            )
            hint = str(item.get("hint") or "").strip()

            if triggers and hint:
                hints.append((triggers, hint))

        return tuple(hints)

    @classmethod
    def query_advisor_patterns(cls) -> tuple[tuple[tuple[str, ...], str, str], ...]:
        raw = cls.node("queryPatternAdvisor", "patterns")

        if not isinstance(raw, list):
            return ()

        patterns: list[tuple[tuple[str, ...], str, str]] = []

        for item in raw:
            if not isinstance(item, dict):
                continue

            triggers = tuple(
                str(token)
                for token in (item.get("triggers") or [])
                if str(token).strip()
            )
            code = str(item.get("code") or "").strip()
            guidance = str(item.get("guidance") or "").strip()

            if triggers and code and guidance:
                patterns.append((triggers, code, guidance))

        return tuple(patterns)

    @classmethod
    def insight_text(cls, key: str, *, default: str = "", **values: str) -> str:
        template = ChatAssistantContentService.get(
            _BUNDLE,
            "resultAnalyzer",
            "insights",
            key,
            default=default,
        )

        if not template:
            return default

        try:
            return template.format(**values)
        except KeyError:
            return template
