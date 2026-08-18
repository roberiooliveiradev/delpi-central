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
TOOL_CONTEXT_TEMPLATE_FALLBACK = "userProfileTemplateFallback"
PIPELINE_STAGE_IDENTITY_LLM_SYNTHESIS = "identity_llm_synthesis"
POLICY_NAME = "chat-user-profile.md"


class ChatUserProfileLlmSynthesisService:
    TOOL_CONTEXT_SYNTHESIS_FLAG = TOOL_CONTEXT_SYNTHESIS_FLAG
    TOOL_CONTEXT_SYNTHESIS_FACTS = TOOL_CONTEXT_SYNTHESIS_FACTS
    TOOL_CONTEXT_TEMPLATE_FALLBACK = TOOL_CONTEXT_TEMPLATE_FALLBACK
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
    def parse_profile_resolver_payload(cls, raw: Any) -> tuple[str, str | None]:
        if isinstance(raw, dict):
            facts = str(raw.get("facts") or "").strip()
            template = str(raw.get("template") or "").strip() or None
            return facts, template
        return str(raw or "").strip(), None

    @classmethod
    def template_or_facts(cls, raw: Any) -> str | None:
        facts, template = cls.parse_profile_resolver_payload(raw)
        text = (template or facts or "").strip()
        return text or None

    @classmethod
    def extract_fact_field(cls, facts: str | None, field: str) -> str:
        needle = f"**{field}:**"
        for line in str(facts or "").splitlines():
            stripped = line.strip()
            if needle.lower() in stripped.lower():
                return stripped[stripped.lower().find(needle.lower()) + len(needle) :].strip()
        return ""

    @classmethod
    def answer_needs_fallback(cls, *, answer: str, synthesis_facts: str | None) -> bool:
        facts = str(synthesis_facts or "").strip()
        text = str(answer or "").strip()

        if not facts:
            return False

        lowered = text.lower()
        for marker in ChatUserProfileContentService.placeholder_markers():
            if marker and marker in lowered:
                return True

        for marker in ChatUserProfileContentService.leak_markers():
            if marker and marker in lowered:
                return True

        facts_title = facts.splitlines()[0].strip().lower() if facts else ""
        if facts_title and len(facts_title) >= 8 and facts_title in lowered:
            return True

        name = cls.extract_fact_field(facts, "Nome")
        if name:
            name_lower = name.lower()
            first = name_lower.split()[0] if name_lower.split() else ""
            if name_lower not in lowered and first not in lowered:
                return True

        return False

    @classmethod
    def guard_answer(
        cls,
        *,
        answer: str,
        synthesis_facts: str | None,
        fallback: str | None,
    ) -> str:
        if not cls.answer_needs_fallback(answer=answer, synthesis_facts=synthesis_facts):
            return str(answer or "").strip()

        recovery = str(fallback or "").strip()
        if recovery:
            return recovery
        return str(synthesis_facts or "").strip() or str(answer or "").strip()

    @classmethod
    def enrich_tool_context(
        cls,
        tool_context: dict[str, Any] | None,
        *,
        profile_facts: str | None,
        template_fallback: str | None = None,
    ) -> dict[str, Any]:
        context = dict(tool_context) if isinstance(tool_context, dict) else {}
        context[TOOL_CONTEXT_SYNTHESIS_FLAG] = True

        facts = str(profile_facts or "").strip()

        if facts:
            context[TOOL_CONTEXT_SYNTHESIS_FACTS] = facts

        template = str(template_fallback or "").strip()
        if template:
            context[TOOL_CONTEXT_TEMPLATE_FALLBACK] = template

        return context

    @classmethod
    def extract_template_fallback(cls, tool_context: dict[str, Any] | None) -> str | None:
        if not isinstance(tool_context, dict):
            return None

        template = str(tool_context.get(TOOL_CONTEXT_TEMPLATE_FALLBACK) or "").strip()
        return template or None

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
