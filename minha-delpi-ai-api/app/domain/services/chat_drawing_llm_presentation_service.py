"""Apresentação LLM para análise de desenho — hidratação e render-only do checklist."""

from __future__ import annotations

import json
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_conversation_context_service import (
    ChatConversationContextService,
)
from app.domain.services.chat_drawing_intent_service import ChatDrawingIntentService


class ChatDrawingLlmPresentationService:
    _INTENT_BUNDLE = "drawing_query_intent"

    @classmethod
    def last_analysis_from_messages(
        cls,
        previous_messages: list | None,
    ) -> dict[str, Any] | None:
        for item in reversed(previous_messages or []):
            if ChatConversationContextService.message_role(item).lower() != "assistant":
                continue

            metadata = ChatConversationContextService.message_metadata(item)

            if not metadata:
                continue

            drawing = cls._drawing_analysis_from_metadata(metadata)

            if isinstance(drawing, dict) and drawing.get("items"):
                return drawing

        return None

    @classmethod
    def _drawing_analysis_from_metadata(cls, metadata: dict[str, Any]) -> dict[str, Any] | None:
        drawing = metadata.get("drawingAnalysis")

        if isinstance(drawing, dict) and drawing.get("items"):
            return drawing

        intelligence = metadata.get("intelligence")

        if isinstance(intelligence, dict):
            nested = intelligence.get("drawingAnalysis")

            if isinstance(nested, dict) and nested.get("items"):
                return nested

        return None

    @classmethod
    def is_new_analysis_turn(
        cls,
        message: str | None,
        *,
        attachment_ids: list[str] | None = None,
    ) -> bool:
        return ChatDrawingIntentService.is_drawing_analysis_request(
            message,
            attachment_ids=attachment_ids,
        )

    @classmethod
    def should_hydrate_follow_up(
        cls,
        tool_context: dict | None,
        *,
        message: str | None,
        attachment_ids: list[str] | None = None,
        previous_messages: list | None,
    ) -> bool:
        if cls.is_new_analysis_turn(message, attachment_ids=attachment_ids):
            return False

        if isinstance(tool_context, dict) and isinstance(
            tool_context.get("drawingAnalysis"),
            dict,
        ):
            return False

        return cls.last_analysis_from_messages(previous_messages) is not None

    @classmethod
    def hydrate_tool_context(
        cls,
        tool_context: dict | None,
        *,
        message: str | None,
        attachment_ids: list[str] | None = None,
        previous_messages: list | None,
    ) -> dict[str, Any]:
        if not isinstance(tool_context, dict):
            tool_context = {}

        if not cls.should_hydrate_follow_up(
            tool_context,
            message=message,
            attachment_ids=attachment_ids,
            previous_messages=previous_messages,
        ):
            return tool_context

        analysis = cls.last_analysis_from_messages(previous_messages)

        if not analysis:
            return tool_context

        merged = dict(tool_context)
        merged["drawingAnalysisMode"] = True
        merged["drawingAnalysis"] = analysis
        return merged

    @classmethod
    def enrich_context_string(cls, context: str, tool_context: dict | None) -> str:
        if not isinstance(tool_context, dict):
            return str(context or "")

        analysis = tool_context.get("drawingAnalysis")

        if not isinstance(analysis, dict) or not analysis.get("items"):
            return str(context or "")

        payload = {
            "drawingAnalysisMode": True,
            "drawingAnalysis": analysis,
        }
        marker = json.dumps(payload, ensure_ascii=False)
        base = str(context or "").strip()

        if base:
            return f"{base}\n\n{marker}"

        return marker

    @classmethod
    def has_export_markdown(cls, tool_context: dict | None) -> bool:
        if not isinstance(tool_context, dict):
            return False

        export = tool_context.get("drawingAnalysisExport")

        if not isinstance(export, dict):
            return False

        return bool(str(export.get("markdown") or "").strip())

    @classmethod
    def build_llm_policy_addon(
        cls,
        *,
        message: str | None,
        attachment_ids: list[str] | None = None,
        tool_context: dict | None,
        previous_messages: list | None,
    ) -> str:
        if cls.is_new_analysis_turn(message, attachment_ids=attachment_ids):
            return ChatDrawingIntentService.build_llm_fallback_policy_addon(
                message,
                attachment_ids=attachment_ids,
            )

        hydrated = cls.hydrate_tool_context(
            tool_context,
            message=message,
            attachment_ids=attachment_ids,
            previous_messages=previous_messages,
        )

        if not isinstance(hydrated.get("drawingAnalysis"), dict):
            return ""

        if cls.has_export_markdown(hydrated):
            return ""

        policy_file = ChatAssistantContentService.get(
            cls._INTENT_BUNDLE,
            "followUpRenderOnly",
            "policyFile",
            default="drawing-analysis-render-only.md",
        )

        from app.domain.services.prompt_policy_service import PromptPolicyService

        policy_body = PromptPolicyService()._load_policy(str(policy_file))

        if not policy_body:
            return ""

        return policy_body.strip()
