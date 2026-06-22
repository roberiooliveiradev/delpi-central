"""Orquestração pós-tool para perguntas meta via síntese LLM (perfil, capacidades, assistente)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from app.application.services.chat_assistant_identity_service import (
    ChatAssistantIdentityService,
)
from app.application.services.chat_capabilities_service import ChatCapabilitiesService
from app.application.services.chat_meta_direct_answer_service import (
    ChatMetaDirectAnswerService,
    MetaDirectAnswerIntents,
)
from app.domain.services.chat_meta_llm_synthesis_service import (
    ChatMetaLlmSynthesisService,
    MetaLlmSynthesisSection,
    SECTION_ASSISTANT,
    SECTION_CAPABILITIES,
    SECTION_PROFILE,
)
from app.domain.services.chat_user_profile_llm_synthesis_service import (
    ChatUserProfileLlmSynthesisService,
)


@dataclass(frozen=True)
class ChatMetaLlmTurnPreparationResult:
    active: bool
    skip_rag: bool
    skip_user_direct_answer: bool
    skip_meta_direct_answer: bool
    skip_isolated_meta_direct_answers: bool
    tool_context: dict
    pipeline_stages: list[str]


class ChatMetaLlmTurnPreparationService:
    @classmethod
    def detect_meta_intents(cls, message: str) -> MetaDirectAnswerIntents:
        return ChatMetaDirectAnswerService.detect_intents(message)

    @classmethod
    def apply_meta_llm_route(
        cls,
        *,
        message: str,
        workspace_context: dict,
        tool_context: dict,
        pipeline_stages: list[str],
        resolve_profile_facts: Callable[[str], str | None],
        resolve_capabilities_facts: Callable[[str], str | None],
        resolve_assistant_identity_facts: Callable[[str], str | None],
        meta_intents: MetaDirectAnswerIntents | None = None,
    ) -> ChatMetaLlmTurnPreparationResult:
        stages = list(pipeline_stages)
        context = dict(tool_context)
        intents = meta_intents or cls.detect_meta_intents(message)
        sections: list[MetaLlmSynthesisSection] = []
        compound = intents.count >= 2

        if intents.user_profile and ChatUserProfileLlmSynthesisService.should_route_to_llm(
            message
        ):
            profile_facts = str(resolve_profile_facts(message) or "").strip()

            if profile_facts:
                sections.append(
                    MetaLlmSynthesisSection(
                        section_id=SECTION_PROFILE,
                        title=ChatMetaLlmSynthesisService.section_title(
                            SECTION_PROFILE,
                            compound=compound,
                        ),
                        facts=profile_facts,
                    )
                )

        if intents.capabilities and ChatCapabilitiesService.is_capabilities_question(message):
            from app.application.services.chat_workspace_agent_activation_service import (
                ChatWorkspaceAgentActivationService,
            )

            use_capabilities_llm = ChatWorkspaceAgentActivationService.operational_tools_enabled(
                workspace_context,
            )

            if use_capabilities_llm:
                capabilities_facts = str(resolve_capabilities_facts(message) or "").strip()

                if capabilities_facts:
                    sections.append(
                        MetaLlmSynthesisSection(
                            section_id=SECTION_CAPABILITIES,
                            title=ChatMetaLlmSynthesisService.section_title(
                                SECTION_CAPABILITIES,
                                compound=compound,
                            ),
                            facts=capabilities_facts,
                        )
                    )

        if intents.assistant_identity and ChatAssistantIdentityService.is_assistant_identity_question(
            message
        ):
            assistant_facts = str(resolve_assistant_identity_facts(message) or "").strip()

            if assistant_facts:
                sections.append(
                    MetaLlmSynthesisSection(
                        section_id=SECTION_ASSISTANT,
                        title=ChatMetaLlmSynthesisService.section_title(
                            SECTION_ASSISTANT,
                            compound=compound,
                        ),
                        facts=assistant_facts,
                    )
                )

        if not sections:
            return ChatMetaLlmTurnPreparationResult(
                active=False,
                skip_rag=False,
                skip_user_direct_answer=False,
                skip_meta_direct_answer=False,
                skip_isolated_meta_direct_answers=False,
                tool_context=context,
                pipeline_stages=stages,
            )

        context = ChatMetaLlmSynthesisService.enrich_tool_context(context, sections=sections)
        ChatMetaLlmSynthesisService.append_pipeline_stage(stages)

        if any(section.section_id == SECTION_PROFILE for section in sections):
            ChatUserProfileLlmSynthesisService.append_pipeline_stage(stages)

        return ChatMetaLlmTurnPreparationResult(
            active=True,
            skip_rag=True,
            skip_user_direct_answer=any(
                section.section_id == SECTION_PROFILE for section in sections
            ),
            skip_meta_direct_answer=True,
            skip_isolated_meta_direct_answers=True,
            tool_context=context,
            pipeline_stages=stages,
        )
