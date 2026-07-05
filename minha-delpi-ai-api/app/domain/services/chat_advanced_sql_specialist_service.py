"""Especialista SQL avançado — fachada fina sobre delegates por responsabilidade."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_advanced_sql_specialist.chat_advanced_sql_specialist_activation_service import (
    ChatAdvancedSqlSpecialistActivationService,
)
from app.domain.services.chat_advanced_sql_specialist.chat_advanced_sql_specialist_follow_up_service import (
    ChatAdvancedSqlSpecialistFollowUpService,
)
from app.domain.services.chat_advanced_sql_specialist.chat_advanced_sql_specialist_pipeline_service import (
    ChatAdvancedSqlSpecialistPipelineService,
)
from app.domain.services.chat_advanced_sql_specialist.chat_advanced_sql_specialist_prompt_service import (
    ChatAdvancedSqlSpecialistPromptService,
)
from app.domain.services.chat_advanced_sql_specialist.chat_advanced_sql_specialist_prose_formatting_service import (
    ChatAdvancedSqlSpecialistProseFormattingService,
)
from app.domain.services.chat_advanced_sql_specialist.chat_advanced_sql_specialist_schema_prefetch_service import (
    ChatAdvancedSqlSpecialistSchemaPrefetchService,
)
from app.domain.services.chat_advanced_sql_specialist.chat_advanced_sql_specialist_tool_context_service import (
    ChatAdvancedSqlSpecialistToolContextService,
)
from app.domain.services.chat_advanced_sql_specialist.chat_advanced_sql_specialist_types import (
    SqlSpecialistMode,
)

__all__ = ["ChatAdvancedSqlSpecialistService", "SqlSpecialistMode"]


class ChatAdvancedSqlSpecialistService:
    """Fachada — ativação, pipeline, prefetch de schema, prosa SQL e contexto de tools."""

    SqlSpecialistMode = SqlSpecialistMode

    @classmethod
    def should_activate(cls, *args, **kwargs) -> bool:
        return ChatAdvancedSqlSpecialistActivationService.should_activate(*args, **kwargs)

    @classmethod
    def classify_mode(cls, *args, **kwargs) -> SqlSpecialistMode:
        return ChatAdvancedSqlSpecialistActivationService.classify_mode(*args, **kwargs)

    @classmethod
    def build_pipeline_snapshot(cls, *args, **kwargs) -> dict[str, Any] | None:
        return ChatAdvancedSqlSpecialistPipelineService.build_pipeline_snapshot(*args, **kwargs)

    @classmethod
    def build_planner_hints(cls, *args, **kwargs) -> list[str]:
        return ChatAdvancedSqlSpecialistPipelineService.build_planner_hints(*args, **kwargs)

    @classmethod
    def should_prefetch_schema(cls, *args, **kwargs) -> bool:
        return ChatAdvancedSqlSpecialistPipelineService.should_prefetch_schema(*args, **kwargs)

    @classmethod
    def requires_llm_response(cls, *args, **kwargs) -> bool:
        return ChatAdvancedSqlSpecialistPipelineService.requires_llm_response(*args, **kwargs)

    @classmethod
    def enrich_tool_context(cls, *args, **kwargs) -> dict:
        return ChatAdvancedSqlSpecialistToolContextService.enrich_tool_context(*args, **kwargs)

    @classmethod
    def attach_to_assistant_metadata(cls, *args, **kwargs) -> None:
        return ChatAdvancedSqlSpecialistToolContextService.attach_to_assistant_metadata(
            *args, **kwargs
        )

    @classmethod
    def is_schema_prefetch_path(cls, *args, **kwargs) -> bool:
        return ChatAdvancedSqlSpecialistSchemaPrefetchService.is_schema_prefetch_path(
            *args, **kwargs
        )

    @classmethod
    def is_table_search_prefetch_path(cls, *args, **kwargs) -> bool:
        return ChatAdvancedSqlSpecialistSchemaPrefetchService.is_table_search_prefetch_path(
            *args, **kwargs
        )

    @classmethod
    def turn_has_only_sql_schema_prefetch(cls, *args, **kwargs) -> bool:
        return ChatAdvancedSqlSpecialistSchemaPrefetchService.turn_has_only_sql_schema_prefetch(
            *args, **kwargs
        )

    @classmethod
    def should_treat_schema_as_internal(cls, *args, **kwargs) -> bool:
        return ChatAdvancedSqlSpecialistSchemaPrefetchService.should_treat_schema_as_internal(
            *args, **kwargs
        )

    @classmethod
    def annotate_schema_prefetch_tool_metadata(cls, *args, **kwargs) -> None:
        return ChatAdvancedSqlSpecialistSchemaPrefetchService.annotate_schema_prefetch_tool_metadata(
            *args, **kwargs
        )

    @classmethod
    def strip_schema_catalog_presentations(cls, *args, **kwargs) -> dict:
        return ChatAdvancedSqlSpecialistSchemaPrefetchService.strip_schema_catalog_presentations(
            *args, **kwargs
        )

    @classmethod
    def sanitize_tool_calls_for_client(cls, *args, **kwargs) -> list:
        return ChatAdvancedSqlSpecialistSchemaPrefetchService.sanitize_tool_calls_for_client(
            *args, **kwargs
        )

    @classmethod
    def compact_schema_prefetch_context(cls, *args, **kwargs) -> dict:
        return ChatAdvancedSqlSpecialistSchemaPrefetchService.compact_schema_prefetch_context(
            *args, **kwargs
        )

    @classmethod
    def format_sql_authoring_answer(cls, *args, **kwargs) -> str:
        return ChatAdvancedSqlSpecialistProseFormattingService.format_sql_authoring_answer(
            *args, **kwargs
        )

    @classmethod
    def normalize_protheus_sql_answer(cls, *args, **kwargs) -> str:
        return ChatAdvancedSqlSpecialistProseFormattingService.normalize_protheus_sql_answer(
            *args, **kwargs
        )

    @classmethod
    def build_prompt_supplement(cls, *args, **kwargs) -> str:
        return ChatAdvancedSqlSpecialistPromptService.build_prompt_supplement(*args, **kwargs)

    @classmethod
    def ensure_required_sql_block(cls, *args, **kwargs) -> str:
        return ChatAdvancedSqlSpecialistPromptService.ensure_required_sql_block(*args, **kwargs)

    @classmethod
    def build_follow_up_suggestions(cls, *args, **kwargs) -> list[dict[str, str]]:
        return ChatAdvancedSqlSpecialistFollowUpService.build_follow_up_suggestions(*args, **kwargs)

    @classmethod
    def resolve_max_tool_calls(cls, *args, **kwargs) -> int:
        return ChatAdvancedSqlSpecialistFollowUpService.resolve_max_tool_calls(*args, **kwargs)

    # --- Delegates privados (testes legados / patches) ---

    @classmethod
    def _activation_terms(cls):
        return ChatAdvancedSqlSpecialistActivationService._activation_terms()

    @classmethod
    def _incremental_edit_terms(cls):
        return ChatAdvancedSqlSpecialistActivationService._incremental_edit_terms()

    @classmethod
    def _mode_patterns(cls):
        return ChatAdvancedSqlSpecialistActivationService._mode_patterns()

    @classmethod
    def _sql_authoring_enabled(cls, workspace_context: dict | None) -> bool:
        return ChatAdvancedSqlSpecialistActivationService._sql_authoring_enabled(
            workspace_context
        )

    @classmethod
    def _has_successful_operational_tool_result(cls, result: dict) -> bool:
        return ChatAdvancedSqlSpecialistToolContextService._has_successful_operational_tool_result(
            result
        )

    @classmethod
    def _sql_authoring_intro(cls) -> str:
        return ChatAdvancedSqlSpecialistProseFormattingService._sql_authoring_intro()

    @classmethod
    def _sql_authoring_intro_re(cls):
        return ChatAdvancedSqlSpecialistProseFormattingService._sql_authoring_intro_re()

    @classmethod
    def _normalize_prose_chunk(cls, value: str) -> str:
        return ChatAdvancedSqlSpecialistProseFormattingService._normalize_prose_chunk(value)

    @classmethod
    def _prose_chunks_similar(cls, left: str, right: str) -> bool:
        return ChatAdvancedSqlSpecialistProseFormattingService._prose_chunks_similar(left, right)

    @classmethod
    def _strip_redundant_sql_tail_prose(cls, text: str) -> str:
        return ChatAdvancedSqlSpecialistProseFormattingService._strip_redundant_sql_tail_prose(text)

    @classmethod
    def _dedupe_sql_authoring_prose(cls, text: str) -> str:
        return ChatAdvancedSqlSpecialistProseFormattingService._dedupe_sql_authoring_prose(text)

    @classmethod
    def _extract_sql_from_fence(cls, fence: str) -> str:
        return ChatAdvancedSqlSpecialistProseFormattingService._extract_sql_from_fence(fence)

    @classmethod
    def _collect_unique_authoring_prose(cls, text: str) -> list[str]:
        return ChatAdvancedSqlSpecialistProseFormattingService._collect_unique_authoring_prose(text)

    @classmethod
    def _canonicalize_sql_authoring_layout(cls, text: str) -> str:
        return ChatAdvancedSqlSpecialistProseFormattingService._canonicalize_sql_authoring_layout(
            text
        )

    @classmethod
    def _column_hints_from_prefetch(cls, tool_calls: list | None) -> list[str]:
        return ChatAdvancedSqlSpecialistPromptService._column_hints_from_prefetch(tool_calls)

    @classmethod
    def _authoring_sql_from_message(cls, message: str | None, columns: list[str]) -> str | None:
        return ChatAdvancedSqlSpecialistPromptService._authoring_sql_from_message(
            message, columns
        )

    @classmethod
    def _example_join_sql_for_tables(cls, tables: list[str]) -> str | None:
        return ChatAdvancedSqlSpecialistPromptService._example_join_sql_for_tables(tables)

    @classmethod
    def _extract_column_names_from_schema_payload(cls, data: object) -> list[str]:
        return ChatAdvancedSqlSpecialistPromptService._extract_column_names_from_schema_payload(
            data
        )


ChatAdvancedSqlSpecialistService.SQL_AUTHORING_INTRO = (
    ChatAdvancedSqlSpecialistProseFormattingService._sql_authoring_intro()
)
