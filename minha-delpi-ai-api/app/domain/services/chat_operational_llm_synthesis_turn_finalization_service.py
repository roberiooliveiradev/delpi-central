"""Finalização canônica da prosa LLM operacional — enrichment, coerência e fallback."""

from __future__ import annotations

from app.domain.services.chat_operational_llm_synthesis_answer_enrichment_service import (
    ChatOperationalLlmSynthesisAnswerEnrichmentService,
)
from app.domain.services.chat_operational_llm_synthesis_brief_direct_service import (
    ChatOperationalLlmSynthesisBriefDirectService,
)
from app.domain.services.chat_presentation_prose_delivery_service import (
    ChatPresentationProseDeliveryService,
)
from app.domain.services.chat_response_mode_service import ChatResponseModeService
from app.domain.services.chat_response_mode_synthesis_quality_service import (
    ChatResponseModeSynthesisQualityService,
)


class ChatOperationalLlmSynthesisTurnFinalizationService:
    @classmethod
    def finalize_persisted_answer(
        cls,
        answer: str | None,
        tool_calls: list | None,
        *,
        message: str | None = None,
        response_mode: str | None = None,
        response_mode_effect: str | None = None,
    ) -> str:
        normalized_mode = ChatResponseModeService.normalize(response_mode)
        effect = str(response_mode_effect or "").strip()
        compact = effect == "llm_synthesis_brief"

        body = ChatPresentationProseDeliveryService.resolve_llm_synthesis_answer_fallback(
            answer,
            tool_calls,
            compact=compact,
        )

        body = cls._enrich(
            body,
            message=message,
            tool_calls=tool_calls,
            response_mode=normalized_mode,
            response_mode_effect=effect,
        )

        gaps = ChatResponseModeSynthesisQualityService.evaluate_synthesis_coherence(
            mode=normalized_mode,
            question=str(message or ""),
            content=body,
            tool_calls=tool_calls if isinstance(tool_calls, list) else [],
        )

        if gaps:
            fallback = ChatOperationalLlmSynthesisBriefDirectService.try_build_quality_fallback(
                message,
                tool_calls,
                response_mode=normalized_mode,
            )

            if fallback:
                body = cls._enrich(
                    fallback,
                    message=message,
                    tool_calls=tool_calls,
                    response_mode=normalized_mode,
                    response_mode_effect=effect,
                )

        return ChatPresentationProseDeliveryService.ensure_product_code_in_synthesis_prose(
            body,
            message,
            tool_calls,
        ).strip()

    @classmethod
    def _enrich(
        cls,
        body: str,
        *,
        message: str | None,
        tool_calls: list | None,
        response_mode: str,
        response_mode_effect: str,
    ) -> str:
        effect = response_mode_effect

        if not effect:
            effect = ChatResponseModeService.resolve_synthesis_effect(response_mode)

        return ChatOperationalLlmSynthesisAnswerEnrichmentService.finalize_answer(
            body,
            message=message,
            tool_calls=tool_calls,
            response_mode_effect=effect,
            response_mode=response_mode,
        )
