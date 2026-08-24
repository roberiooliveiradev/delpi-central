"""Finalização canônica da prosa LLM operacional — enrichment, coerência e fallback."""

from __future__ import annotations

from app.domain.services.chat_llm_synthesis_delivery_content_service import (
    ChatLlmSynthesisDeliveryContentService,
)
from app.domain.services.chat_operational_llm_synthesis_answer_enrichment_service import (
    ChatOperationalLlmSynthesisAnswerEnrichmentService,
)
from app.domain.services.chat_operational_llm_synthesis_brief_direct_service import (
    ChatOperationalLlmSynthesisBriefDirectService,
)
from app.domain.services.chat_presentation_prose_delivery_service import (
    ChatPresentationProseDeliveryService,
)
from app.domain.services.chat_response_mode_content_service import (
    ChatResponseModeContentService,
)
from app.domain.services.chat_response_mode_service import ChatResponseModeService
from app.domain.services.chat_response_mode_synthesis_quality_content_service import (
    ChatResponseModeSynthesisQualityContentService,
)
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

        if not effect:
            effect = ChatResponseModeService.resolve_synthesis_effect(normalized_mode)

        compact = effect == "llm_synthesis_brief"
        depth = ChatOperationalLlmSynthesisBriefDirectService._commentary_depth(
            normalized_mode,
        )

        raw_answer = str(answer or "").strip()

        if not raw_answer:
            fallback = ChatOperationalLlmSynthesisBriefDirectService.try_build_quality_fallback(
                message,
                tool_calls,
                response_mode=normalized_mode,
            )

            if fallback:
                return cls._finalize_body(
                    fallback,
                    message=message,
                    tool_calls=tool_calls,
                    response_mode=normalized_mode,
                    response_mode_effect=effect,
                )

        if cls._should_try_commentary_before_enrich(normalized_mode, raw_answer, message, tool_calls):
            fallback = ChatOperationalLlmSynthesisBriefDirectService.try_build_quality_fallback(
                message,
                tool_calls,
                response_mode=normalized_mode,
            )

            if fallback:
                return cls._finalize_body(
                    fallback,
                    message=message,
                    tool_calls=tool_calls,
                    response_mode=normalized_mode,
                    response_mode_effect=effect,
                )

        body = ChatPresentationProseDeliveryService.resolve_llm_synthesis_answer_fallback(
            answer,
            tool_calls,
            compact=compact,
            commentary_depth=depth,
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
        min_chars = ChatResponseModeSynthesisQualityContentService.mode_limit_int(
            "minAnswerChars",
            normalized_mode,
            default=72,
        )
        needs_fallback = bool(gaps) or (
            normalized_mode in ChatResponseModeSynthesisQualityContentService.turn_finalization_modes()
            and len(body) < min_chars
        )

        if needs_fallback:
            fallback = ChatOperationalLlmSynthesisBriefDirectService.try_build_quality_fallback(
                message,
                tool_calls,
                response_mode=normalized_mode,
            )

            if fallback:
                body = cls._finalize_body(
                    fallback,
                    message=message,
                    tool_calls=tool_calls,
                    response_mode=normalized_mode,
                    response_mode_effect=effect,
                )

        return cls._substitute_safe_generic_fallback(
            cls._guard_instruction_leak(
                body,
                message=message,
                tool_calls=tool_calls,
                response_mode=normalized_mode,
                response_mode_effect=effect,
            ),
            message=message,
            tool_calls=tool_calls,
            response_mode=normalized_mode,
            response_mode_effect=effect,
        )

    @classmethod
    def _substitute_safe_generic_fallback(
        cls,
        body: str,
        *,
        message: str | None,
        tool_calls: list | None,
        response_mode: str,
        response_mode_effect: str,
    ) -> str:
        if not cls._is_safe_generic_fallback(body) and not cls._contains_safe_generic_fallback(body):
            return body

        recovered = cls._recover_operational_prose(
            message,
            tool_calls,
            response_mode=response_mode,
            response_mode_effect=response_mode_effect,
        )

        if recovered:
            return recovered

        return body

    @classmethod
    def _recover_operational_prose(
        cls,
        message: str | None,
        tool_calls: list | None,
        *,
        response_mode: str,
        response_mode_effect: str,
    ) -> str | None:
        normalized_mode = ChatResponseModeService.normalize(response_mode)
        lead = ChatOperationalLlmSynthesisBriefDirectService.try_build_quality_fallback(
            message,
            tool_calls,
            response_mode=normalized_mode,
        )

        if lead:
            return cls._finalize_body(
                lead,
                message=message,
                tool_calls=tool_calls,
                response_mode=normalized_mode,
                response_mode_effect=response_mode_effect,
            )

        depth = ChatOperationalLlmSynthesisBriefDirectService._commentary_depth(normalized_mode)
        compact = response_mode_effect == "llm_synthesis_brief"
        commentary_lead = ChatPresentationProseDeliveryService.resolve_llm_synthesis_answer_fallback(
            "",
            tool_calls,
            compact=compact,
            commentary_depth=depth,
        ).strip()

        if commentary_lead:
            return cls._finalize_body(
                commentary_lead,
                message=message,
                tool_calls=tool_calls,
                response_mode=normalized_mode,
                response_mode_effect=response_mode_effect,
            )

        humanized_lead = cls._humanized_summary_lead(tool_calls)

        if humanized_lead:
            return cls._finalize_body(
                humanized_lead,
                message=message,
                tool_calls=tool_calls,
                response_mode=normalized_mode,
                response_mode_effect=response_mode_effect,
            )

        return None

    @classmethod
    def _humanized_summary_lead(cls, tool_calls: list | None) -> str:
        from app.domain.services.chat_conversation_context_service import (
            ChatConversationContextService,
        )

        if not isinstance(tool_calls, list):
            return ""

        for tool_call in tool_calls:
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict) or not metadata.get("ok"):
                continue

            summary = ChatConversationContextService._format_humanized_summary(metadata).strip()

            if summary:
                return summary

        return ""

    @classmethod
    def _is_safe_generic_fallback(cls, text: str) -> bool:
        safe = ChatLlmSynthesisDeliveryContentService.safe_fallback_answer()
        stripped = str(text or "").strip()

        return bool(safe) and stripped == safe

    @classmethod
    def _contains_safe_generic_fallback(cls, text: str) -> bool:
        safe = ChatLlmSynthesisDeliveryContentService.safe_fallback_answer()

        return bool(safe) and safe in str(text or "")

    @classmethod
    def _guard_instruction_leak(
        cls,
        body: str,
        *,
        message: str | None,
        tool_calls: list | None,
        response_mode: str,
        response_mode_effect: str,
    ) -> str:
        from app.domain.services.chat_llm_synthesis_leak_guard_service import (
            ChatLlmSynthesisLeakGuardService,
        )
        from app.domain.services.chat_operational_llm_synthesis_context_content_service import (
            ChatOperationalLlmSynthesisContextContentService,
        )

        fallback = cls._recover_operational_prose(
            message,
            tool_calls,
            response_mode=response_mode,
            response_mode_effect=response_mode_effect,
        )

        if not fallback:
            fallback = ChatOperationalLlmSynthesisBriefDirectService.try_build_quality_fallback(
                message,
                tool_calls,
                response_mode=response_mode,
            )

        guarded = ChatLlmSynthesisLeakGuardService.guard_answer(
            answer=body,
            fallback=fallback,
            facts=ChatOperationalLlmSynthesisContextContentService.title(),
            leak_markers=ChatOperationalLlmSynthesisContextContentService.leak_markers(),
        )
        if guarded == str(body or "").strip():
            return body

        if cls._is_safe_generic_fallback(guarded) or cls._contains_safe_generic_fallback(guarded):
            recovered = cls._recover_operational_prose(
                message,
                tool_calls,
                response_mode=response_mode,
                response_mode_effect=response_mode_effect,
            )

            if recovered:
                return recovered

        if guarded == str(fallback or "").strip() and fallback:
            return cls._finalize_body(
                fallback,
                message=message,
                tool_calls=tool_calls,
                response_mode=response_mode,
                response_mode_effect=response_mode_effect,
            )

        return guarded

    @classmethod
    def _should_try_commentary_before_enrich(
        cls,
        response_mode: str,
        raw_answer: str,
        message: str | None,
        tool_calls: list | None,
    ) -> bool:
        if response_mode not in ChatResponseModeSynthesisQualityContentService.turn_finalization_modes():
            return False

        if not ChatResponseModeSynthesisQualityContentService.turn_finalization_prefer_commentary_before_enrich():
            return False

        if not raw_answer:
            return False

        gaps = ChatResponseModeSynthesisQualityService.evaluate_synthesis_coherence(
            mode=response_mode,
            question=str(message or ""),
            content=raw_answer,
            tool_calls=tool_calls if isinstance(tool_calls, list) else [],
        )

        return bool(gaps)

    @classmethod
    def _finalize_body(
        cls,
        body: str,
        *,
        message: str | None,
        tool_calls: list | None,
        response_mode: str,
        response_mode_effect: str,
    ) -> str:
        enriched = cls._enrich(
            body,
            message=message,
            tool_calls=tool_calls,
            response_mode=response_mode,
            response_mode_effect=response_mode_effect,
        )

        min_chars = max(
            ChatResponseModeContentService.quality_fallback_min_chars(),
            ChatResponseModeSynthesisQualityContentService.mode_limit_int(
                "minAnswerChars",
                response_mode,
                default=72,
            ),
        )

        if len(enriched) < min_chars:
            return enriched

        return ChatPresentationProseDeliveryService.ensure_product_code_in_synthesis_prose(
            enriched,
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
        enriched = ChatOperationalLlmSynthesisAnswerEnrichmentService.finalize_answer(
            body,
            message=message,
            tool_calls=tool_calls,
            response_mode_effect=response_mode_effect,
            response_mode=response_mode,
        )

        return ChatPresentationProseDeliveryService.ensure_product_code_in_synthesis_prose(
            enriched,
            message,
            tool_calls,
        ).strip()
