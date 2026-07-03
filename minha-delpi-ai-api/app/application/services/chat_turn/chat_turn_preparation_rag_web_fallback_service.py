"""Fallback pós-RAG: pesquisa na web quando a base interna não trouxe trechos."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from app.domain.services.chat_platform_internal_tools_service import (
    PLATFORM_INTERNAL_TOOL_NAMES,
)
from app.domain.services.chat_web_search_intent_service import ChatWebSearchIntentService


@dataclass(frozen=True)
class ChatTurnPreparationRagWebFallbackResult:
    applied: bool
    direct_answer: str | None = None
    tool_context: dict | None = None
    tool_calls: list | None = None
    sources: list | None = None


class ChatTurnPreparationRagWebFallbackService:
    @staticmethod
    def _web_search_already_ran(
        *,
        tool_calls: list | None,
        tool_context: dict | None,
    ) -> bool:
        for item in tool_calls or []:
            if str(item.get("name") or "") == "web_search":
                return True

        if isinstance(tool_context, dict):
            if tool_context.get("webSearchPayload") or tool_context.get("webSources"):
                return True

            for item in tool_context.get("toolCalls") or []:
                if str(item.get("name") or "") == "web_search":
                    return True

        return False

    @staticmethod
    def _internal_rag_is_empty(rag: dict | None) -> bool:
        if not isinstance(rag, dict):
            return True

        return len(rag.get("sources") or []) == 0

    @classmethod
    def _operational_llm_narration_pending(
        cls,
        *,
        tool_calls: list | None,
        tool_context: dict | None,
    ) -> bool:
        if not isinstance(tool_calls, list):
            return False

        has_external_action = any(
            str(item.get("name") or "") == "execute_external_action" for item in tool_calls
        )

        if not has_external_action:
            return False

        if isinstance(tool_context, dict):
            from app.domain.services.chat_operational_narrative_synthesis_service import (
                ChatOperationalNarrativeSynthesisService,
            )

            effect = str(tool_context.get("responseModeEffect") or "").strip()

            if ChatOperationalNarrativeSynthesisService.is_llm_synthesis_effect(effect):
                return True

        for item in tool_calls:
            if str(item.get("name") or "") != "execute_external_action":
                continue

            metadata = item.get("metadata")

            if not isinstance(metadata, dict):
                continue

            if metadata.get("ok") is True and (
                metadata.get("dataOnlyPresentation")
                or metadata.get("llmProseDecoupled")
                or str(metadata.get("proseDeliveryMode") or "") == "llm"
            ):
                return True

        return False

    @staticmethod
    def _platform_tool_already_ran(
        *,
        tool_calls: list | None,
        tool_context: dict | None,
    ) -> bool:
        items: list = list(tool_calls or [])

        if isinstance(tool_context, dict):
            items.extend(tool_context.get("toolCalls") or [])

        for item in items:
            if not isinstance(item, dict):
                continue

            name = str(item.get("name") or "").strip()

            if name not in PLATFORM_INTERNAL_TOOL_NAMES:
                continue

            metadata = item.get("metadata")

            if not isinstance(metadata, dict):
                return True

            if metadata.get("ok") is False:
                continue

            return True

        return False

    @classmethod
    def should_apply(
        cls,
        *,
        message: str,
        skip_rag: bool,
        direct_answer: str | None,
        rag: dict | None,
        tool_calls: list | None,
        tool_context: dict | None,
        text_task_pure: bool,
    ) -> bool:
        if skip_rag or direct_answer or text_task_pure:
            return False

        if cls._web_search_already_ran(tool_calls=tool_calls, tool_context=tool_context):
            return False

        if cls._operational_llm_narration_pending(
            tool_calls=tool_calls,
            tool_context=tool_context,
        ):
            return False

        if cls._platform_tool_already_ran(
            tool_calls=tool_calls,
            tool_context=tool_context,
        ):
            return False

        if not cls._internal_rag_is_empty(rag):
            return False

        return ChatWebSearchIntentService.should_try_web_after_empty_rag(message)

    @classmethod
    def apply(
        cls,
        *,
        message: str,
        skip_rag: bool,
        direct_answer: str | None,
        rag: dict | None,
        tool_calls: list | None,
        tool_context: dict | None,
        sources: list | None,
        text_task_pure: bool,
        pipeline_stages: list[str],
        run_web_search_fallback: Callable[..., dict | None] | None,
    ) -> ChatTurnPreparationRagWebFallbackResult:
        if run_web_search_fallback is None:
            return ChatTurnPreparationRagWebFallbackResult(applied=False)

        if not cls.should_apply(
            message=message,
            skip_rag=skip_rag,
            direct_answer=direct_answer,
            rag=rag,
            tool_calls=tool_calls,
            tool_context=tool_context,
            text_task_pure=text_task_pure,
        ):
            return ChatTurnPreparationRagWebFallbackResult(applied=False)

        fallback_context = run_web_search_fallback()

        if not isinstance(fallback_context, dict):
            return ChatTurnPreparationRagWebFallbackResult(applied=False)

        if "rag_web_fallback" not in pipeline_stages:
            pipeline_stages.append("rag_web_fallback")

        if "tools" not in pipeline_stages:
            pipeline_stages.append("tools")

        merged_tool_calls = list(tool_calls or [])
        fallback_calls = list(fallback_context.get("toolCalls") or [])

        if fallback_calls:
            merged_tool_calls.extend(fallback_calls)

        merged_sources = list(sources or [])
        fallback_sources = list(fallback_context.get("webSources") or [])

        if fallback_sources:
            merged_sources = [*fallback_sources, *merged_sources]

        merged_context = dict(tool_context or {})
        merged_context.update(
            {
                key: fallback_context[key]
                for key in (
                    "context",
                    "toolCalls",
                    "nativeToolCalling",
                    "webSources",
                    "webSearchPayload",
                    "skipRag",
                )
                if key in fallback_context
            }
        )

        if merged_tool_calls:
            merged_context["toolCalls"] = merged_tool_calls

        fallback_direct = fallback_context.get("directAnswer")

        return ChatTurnPreparationRagWebFallbackResult(
            applied=True,
            direct_answer=fallback_direct or direct_answer,
            tool_context=merged_context,
            tool_calls=merged_tool_calls,
            sources=merged_sources,
        )
