"""Textos e limites da compactação de histórico — bundle turn_preparation.historySummary."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "turn_preparation"
_PREFIX = ("historySummary",)


class ChatHistorySummaryContentService:
    @classmethod
    def system_prompt(cls) -> str:
        return ChatAssistantContentService.get(
            _BUNDLE,
            *_PREFIX,
            "systemPrompt",
            default=(
                "Você resume conversas anteriores de chat corporativo em português do Brasil. "
                "Preserve fatos, pedidos do usuário, respostas do assistente, números, códigos "
                "e decisões. Não invente informação. Máximo 8 frases objetivas."
            ),
        )

    @classmethod
    def priority_instruction(cls) -> str:
        return ChatAssistantContentService.get(
            _BUNDLE,
            *_PREFIX,
            "priorityInstruction",
            default="",
        )

    @classmethod
    def user_prompt(cls, *, conversation: str) -> str:
        return ChatAssistantContentService.format(
            _BUNDLE,
            *_PREFIX,
            "userPromptTemplate",
            default="Resuma a conversa anterior:\n\n{conversation}",
            conversation=conversation,
        )

    @classmethod
    def user_prompt_with_priority(cls, *, conversation: str, priority_facts: str) -> str:
        return ChatAssistantContentService.format(
            _BUNDLE,
            *_PREFIX,
            "userPromptWithPriorityTemplate",
            default=(
                "Fatos preservados (prioridade máxima):\n{priorityFacts}\n\n"
                "Resuma a conversa anterior sem omitir esses fatos:\n\n{conversation}"
            ),
            conversation=conversation,
            priorityFacts=priority_facts,
        )

    @classmethod
    def preserved_facts_header(cls) -> str:
        return ChatAssistantContentService.get(
            _BUNDLE,
            *_PREFIX,
            "preservedFactsHeader",
            default="Fatos preservados da memória de trabalho:",
        )

    @classmethod
    def section_label(cls, key: str) -> str:
        return ChatAssistantContentService.get(
            _BUNDLE,
            *_PREFIX,
            "sectionLabels",
            key,
            default=key,
        )

    @classmethod
    def limit_int(cls, key: str, *, default: int) -> int:
        node = ChatAssistantContentService.get_node(_BUNDLE, *_PREFIX, key)

        if node in (None, ""):
            return default

        try:
            return max(1, int(node))
        except (TypeError, ValueError):
            return default

    @classmethod
    def section_labels(cls) -> dict[str, Any]:
        node = ChatAssistantContentService.get_node(_BUNDLE, *_PREFIX, "sectionLabels")

        return node if isinstance(node, dict) else {}
