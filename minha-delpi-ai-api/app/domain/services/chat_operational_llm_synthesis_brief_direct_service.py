"""Síntese Rápida/Normal sem segunda passagem LLM — lead a partir de dataCommentary/dataAnswer."""

from __future__ import annotations

from app.domain.services.chat_operational_llm_synthesis_answer_enrichment_service import (
    ChatOperationalLlmSynthesisAnswerEnrichmentService,
)
from app.domain.services.chat_presentation_prose_delivery_service import (
    ChatPresentationProseDeliveryService,
)
from app.domain.services.chat_operational_commentary_lead_content_service import (
    ChatOperationalCommentaryLeadContentService,
)
from app.domain.services.chat_response_mode_content_service import (
    ChatResponseModeContentService,
)
from app.domain.services.chat_response_mode_service import ChatResponseModeService


class ChatOperationalLlmSynthesisBriefDirectService:
    @classmethod
    def _commentary_depth(cls, response_mode: str | None) -> str:
        return ChatOperationalCommentaryLeadContentService.depth_for_mode(response_mode)

    @classmethod
    def build_commentary_lead(
        cls,
        message: str | None,
        tool_calls: list | None,
        *,
        response_mode: str | None = None,
        compact: bool | None = None,
    ) -> str | None:
        if not cls._qualifies(tool_calls):
            return None

        depth = cls._commentary_depth(response_mode)
        use_compact = compact if compact is not None else depth == cls._brief_depth_key()

        body = ChatPresentationProseDeliveryService.resolve_llm_synthesis_answer_fallback(
            "",
            tool_calls,
            compact=use_compact,
            commentary_depth=depth,
        ).strip()

        if not body:
            return None

        effect = ChatOperationalCommentaryLeadContentService.synthesis_effect_for_depth(depth)
        enriched = ChatOperationalLlmSynthesisAnswerEnrichmentService.finalize_answer(
            body,
            message=message,
            tool_calls=tool_calls,
            response_mode_effect=effect,
        ).strip()

        return enriched or None

    @classmethod
    def try_build_quality_fallback(
        cls,
        message: str | None,
        tool_calls: list | None,
        *,
        response_mode: str | None,
    ) -> str | None:
        normalized = ChatResponseModeService.normalize(response_mode)
        lead = cls.build_commentary_lead(
            message,
            tool_calls,
            response_mode=normalized,
        )

        if not lead:
            return None

        min_chars = ChatResponseModeContentService.quality_fallback_min_chars()

        if len(lead) < min_chars:
            return None

        return lead

    @classmethod
    def try_build_direct_answer(
        cls,
        message: str | None,
        tool_calls: list | None,
        *,
        response_mode: str | None,
    ) -> str | None:
        normalized = ChatResponseModeService.normalize(response_mode)
        config = cls._resolve_mode_config(normalized)

        if not config:
            return None

        if not cls._qualifies(tool_calls):
            return None

        compact = normalized == "fast"
        enriched = cls.build_commentary_lead(
            message,
            tool_calls,
            response_mode=normalized,
            compact=compact,
        )

        if not enriched:
            return None

        min_chars = config["min_chars"]

        if len(enriched) < min_chars:
            return None

        return enriched

    @classmethod
    def _resolve_mode_config(cls, normalized_mode: str) -> dict[str, int] | None:
        if normalized_mode == "fast":
            if not ChatResponseModeContentService.fast_commentary_direct_enabled():
                return None

            return {
                "min_chars": ChatResponseModeContentService.fast_commentary_direct_min_chars(),
            }

        if normalized_mode == "normal":
            if not ChatResponseModeContentService.normal_commentary_direct_enabled():
                return None

            return {
                "min_chars": ChatResponseModeContentService.normal_commentary_direct_min_chars(),
            }

        return None

    @classmethod
    def mark_tool_context(cls, tool_context: dict | None) -> None:
        if isinstance(tool_context, dict):
            tool_context[cls._brief_direct_flag()] = True

    @classmethod
    def is_commentary_brief_context(cls, tool_context: dict | None) -> bool:
        return isinstance(tool_context, dict) and bool(
            tool_context.get(cls._brief_direct_flag()),
        )

    @classmethod
    def _brief_direct_flag(cls) -> str:
        return ChatOperationalCommentaryLeadContentService.brief_direct_tool_context_flag()

    @classmethod
    def _brief_depth_key(cls) -> str:
        return ChatOperationalCommentaryLeadContentService.default_brief_depth()

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
