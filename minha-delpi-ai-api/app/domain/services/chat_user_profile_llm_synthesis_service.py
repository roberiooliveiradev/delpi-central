"""Entrega de síntese LLM para perfil do usuário — fatos no prompt, prosa no modelo."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_user_profile_content_service import (
    ChatUserProfileContentService,
)
from app.domain.services.chat_user_profile_intent_service import (
    ChatUserProfileIntentService,
)

TOOL_CONTEXT_SYNTHESIS_FLAG = "userProfileLlmSynthesis"
TOOL_CONTEXT_SYNTHESIS_FACTS = "userProfileSynthesisFacts"
PIPELINE_STAGE_IDENTITY_LLM_SYNTHESIS = "identity_llm_synthesis"
POLICY_NAME = "chat-user-profile.md"


class ChatUserProfileLlmSynthesisService:
    TOOL_CONTEXT_SYNTHESIS_FLAG = TOOL_CONTEXT_SYNTHESIS_FLAG
    TOOL_CONTEXT_SYNTHESIS_FACTS = TOOL_CONTEXT_SYNTHESIS_FACTS
    PIPELINE_STAGE_IDENTITY_LLM_SYNTHESIS = PIPELINE_STAGE_IDENTITY_LLM_SYNTHESIS
    POLICY_NAME = POLICY_NAME

    @classmethod
    def should_route_to_llm(cls, message: str | None) -> bool:
        return ChatUserProfileIntentService.is_user_identity_question(message)

    @classmethod
    def should_skip_meta_direct_answer(cls, *, user_profile_intent: bool) -> bool:
        return user_profile_intent

    @classmethod
    def is_compound_profile_question(
        cls,
        message: str | None,
        *,
        meta_intent_count: int,
    ) -> bool:
        if not cls.should_route_to_llm(message):
            return False

        return meta_intent_count >= 2

    @classmethod
    def compose_user_message(
        cls,
        *,
        profile_facts: str | None,
        question: str | None,
    ) -> str:
        facts = str(profile_facts or "").strip()
        prompt = str(question or "").strip()

        if not facts:
            return prompt

        lead = ChatUserProfileContentService.llm_synthesis_user_message_lead()

        if not lead:
            lead = (
                "Responda em linguagem natural com os dados reais do perfil abaixo "
                "(nunca use placeholders como [nome] ou [email]):"
            )

        prefix = ChatUserProfileContentService.llm_synthesis_question_prefix() or "Pergunta:"

        return f"{lead}\n\n{facts}\n\n{prefix} {prompt}".strip()

    @classmethod
    def enrich_tool_context(
        cls,
        tool_context: dict[str, Any] | None,
        *,
        profile_facts: str | None,
    ) -> dict[str, Any]:
        context = dict(tool_context) if isinstance(tool_context, dict) else {}
        context[TOOL_CONTEXT_SYNTHESIS_FLAG] = True

        facts = str(profile_facts or "").strip()

        if facts:
            context[TOOL_CONTEXT_SYNTHESIS_FACTS] = facts

        return context

    @classmethod
    def extract_synthesis_facts(cls, tool_context: dict[str, Any] | None) -> str | None:
        if not isinstance(tool_context, dict):
            return None

        facts = str(tool_context.get(TOOL_CONTEXT_SYNTHESIS_FACTS) or "").strip()

        return facts or None

    @classmethod
    def append_pipeline_stage(cls, pipeline_stages: list[str]) -> None:
        if PIPELINE_STAGE_IDENTITY_LLM_SYNTHESIS not in pipeline_stages:
            pipeline_stages.append(PIPELINE_STAGE_IDENTITY_LLM_SYNTHESIS)

    @classmethod
    def resolve_user_message_content(
        cls,
        *,
        message: str,
        profile_synthesis_facts: str | None,
    ) -> str:
        facts = str(profile_synthesis_facts or "").strip()

        if not facts or not cls.should_route_to_llm(message):
            return message

        return cls.compose_user_message(profile_facts=facts, question=message)
