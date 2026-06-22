"""Orquestração pós-tool para perguntas de perfil do usuário via síntese LLM."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from app.application.services.chat_meta_direct_answer_service import (
    ChatMetaDirectAnswerService,
    MetaDirectAnswerIntents,
)
from app.domain.services.chat_user_profile_llm_synthesis_service import (
    ChatUserProfileLlmSynthesisService,
)


@dataclass(frozen=True)
class ChatUserProfileTurnPreparationResult:
    skip_rag: bool
    skip_user_direct_answer: bool
    skip_compound_direct_answers: bool
    skip_meta_direct_answer: bool
    tool_context: dict
    pipeline_stages: list[str]


class ChatUserProfileTurnPreparationService:
    @classmethod
    def detect_meta_intents(cls, message: str) -> MetaDirectAnswerIntents:
        return ChatMetaDirectAnswerService.detect_intents(message)

    @classmethod
    def apply_identity_llm_route(
        cls,
        *,
        message: str,
        tool_context: dict,
        pipeline_stages: list[str],
        resolve_profile_facts: Callable[[str], str | None],
        meta_intents: MetaDirectAnswerIntents | None = None,
    ) -> ChatUserProfileTurnPreparationResult:
        stages = list(pipeline_stages)
        context = dict(tool_context)

        if not ChatUserProfileLlmSynthesisService.should_route_to_llm(message):
            return ChatUserProfileTurnPreparationResult(
                skip_rag=False,
                skip_user_direct_answer=False,
                skip_compound_direct_answers=False,
                skip_meta_direct_answer=False,
                tool_context=context,
                pipeline_stages=stages,
            )

        intents = meta_intents or cls.detect_meta_intents(message)
        profile_facts = resolve_profile_facts(message)
        context = ChatUserProfileLlmSynthesisService.enrich_tool_context(
            context,
            profile_facts=profile_facts,
        )
        ChatUserProfileLlmSynthesisService.append_pipeline_stage(stages)

        return ChatUserProfileTurnPreparationResult(
            skip_rag=True,
            skip_user_direct_answer=True,
            skip_compound_direct_answers=ChatUserProfileLlmSynthesisService.is_compound_profile_question(
                message,
                meta_intent_count=intents.count,
            ),
            skip_meta_direct_answer=ChatUserProfileLlmSynthesisService.should_skip_meta_direct_answer(
                user_profile_intent=intents.user_profile,
            ),
            tool_context=context,
            pipeline_stages=stages,
        )
