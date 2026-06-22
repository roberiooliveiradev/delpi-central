"""Respostas diretas compostas para perguntas meta improvisadas (perfil + capacidades + assistente)."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

from app.application.services.chat_assistant_identity_service import (
    ChatAssistantIdentityService,
)
from app.application.services.chat_capabilities_service import ChatCapabilitiesService
from app.domain.services.chat_user_profile_intent_service import (
    ChatUserProfileIntentService,
)


@dataclass(frozen=True)
class MetaDirectAnswerIntents:
    user_profile: bool
    capabilities: bool
    assistant_identity: bool

    @property
    def count(self) -> int:
        return sum(
            (
                self.user_profile,
                self.capabilities,
                self.assistant_identity,
            )
        )


class ChatMetaDirectAnswerService:
    @classmethod
    def detect_intents(cls, message: str) -> MetaDirectAnswerIntents:
        return MetaDirectAnswerIntents(
            user_profile=ChatUserProfileIntentService.is_user_identity_question(message),
            capabilities=ChatCapabilitiesService.is_capability_inquiry(message),
            assistant_identity=ChatAssistantIdentityService.classify(message) is not None,
        )

    @classmethod
    def build(
        cls,
        *,
        message: str,
        workspace_context: dict,
        resolve_user_identity_answer: Callable[[str], str | None],
        resolve_capabilities_answer: Callable[[str], str | None],
    ) -> str | None:
        intents = cls.detect_intents(message)
        sections: list[tuple[str, str]] = []

        if intents.user_profile:
            user_answer = resolve_user_identity_answer(message)

            if user_answer:
                sections.append(
                    (
                        "Seu perfil na Minha DELPI",
                        cls._strip_section_heading(user_answer),
                    )
                )

        if intents.capabilities:
            capabilities_answer = resolve_capabilities_answer(message)

            if capabilities_answer:
                sections.append(
                    (
                        "O que você pode fazer aqui",
                        cls._strip_section_heading(capabilities_answer),
                    )
                )

        if intents.assistant_identity:
            assistant_answer = ChatAssistantIdentityService.build_direct_answer(
                message=message,
                workspace_context=workspace_context,
            )

            if assistant_answer:
                sections.append(
                    (
                        "Sobre o assistente",
                        cls._strip_section_heading(assistant_answer),
                    )
                )

        if not sections:
            return None

        if len(sections) == 1:
            title, body = sections[0]
            return f"**{title}**\n\n{body}".strip()

        parts: list[str] = []

        if intents.count >= 2:
            parts.append(
                "Organizei sua pergunta em partes para ficar mais fácil de ler:"
            )
            parts.append("")

        for title, body in sections:
            parts.append(f"## {title}")
            parts.append("")
            parts.append(body.strip())

        return "\n".join(parts).strip()

    @classmethod
    def _strip_section_heading(cls, text: str) -> str:
        normalized = str(text or "").strip()
        normalized = re.sub(
            r"^\*\*[^*]+\*\*\s*\n+",
            "",
            normalized,
            count=1,
        )
        return normalized.strip()
