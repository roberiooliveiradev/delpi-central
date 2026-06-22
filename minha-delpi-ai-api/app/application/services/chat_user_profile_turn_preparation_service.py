"""Orquestração pós-tool para perguntas de perfil do usuário via síntese LLM."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from app.application.services.chat_meta_direct_answer_service import (
    MetaDirectAnswerIntents,
)
from app.application.services.chat_meta_llm_turn_preparation_service import (
    ChatMetaLlmTurnPreparationService,
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
        return ChatMetaLlmTurnPreparationService.detect_meta_intents(message)

    @classmethod
    def apply_identity_llm_route(
        cls,
        *,
        message: str,
        tool_context: dict,
        pipeline_stages: list[str],
        resolve_profile_facts: Callable[[str], str | None],
        meta_intents: MetaDirectAnswerIntents | None = None,
        workspace_context: dict | None = None,
        resolve_capabilities_facts: Callable[[str], str | None] | None = None,
        resolve_assistant_identity_facts: Callable[[str], str | None] | None = None,
    ) -> ChatUserProfileTurnPreparationResult:
        meta_result = ChatMetaLlmTurnPreparationService.apply_meta_llm_route(
            message=message,
            workspace_context=workspace_context or {},
            tool_context=tool_context,
            pipeline_stages=pipeline_stages,
            resolve_profile_facts=resolve_profile_facts,
            resolve_capabilities_facts=resolve_capabilities_facts
            or (lambda _message: None),
            resolve_assistant_identity_facts=resolve_assistant_identity_facts
            or (lambda _message: None),
            meta_intents=meta_intents,
        )

        return ChatUserProfileTurnPreparationResult(
            skip_rag=meta_result.skip_rag,
            skip_user_direct_answer=meta_result.skip_user_direct_answer,
            skip_compound_direct_answers=meta_result.skip_isolated_meta_direct_answers,
            skip_meta_direct_answer=meta_result.skip_meta_direct_answer,
            tool_context=meta_result.tool_context,
            pipeline_stages=meta_result.pipeline_stages,
        )
