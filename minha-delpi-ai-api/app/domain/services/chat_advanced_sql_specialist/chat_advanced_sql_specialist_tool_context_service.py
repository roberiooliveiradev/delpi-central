"""Delegate — especialista SQL avançado."""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from functools import lru_cache
from typing import Any

from app.domain.services.chat_sql_intent_service import ChatSqlIntentService
from app.domain.services.chat_sql_intent_vocabulary_service import ChatSqlIntentVocabularyService
from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

from app.domain.services.chat_advanced_sql_specialist.chat_advanced_sql_specialist_prompt_service import (
    ChatAdvancedSqlSpecialistPromptService,
)
from app.domain.services.chat_advanced_sql_specialist.chat_advanced_sql_specialist_constants import (
    SQL_BLOCK_RE as _SQL_BLOCK_RE,
)
from app.domain.services.chat_advanced_sql_specialist.chat_advanced_sql_specialist_facade_access import (
    sql_specialist_service,
)
from app.domain.services.chat_advanced_sql_specialist.chat_advanced_sql_specialist_types import (
    SqlSpecialistMode,
    _interactivity_content,
)



class ChatAdvancedSqlSpecialistToolContextService:
    @classmethod
    def enrich_tool_context(
        cls,
        *,
        message: str,
        result: dict,
        workspace_context: dict | None = None,
        previous_messages: list[Any] | None = None,
    ) -> dict:
        snapshot = sql_specialist_service().build_pipeline_snapshot(
            message=message,
            workspace_context=workspace_context,
            previous_messages=previous_messages,
            tool_calls=result.get("toolCalls") if isinstance(result.get("toolCalls"), list) else None,
        )

        if result.get("suppressAdvancedSqlEnrichment"):
            cleaned = dict(result)
            cleaned.pop("suppressAdvancedSqlEnrichment", None)
            return cleaned

        from app.domain.services.chat_presentation_format_refinement_service import (
            ChatPresentationFormatRefinementService,
        )

        if (
            ChatPresentationFormatRefinementService.looks_like_format_refinement(message)
            and cls._has_successful_operational_tool_result(result)
        ):
            from app.domain.services.chat_tool_context_presentation_service import (
                ChatToolContextPresentationService,
            )

            tool_calls = result.get("toolCalls")
            presentation_answer = ChatToolContextPresentationService.prefer_presentation_direct_answer(
                result.get("directAnswer"),
                tool_calls if isinstance(tool_calls, list) else [],
                message=message,
            )
            updated = dict(result)

            if presentation_answer:
                updated["directAnswer"] = presentation_answer

            updated["skipRag"] = True
            updated.pop("sqlRequiresLlm", None)

            return updated

        if not snapshot:
            return result

        tool_calls = result.get("toolCalls")

        if (
            (not isinstance(tool_calls, list) or not tool_calls)
            and not str(result.get("context") or "").strip()
            and not result.get("directAnswer")
            and not sql_specialist_service().requires_llm_response(snapshot)
        ):
            return result

        updated = dict(result)
        snapshot = {**snapshot, "message": message}
        updated["sqlAdvanced"] = snapshot
        supplement = ChatAdvancedSqlSpecialistPromptService.build_prompt_supplement(snapshot)

        if supplement:
            existing = str(updated.get("context") or "").strip()
            updated["context"] = f"{existing}\n\n{supplement}".strip() if existing else supplement

        if sql_specialist_service().requires_llm_response(snapshot):
            updated.pop("directAnswer", None)
            if not cls._has_successful_operational_tool_result(updated):
                updated["skipRag"] = False
            updated["sqlRequiresLlm"] = True
            updated = sql_specialist_service().strip_schema_catalog_presentations(updated)

        return updated

    @classmethod
    def _has_successful_operational_tool_result(cls, result: dict) -> bool:
        tool_calls = result.get("toolCalls")

        if not isinstance(tool_calls, list):
            return False

        for call in tool_calls:
            if str(call.get("name") or "") != "execute_external_action":
                continue

            metadata = call.get("metadata") or {}

            if not metadata.get("ok") or metadata.get("sqlSchemaPrefetch"):
                continue

            if sql_specialist_service().is_schema_prefetch_path(str(metadata.get("path") or "")):
                continue

            return True

        return False

    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict,
        *,
        message: str | None,
        workspace_context: dict | None = None,
        previous_messages: list[Any] | None = None,
        tool_calls: list | None = None,
    ) -> None:
        snapshot = sql_specialist_service().build_pipeline_snapshot(
            message=message,
            workspace_context=workspace_context,
            previous_messages=previous_messages,
            tool_calls=tool_calls,
        )

        if not snapshot:
            return

        metadata["sqlAdvanced"] = snapshot

