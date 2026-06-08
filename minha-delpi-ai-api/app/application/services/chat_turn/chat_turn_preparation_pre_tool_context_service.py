"""Direct-answers iniciais e memória pré-tool — Fase 3C lote 22."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.application.services.chat_turn.chat_turn_preparation_direct_answer_service import (
    ChatTurnPreparationDirectAnswerService,
)
from app.application.services.chat_turn.chat_turn_preparation_memory_context_service import (
    ChatTurnPreparationMemoryContextService,
)


@dataclass(frozen=True)
class ChatTurnPreparationPreToolContextResult:
    workspace_context: dict
    working_memory_snapshot: dict
    conversation_context: str
    canvas_action: Any
    fast_path: bool
    pre_capability_answer: str | None
    small_talk_direct: str | None
    utility_direct: str | None
    unclear_direct: str | None
    web_save_sources_direct: str | None
    web_post_search_direct: str | None
    attachment_welcome_direct: str | None
    routing_disambiguation: Any
    routing_disambiguation_answer: str | None
    routing_disambiguation_suggestions: list | None
    session_memory_direct: str | None
    email_writing_mode: bool
    email_subtype: str | None
    text_correction_mode: bool
    text_correction_subtype: str | None
    interpretation_without_data_answer: str | None
    pipeline_stage_additions: list[str]


class ChatTurnPreparationPreToolContextService:
    @classmethod
    def build(
        cls,
        *,
        message: str,
        workspace_context: dict,
        history_source: list,
        attachments: list[dict],
        attachment_ids,
        session,
        user_id,
        allowed_action_ids: list[str],
        canvas_action,
        analysis_mode: bool,
        text_task_pure: bool,
        text_task_category: str | None,
        fast_path_enabled: bool,
        fast_path_max_chars: int,
        ingress_fast_path: bool,
        session_memory_service,
    ) -> ChatTurnPreparationPreToolContextResult:
        direct_answer_bundle = ChatTurnPreparationDirectAnswerService.build_early_bundle(
            message=message,
            workspace_context=workspace_context,
            history_source=history_source,
            attachments=attachments,
            attachment_ids=attachment_ids,
            session=session,
            user_id=user_id,
            allowed_action_ids=allowed_action_ids,
            canvas_action=canvas_action,
            analysis_mode=analysis_mode,
            text_task_pure=text_task_pure,
            text_task_category=text_task_category,
            fast_path_enabled=fast_path_enabled,
            fast_path_max_chars=fast_path_max_chars,
        )

        stage_additions = list(direct_answer_bundle.pipeline_stage_additions)
        workspace_context = dict(workspace_context)
        workspace_context.update(direct_answer_bundle.workspace_context_patches)

        memory_context = ChatTurnPreparationMemoryContextService.build(
            message=message,
            workspace_context=workspace_context,
            history_source=history_source,
            attachments=attachments,
            session=session,
            user_id=user_id,
            session_memory_service=session_memory_service,
        )

        workspace_context = memory_context.workspace_context
        stage_additions.extend(memory_context.pipeline_stage_additions)

        interpretation_without_data_answer = (
            ChatTurnPreparationDirectAnswerService.resolve_interpretation_without_data(
                message=message,
                history_source=history_source,
                canvas_action=canvas_action,
                pre_capability_answer=direct_answer_bundle.pre_capability_answer,
                analysis_mode=analysis_mode,
                text_task_pure=text_task_pure,
            )
        )

        return ChatTurnPreparationPreToolContextResult(
            workspace_context=workspace_context,
            working_memory_snapshot=memory_context.working_memory_snapshot,
            conversation_context=memory_context.conversation_context,
            canvas_action=canvas_action,
            fast_path=direct_answer_bundle.fast_path or ingress_fast_path,
            pre_capability_answer=direct_answer_bundle.pre_capability_answer,
            small_talk_direct=direct_answer_bundle.small_talk_direct,
            utility_direct=direct_answer_bundle.utility_direct,
            unclear_direct=direct_answer_bundle.unclear_direct,
            web_save_sources_direct=direct_answer_bundle.web_save_sources_direct,
            web_post_search_direct=direct_answer_bundle.web_post_search_direct,
            attachment_welcome_direct=direct_answer_bundle.attachment_welcome_direct,
            routing_disambiguation=direct_answer_bundle.routing_disambiguation,
            routing_disambiguation_answer=direct_answer_bundle.routing_disambiguation_answer,
            routing_disambiguation_suggestions=(
                direct_answer_bundle.routing_disambiguation_suggestions
            ),
            session_memory_direct=direct_answer_bundle.session_memory_direct,
            email_writing_mode=direct_answer_bundle.email_writing_mode,
            email_subtype=direct_answer_bundle.email_subtype,
            text_correction_mode=direct_answer_bundle.text_correction_mode,
            text_correction_subtype=direct_answer_bundle.text_correction_subtype,
            interpretation_without_data_answer=interpretation_without_data_answer,
            pipeline_stage_additions=stage_additions,
        )
