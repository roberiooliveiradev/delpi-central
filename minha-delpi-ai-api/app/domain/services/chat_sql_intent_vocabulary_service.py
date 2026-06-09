"""Vocabulário PT de intenção/refinamento SQL — bundle ``sql_intent_vocabulary.json``."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.domain.services.chat_assistant_vocabulary_service import (
    ChatAssistantVocabularyService,
)


class ChatSqlIntentVocabularyService(ChatAssistantVocabularyService):
    BUNDLE = "sql_intent_vocabulary"

    @classmethod
    def incremental_authoring_terms(cls) -> tuple[str, ...]:
        return cls.merge_terms(
            ("shared", "previousQueryTerms"),
            ("shared", "groupByCommandTerms"),
            ("queryRefinement", "incrementalAuthoringSpecific"),
        )

    @classmethod
    def incremental_edit_terms(cls) -> tuple[str, ...]:
        return cls.merge_terms(
            ("shared", "previousQueryTerms"),
            ("advancedSqlSpecialist", "incrementalEditSpecific"),
        )

    @classmethod
    def group_by_terms(cls) -> tuple[str, ...]:
        return cls.merge_terms(
            ("shared", "groupByCommandTerms"),
            ("shared", "groupByExtendedTerms"),
        )

    @classmethod
    def filter_prefix_terms(cls) -> tuple[str, ...]:
        return cls.merge_terms(
            ("shared", "filterPrefixTerms"),
        )

    @classmethod
    @lru_cache(maxsize=8)
    def column_definitions(cls, table_group: str) -> dict[str, dict[str, Any]]:
        raw = cls.node("queryRefinement", "columnDefinitions", table_group)

        if not isinstance(raw, dict):
            return {}

        resolved: dict[str, dict[str, Any]] = {}

        for key, definition in raw.items():
            if not isinstance(definition, dict):
                continue

            aliases = definition.get("aliases") or []

            resolved[str(key)] = {
                "aliases": tuple(str(item) for item in aliases if str(item).strip()),
                "select": str(definition.get("select") or ""),
                "group_by": str(definition.get("group_by") or ""),
                "result_alias": str(definition.get("result_alias") or ""),
            }

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
        return cls.format(
            "resultAnalyzer",
            "insights",
            key,
            default=default,
            **values,
        )
