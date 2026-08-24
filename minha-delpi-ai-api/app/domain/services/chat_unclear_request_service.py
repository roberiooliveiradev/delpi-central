"""Fallback honesto para pedidos não entendidos (Playbook de Inteligência, seções 11 e 28).

Regra central: quando a mensagem é vaga e sem referente claro, o chat deve **dizer que não
entendeu** e pedir esclarecimento — sem inventar intenção nem chamar ferramentas.

Para evitar falsos positivos, só ativa em mensagens **curtas** que sejam essencialmente o
gatilho vago (ex.: "faz isso", "arruma", "isso") e que não contenham termos operacionais,
de texto, anexo, lousa ou web (esses são tratados pelos roteadores específicos).
"""

from __future__ import annotations

import re
from functools import lru_cache

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_turn_grounding_service import ChatTurnGroundingStatus


@lru_cache(maxsize=1)
def _content() -> dict:
    return ChatAssistantContentService.load_bundle("unclear_requests")


class ChatUnclearRequestService:
    """Classifica pedidos vagos e devolve uma resposta de esclarecimento."""

    @classmethod
    def is_unclear_request(
        cls,
        message: str,
        *,
        previous_messages: list | None = None,
        grounding_status: str | None = None,
    ) -> bool:
        return (
            cls.classify(
                message,
                previous_messages=previous_messages,
                grounding_status=grounding_status,
            )
            is not None
        )

    @classmethod
    def classify(
        cls,
        message: str,
        *,
        previous_messages: list | None = None,
        grounding_status: str | None = None,
    ) -> str | None:
        if cls._is_grounded_status(grounding_status):
            return None

        if cls._has_recent_assistant_tool_success(previous_messages):
            return None

        text = str(message or "").strip()

        if not text:
            return None

        content = _content()
        max_length = int(content.get("maxMessageLength") or 40)

        if len(text) > max_length:
            return None

        normalized = ChatMessageNormalizationService.normalize_for_matching(text) or ""
        normalized = " ".join(normalized.split())

        if not normalized:
            return None

        disqualifiers = tuple(str(item) for item in (content.get("disqualifiers") or ()))

        if ChatMessageNormalizationService.contains_any(normalized, disqualifiers):
            return None

        patterns = content.get("patterns") or {}
        priority = content.get("categoryPriority") or list(patterns.keys())

        for category in priority:
            for pattern in patterns.get(category) or ():
                if cls._matches(normalized, str(pattern)):
                    return str(category)

        return None

    @classmethod
    def build_direct_answer(
        cls,
        *,
        message: str,
        previous_messages: list | None = None,
        with_options: bool = False,
        grounding_status: str | None = None,
    ) -> str | None:
        category = cls.classify(
            message,
            previous_messages=previous_messages,
            grounding_status=grounding_status,
        )

        if not category:
            return None

        responses = _content().get("responses") or {}

        if with_options:
            options = str(responses.get("withOptions") or "").strip()

            if options:
                return options

        answer = str(responses.get(category) or "").strip()

        if answer:
            return answer

        return str(responses.get("default") or "").strip() or None

    @classmethod
    def build_suggestions(
        cls,
        *,
        message: str,
        previous_messages: list | None = None,
    ) -> list[dict[str, str]]:
        category = cls.classify(message, previous_messages=previous_messages)

        if not category:
            return []

        by_category = _content().get("suggestionsByCategory") or {}
        raw = by_category.get(category)

        if not isinstance(raw, list):
            return []

        suggestions: list[dict[str, str]] = []

        for item in raw:
            if not isinstance(item, dict):
                continue

            label = str(item.get("label") or "").strip()
            query = str(item.get("query") or "").strip()

            if label and query:
                suggestions.append({"label": label, "query": query})

        return suggestions

    @classmethod
    def _matches(cls, normalized: str, pattern: str) -> bool:
        candidate = ChatMessageNormalizationService.normalize_for_matching(pattern) or pattern
        candidate = " ".join(candidate.split())

        if not candidate:
            return False

        if normalized == candidate:
            return True

        trailing = re.sub(r"[\s!?.,:;]+$", "", normalized)

        return trailing == candidate

    @classmethod
    def _is_grounded_status(cls, grounding_status: str | None) -> bool:
        status = str(grounding_status or "").strip().lower()

        return status == ChatTurnGroundingStatus.GROUNDED.value

    @classmethod
    def _has_recent_assistant_tool_success(cls, previous_messages: list | None) -> bool:
        for item in reversed(previous_messages or []):
            role = str(
                getattr(item, "role", None) or (item.get("role") if isinstance(item, dict) else "")
            ).strip()

            if role != "assistant":
                continue

            metadata = getattr(item, "metadata", None)

            if metadata is None and isinstance(item, dict):
                metadata = item.get("metadata")

            if not isinstance(metadata, dict):
                return False

            for tool_call in metadata.get("toolCalls") or []:
                if not isinstance(tool_call, dict):
                    continue

                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                tool_meta = tool_call.get("metadata")

                if isinstance(tool_meta, dict) and tool_meta.get("ok"):
                    return True

            return False

        return False
