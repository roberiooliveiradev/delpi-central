"""Síntese LLM composta para perguntas meta (perfil, capacidades, assistente)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.services.chat_assistant_identity_content_service import (
    ChatAssistantIdentityContentService,
)
from app.domain.services.chat_capabilities_content_service import (
    ChatCapabilitiesContentService,
)
from app.domain.services.chat_user_profile_content_service import (
    ChatUserProfileContentService,
)
from app.domain.services.chat_user_profile_llm_synthesis_service import (
    ChatUserProfileLlmSynthesisService,
)

TOOL_CONTEXT_META_LLM_SYNTHESIS = "metaLlmSynthesis"
TOOL_CONTEXT_META_SYNTHESIS_FACTS = "metaSynthesisFacts"
TOOL_CONTEXT_META_SYNTHESIS_SECTIONS = "metaSynthesisSections"
PIPELINE_STAGE_META_LLM_SYNTHESIS = "meta_llm_synthesis"

SECTION_PROFILE = "profile"
SECTION_CAPABILITIES = "capabilities"
SECTION_ASSISTANT = "assistant"


@dataclass(frozen=True)
class MetaLlmSynthesisSection:
    section_id: str
    title: str
    facts: str

    def as_dict(self) -> dict[str, str]:
        return {
            "sectionId": self.section_id,
            "title": self.title,
            "facts": self.facts,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> MetaLlmSynthesisSection | None:
        if not isinstance(payload, dict):
            return None

        section_id = str(payload.get("sectionId") or "").strip()
        facts = str(payload.get("facts") or "").strip()

        if not section_id or not facts:
            return None

        title = str(payload.get("title") or "").strip()

        return cls(section_id=section_id, title=title, facts=facts)


class ChatMetaLlmSynthesisService:
    TOOL_CONTEXT_META_LLM_SYNTHESIS = TOOL_CONTEXT_META_LLM_SYNTHESIS
    TOOL_CONTEXT_META_SYNTHESIS_FACTS = TOOL_CONTEXT_META_SYNTHESIS_FACTS
    TOOL_CONTEXT_META_SYNTHESIS_SECTIONS = TOOL_CONTEXT_META_SYNTHESIS_SECTIONS
    PIPELINE_STAGE_META_LLM_SYNTHESIS = PIPELINE_STAGE_META_LLM_SYNTHESIS

    @classmethod
    def section_title(cls, section_id: str, *, compound: bool) -> str:
        if section_id == SECTION_PROFILE:
            return "Seu perfil na Minha DELPI"

        if section_id == SECTION_CAPABILITIES:
            if compound:
                return ChatCapabilitiesContentService.llm_synthesis_compound_section_title()
            return ChatCapabilitiesContentService.llm_synthesis_facts_section_title()

        if section_id == SECTION_ASSISTANT:
            if compound:
                return ChatAssistantIdentityContentService.llm_synthesis_compound_section_title()
            return ChatAssistantIdentityContentService.llm_synthesis_facts_section_title()

        return section_id

    @classmethod
    def compose_facts_block(cls, sections: list[MetaLlmSynthesisSection]) -> str:
        if not sections:
            return ""

        compound = len(sections) >= 2
        parts: list[str] = []

        for section in sections:
            facts = str(section.facts or "").strip()

            if not facts:
                continue

            if compound:
                parts.append(f"## {section.title}")
                parts.append("")
                parts.append(facts)
                parts.append("")
            else:
                parts.append(facts)

        return "\n".join(parts).strip()

    @classmethod
    def compose_user_message_lead(cls, sections: list[MetaLlmSynthesisSection]) -> str:
        if len(sections) == 1:
            section = sections[0]

            if section.section_id == SECTION_PROFILE:
                lead = ChatUserProfileContentService.llm_synthesis_user_message_lead()
            elif section.section_id == SECTION_CAPABILITIES:
                lead = ChatCapabilitiesContentService.llm_synthesis_user_message_lead()
            else:
                lead = ChatAssistantIdentityContentService.llm_synthesis_user_message_lead()

            if lead:
                return lead

        return (
            "Responda à pergunta em linguagem natural com os blocos de fatos abaixo. "
            "Use somente dados reais de cada seção — não invente nem use placeholders."
        )

    @classmethod
    def compose_question_prefix(cls, sections: list[MetaLlmSynthesisSection]) -> str:
        if len(sections) == 1:
            section = sections[0]

            if section.section_id == SECTION_PROFILE:
                return ChatUserProfileContentService.llm_synthesis_question_prefix()

            if section.section_id == SECTION_CAPABILITIES:
                return ChatCapabilitiesContentService.llm_synthesis_question_prefix()

            return ChatAssistantIdentityContentService.llm_synthesis_question_prefix()

        return "Pergunta:"

    @classmethod
    def compose_user_message(
        cls,
        *,
        sections: list[MetaLlmSynthesisSection],
        question: str | None,
    ) -> str:
        facts_block = cls.compose_facts_block(sections)
        prompt = str(question or "").strip()

        if not facts_block:
            return prompt

        lead = cls.compose_user_message_lead(sections)
        prefix = cls.compose_question_prefix(sections)

        return f"{lead}\n\n{facts_block}\n\n{prefix} {prompt}".strip()

    @classmethod
    def enrich_tool_context(
        cls,
        tool_context: dict[str, Any] | None,
        *,
        sections: list[MetaLlmSynthesisSection],
    ) -> dict[str, Any]:
        context = dict(tool_context) if isinstance(tool_context, dict) else {}
        facts = cls.compose_facts_block(sections)

        if not facts:
            return context

        context[TOOL_CONTEXT_META_LLM_SYNTHESIS] = True
        context[TOOL_CONTEXT_META_SYNTHESIS_FACTS] = facts
        context[TOOL_CONTEXT_META_SYNTHESIS_SECTIONS] = [
            section.as_dict() for section in sections
        ]

        for section in sections:
            if section.section_id == SECTION_PROFILE:
                context = ChatUserProfileLlmSynthesisService.enrich_tool_context(
                    context,
                    profile_facts=section.facts,
                )
                break

        return context

    @classmethod
    def extract_sections(cls, tool_context: dict[str, Any] | None) -> list[MetaLlmSynthesisSection]:
        if not isinstance(tool_context, dict):
            return []

        raw_sections = tool_context.get(TOOL_CONTEXT_META_SYNTHESIS_SECTIONS)

        if not isinstance(raw_sections, list):
            return []

        sections: list[MetaLlmSynthesisSection] = []

        for item in raw_sections:
            section = MetaLlmSynthesisSection.from_dict(item)

            if section:
                sections.append(section)

        return sections

    @classmethod
    def extract_synthesis_facts(cls, tool_context: dict[str, Any] | None) -> str | None:
        if not isinstance(tool_context, dict):
            return None

        meta_facts = str(tool_context.get(TOOL_CONTEXT_META_SYNTHESIS_FACTS) or "").strip()

        if meta_facts:
            return meta_facts

        return ChatUserProfileLlmSynthesisService.extract_synthesis_facts(tool_context)

    @classmethod
    def append_pipeline_stage(cls, pipeline_stages: list[str]) -> None:
        if PIPELINE_STAGE_META_LLM_SYNTHESIS not in pipeline_stages:
            pipeline_stages.append(PIPELINE_STAGE_META_LLM_SYNTHESIS)

    @classmethod
    def resolve_user_message_content(
        cls,
        *,
        message: str,
        synthesis_facts: str | None,
        tool_context: dict[str, Any] | None = None,
    ) -> str:
        sections = cls.extract_sections(tool_context)

        if sections:
            return cls.compose_user_message(sections=sections, question=message)

        facts = str(synthesis_facts or "").strip()

        if not facts:
            return message

        return ChatUserProfileLlmSynthesisService.resolve_user_message_content(
            message=message,
            profile_synthesis_facts=facts,
        )
