"""Vocabulário declarativo da entrega de síntese LLM — bundle ``llm_synthesis_delivery``."""

from __future__ import annotations

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "llm_synthesis_delivery"


class ChatLlmSynthesisDeliveryContentService:
    @classmethod
    def compound_user_message_lead(cls) -> str:
        return str(
            ChatAssistantContentService.get(
                _BUNDLE,
                "compoundUserMessageLead",
                default=(
                    "Responda à pergunta em linguagem natural com os blocos de fatos abaixo. "
                    "Use somente dados reais de cada seção — não invente nem use placeholders."
                ),
            )
            or ""
        ).strip()

    @classmethod
    def common_leak_markers(cls) -> tuple[str, ...]:
        return tuple(
            str(item).strip().lower()
            for item in ChatAssistantContentService.list(_BUNDLE, "commonLeakMarkers")
            if str(item).strip()
        )

    @classmethod
    def safe_fallback_answer(cls) -> str:
        return str(
            ChatAssistantContentService.get(
                _BUNDLE,
                "safeFallbackAnswer",
                default=(
                    "Não consegui formular a resposta de forma clara. "
                    "Pode reformular a pergunta em uma frase?"
                ),
            )
            or ""
        ).strip()
