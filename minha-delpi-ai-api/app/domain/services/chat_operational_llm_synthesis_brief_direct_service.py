"""Síntese Rápida sem segunda passagem LLM — lead a partir de dataCommentary/dataAnswer."""

from __future__ import annotations

from app.domain.services.chat_operational_llm_synthesis_answer_enrichment_service import (
    ChatOperationalLlmSynthesisAnswerEnrichmentService,
)
from app.domain.services.chat_presentation_prose_delivery_service import (
    ChatPresentationProseDeliveryService,
)
from app.domain.services.chat_response_mode_content_service import (
    ChatResponseModeContentService,
)
from app.domain.services.chat_response_mode_service import ChatResponseModeService

_COMMENTARY_BRIEF_FLAG = "commentaryBriefDirect"


class ChatOperationalLlmSynthesisBriefDirectService:
    @classmethod
    def try_build_direct_answer(
        cls,
        message: str | None,
        tool_calls: list | None,
        *,
        response_mode: str | None,
    ) -> str | None:
        if ChatResponseModeService.normalize(response_mode) != "fast":
            return None

        if not ChatResponseModeContentService.fast_commentary_direct_enabled():
            return None

        if not cls._qualifies(tool_calls):
            return None

        body = ChatPresentationProseDeliveryService.resolve_llm_synthesis_answer_fallback(
            "",
            tool_calls,
            compact=True,
        )
        enriched = ChatOperationalLlmSynthesisAnswerEnrichmentService.finalize_answer(
            body,
            message=message,
            tool_calls=tool_calls,
            response_mode_effect="llm_synthesis_brief",
        ).strip()
        min_chars = ChatResponseModeContentService.fast_commentary_direct_min_chars()

        if len(enriched) < min_chars:
            return None

        return enriched

    @classmethod
    def mark_tool_context(cls, tool_context: dict | None) -> None:
        if isinstance(tool_context, dict):
            tool_context[_COMMENTARY_BRIEF_FLAG] = True

    @classmethod
    def is_commentary_brief_context(cls, tool_context: dict | None) -> bool:
        return isinstance(tool_context, dict) and bool(tool_context.get(_COMMENTARY_BRIEF_FLAG))

    @classmethod
    def _qualifies(cls, tool_calls: list | None) -> bool:
        if not isinstance(tool_calls, list):
            return False

        for tool_call in tool_calls:
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict) or not metadata.get("ok"):
                continue

            if ChatPresentationProseDeliveryService.is_llm_decoupled_metadata(metadata):
                return True

        return False
