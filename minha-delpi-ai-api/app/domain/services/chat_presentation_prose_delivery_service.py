"""Gate canônico — escolha e aplicação de prosa template vs LLM vs direct."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_operational_narrative_synthesis_service import (
    ChatOperationalNarrativeSynthesisService,
)
from app.domain.services.chat_presentation_prose_delivery_content_service import (
    ChatPresentationProseDeliveryContentService,
)
from app.domain.services.chat_response_mode_service import ChatResponseModeService

MODE_TEMPLATE = "template"
MODE_LLM = "llm"
MODE_DIRECT = "direct"


class ChatPresentationProseDeliveryService:
    @classmethod
    def resolve_mode(
        cls,
        message: str | None,
        tool_calls: list | None,
        *,
        response_mode: str | None = None,
    ) -> str:
        del response_mode

        if cls._qualifies_llm_prose(message, tool_calls):
            return MODE_LLM

        if cls._qualifies_direct_prose(message, tool_calls):
            return MODE_DIRECT

        return MODE_TEMPLATE

    @classmethod
    def apply_turn(
        cls,
        message: str | None,
        tool_calls: list | None,
        *,
        response_mode: str | None = None,
    ) -> str:
        mode = cls.resolve_mode(message, tool_calls, response_mode=response_mode)

        if not isinstance(tool_calls, list):
            return mode

        if mode == MODE_LLM:
            from app.domain.services.chat_presentation_llm_prose_decoupling_service import (
                ChatPresentationLlmProseDecouplingService,
            )

            ChatPresentationLlmProseDecouplingService.apply_to_tool_calls(
                tool_calls,
                message=message,
            )

        cls._stamp_delivery_mode(tool_calls, mode)
        return mode

    @classmethod
    def should_use_llm_prose(
        cls,
        message: str | None,
        tool_calls: list | None,
        *,
        response_mode: str | None = None,
    ) -> bool:
        return (
            cls.resolve_mode(message, tool_calls, response_mode=response_mode) == MODE_LLM
        )

    @classmethod
    def should_use_template_prose(
        cls,
        message: str | None,
        tool_calls: list | None,
        *,
        response_mode: str | None = None,
    ) -> bool:
        return (
            cls.resolve_mode(message, tool_calls, response_mode=response_mode)
            == MODE_TEMPLATE
        )

    @classmethod
    def is_llm_decoupled_metadata(cls, metadata: dict[str, Any] | None) -> bool:
        if not isinstance(metadata, dict):
            return False

        if metadata.get("llmProseDecoupled"):
            return True

        decision = metadata.get("presentationDecision")

        if isinstance(decision, dict):
            prose_source = str(decision.get("proseSource") or "").strip().lower()

            if prose_source == MODE_LLM:
                return True

        return str(metadata.get("proseDeliveryMode") or "").strip().lower() == MODE_LLM

    @classmethod
    def _qualifies_llm_prose(
        cls,
        message: str | None,
        tool_calls: list | None,
    ) -> bool:
        if not ChatOperationalNarrativeSynthesisService.should_force_llm_synthesis(
            message,
            tool_calls,
        ):
            return False

        if ChatPresentationProseDeliveryContentService.require_response_modes_for_llm_prose():
            return ChatResponseModeService.is_enabled()

        return True

    @classmethod
    def _qualifies_direct_prose(
        cls,
        message: str | None,
        tool_calls: list | None,
    ) -> bool:
        if not isinstance(tool_calls, list):
            return False

        if ChatOperationalNarrativeSynthesisService.should_force_llm_synthesis(
            message,
            tool_calls,
        ):
            return False

        from app.domain.services.chat_message_normalization_service import (
            ChatMessageNormalizationService,
        )
        from app.domain.services.chat_operational_narrative_synthesis_content_service import (
            ChatOperationalNarrativeSynthesisContentService,
        )

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if not any(
            term in normalized
            for term in ChatOperationalNarrativeSynthesisContentService.factual_narrow_terms()
        ):
            return False

        if any(
            marker in normalized
            for marker in ChatOperationalNarrativeSynthesisContentService.narrative_markers()
        ):
            return False

        for tool_call in tool_calls:
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if isinstance(metadata, dict) and metadata.get("ok"):
                return True

        return False

    @classmethod
    def _stamp_delivery_mode(cls, tool_calls: list, mode: str) -> None:
        key = ChatPresentationProseDeliveryContentService.metadata_key("deliveryMode")

        for tool_call in tool_calls:
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict) or not metadata.get("ok"):
                continue

            metadata[key] = mode
