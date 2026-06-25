"""Delegate — especialista SQL avançado."""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from functools import lru_cache
from typing import Any

from app.domain.services.chat_sql_intent_service import ChatSqlIntentService
from app.domain.services.chat_sql_intent_vocabulary_service import ChatSqlIntentVocabularyService
from app.domain.services.chat_domain_config_service import ChatDomainConfigService
from app.domain.services.chat_message_normalization_service import ChatMessageNormalizationService
from app.domain.services.chat_sql_memory_workspace_service import ChatSqlMemoryWorkspaceService
from app.domain.services.chat_sql_performance_advisor_service import ChatSqlPerformanceAdvisorService
from app.domain.services.chat_sql_query_refinement_service import ChatSqlQueryRefinementService
from app.domain.services.chat_sql_safety_service import ChatSqlSafetyService

from app.domain.services.chat_advanced_sql_specialist.chat_advanced_sql_specialist_constants import (
    SQL_BLOCK_RE as _SQL_BLOCK_RE,
)
from app.domain.services.chat_advanced_sql_specialist.chat_advanced_sql_specialist_facade_access import (
    sql_specialist_service,
)
from app.domain.services.chat_advanced_sql_specialist.chat_advanced_sql_specialist_types import (
    SqlSpecialistMode,
    _MODE_ORDER,
    _interactivity_content,
)



class ChatAdvancedSqlSpecialistActivationService:
    @classmethod
    def _activation_terms(cls) -> tuple[str, ...]:
        return ChatSqlIntentVocabularyService.terms(
            "advancedSqlSpecialist",
            "activationTerms",
        )

    @classmethod
    def _incremental_edit_terms(cls) -> tuple[str, ...]:
        return ChatSqlIntentVocabularyService.incremental_edit_terms()

    @classmethod
    def _mode_patterns(cls) -> tuple[tuple[SqlSpecialistMode, tuple[str, ...]], ...]:
        mapping = ChatSqlIntentVocabularyService.mode_pattern_map()
        resolved: list[tuple[SqlSpecialistMode, tuple[str, ...]]] = []

        for mode in _MODE_ORDER:
            patterns = mapping.get(mode)

            if patterns:
                resolved.append((mode, patterns))

        return tuple(resolved)

    @classmethod
    def should_activate(
        cls,
        message: str | None,
        *,
        workspace_context: dict | None = None,
    ) -> bool:
        if not cls._sql_authoring_enabled(workspace_context):
            return False

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if ChatSqlSafetyService.contains_destructive_sql(message):
            return True

        if ChatSqlIntentService.is_authoring_request(message):
            return True

        if ChatSqlIntentService.should_auto_execute_sql(str(message or "")):
            return True

        if ChatSqlQueryRefinementService.is_sql_follow_up(
            str(message or ""),
            previous_messages=None,
        ):
            return True

        if ChatSqlPerformanceAdvisorService.extract_sql_block(message):
            return True

        return any(term in normalized for term in cls._activation_terms())

    @classmethod
    def classify_mode(
        cls,
        message: str | None,
        *,
        previous_messages: list[Any] | None = None,
    ) -> SqlSpecialistMode:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return "none"

        for mode, patterns in cls._mode_patterns():
            if mode in {"analyze_result", "visualize", "explain", "review", "optimize", "schema_explore"}:
                if any(pattern in normalized for pattern in patterns):
                    return mode

        if ChatSqlQueryRefinementService.is_sql_follow_up(
            str(message or ""),
            previous_messages=previous_messages,
        ):
            return "incremental_edit"

        if any(term in normalized for term in cls._incremental_edit_terms()):
            workspace = ChatSqlMemoryWorkspaceService.build_workspace(
                message=message,
                previous_messages=previous_messages,
            )

            if workspace.get("hasActiveQuery") or "anterior" in normalized:
                return "incremental_edit"

        if ChatSqlIntentService.should_auto_execute_sql(str(message or "")):
            return "execute"

        if ChatSqlPerformanceAdvisorService.extract_sql_block(message) and any(
            token in normalized for token in ("revisa", "valida", "corrig", "ajust")
        ):
            return "review"

        if ChatSqlPerformanceAdvisorService.extract_sql_block(message) and "explique" in normalized:
            return "explain"

        if ChatSqlIntentService.is_authoring_request(message):
            return "create"

        if any(term in normalized for term in cls._activation_terms()):
            return "create"

        return "none"

    @classmethod
    def _sql_authoring_enabled(cls, workspace_context: dict | None) -> bool:
        skills = (workspace_context or {}).get("skills") or {}
        sql_authoring = skills.get("sqlAuthoring")

        if sql_authoring is None:
            sql_authoring = ChatDomainConfigService.chat_default_sql_authoring_skill_enabled()

        return bool(sql_authoring)

