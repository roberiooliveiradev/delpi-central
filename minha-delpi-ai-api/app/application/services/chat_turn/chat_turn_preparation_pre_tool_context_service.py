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
from app.domain.services.chat_unclear_request_service import ChatUnclearRequestService


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
    project_sources_direct: str | None
    web_post_search_direct: str | None
    attachment_welcome_direct: str | None
    routing_disambiguation: Any
    routing_disambiguation_answer: str | None
    routing_disambiguation_suggestions: list | None
    learning_term_confirmation_answer: str | None
    session_memory_direct: str | None
    email_writing_mode: bool
    email_subtype: str | None
    text_correction_mode: bool
    text_correction_subtype: str | None
    interpretation_without_data_answer: str | None
    turn_grounding: dict[str, Any] | None
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
        turn_response_format: str | None = None,
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
            defer_unclear=True,
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
            turn_response_format=turn_response_format,
        )

        workspace_context = memory_context.workspace_context
        working_memory_snapshot = dict(memory_context.working_memory_snapshot)
        stage_additions.extend(memory_context.pipeline_stage_additions)

        memory_patch = direct_answer_bundle.learning_term_working_memory_patch

        if isinstance(memory_patch, dict):
            for key, value in memory_patch.items():
                if value is None:
                    working_memory_snapshot.pop(key, None)
                else:
                    working_memory_snapshot[key] = value

            workspace_context = dict(workspace_context)
            workspace_context["workingMemory"] = working_memory_snapshot

        from app.domain.services.chat_turn_grounding_service import (
            ChatTurnGroundingService,
        )

        turn_grounding = ChatTurnGroundingService.evaluate(
            message=message,
            snapshot=working_memory_snapshot,
            previous_messages=history_source,
        )
        turn_grounding_metadata = turn_grounding.to_metadata()
        working_last_action = (
            working_memory_snapshot.get("lastAction")
            if isinstance(working_memory_snapshot.get("lastAction"), dict)
            else None
        )
        working_focus = (
            working_memory_snapshot.get("operationalFocus")
            if isinstance(working_memory_snapshot.get("operationalFocus"), dict)
            else None
        )
        grounded_stage = ChatTurnGroundingService.resolve_grounded_stage(
            message=message,
            excerpt=turn_grounding.excerpt if isinstance(turn_grounding.excerpt, dict) else None,
            last_action=working_last_action,
            operational_focus=working_focus,
        )

        if grounded_stage:
            turn_grounding_metadata["stage"] = grounded_stage

        from app.domain.services.chat_follow_up_turn_interpretation_service import (
            ChatFollowUpTurnInterpretationService,
        )

        follow_up = ChatFollowUpTurnInterpretationService.interpret(
            message=message,
            last_action=working_last_action,
            last_result_excerpt=turn_grounding.excerpt
            if isinstance(turn_grounding.excerpt, dict)
            else None,
            operational_focus=working_focus,
        )
        turn_grounding_metadata["followUp"] = follow_up.to_metadata()

        workspace_context = dict(workspace_context)
        workspace_context["turnGrounding"] = turn_grounding_metadata
        stage_additions.append("turn_grounding")

        from app.domain.services.chat_clarify_policy_service import (
            ChatClarifyPolicyService,
        )
        from app.domain.services.chat_unclear_request_service import (
            ChatUnclearRequestService,
        )

        clarify_policy = ChatClarifyPolicyService.resolve(turn_grounding)
        unclear_direct = None

        if (
            not attachment_ids
            and not direct_answer_bundle.small_talk_direct
            and not direct_answer_bundle.utility_direct
        ):
            if clarify_policy.kind.value == "ungrounded":
                unclear_direct = ChatUnclearRequestService.build_direct_answer(
                    message=message,
                    previous_messages=history_source,
                    grounding_status=turn_grounding.status.value,
                )
            elif clarify_policy.kind.value == "ambiguous" and clarify_policy.answer:
                unclear_direct = clarify_policy.answer

            if unclear_direct:
                stage_additions.append("unclear_request")

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
            working_memory_snapshot=working_memory_snapshot,
            conversation_context=memory_context.conversation_context,
            canvas_action=canvas_action,
            fast_path=direct_answer_bundle.fast_path or ingress_fast_path,
            pre_capability_answer=direct_answer_bundle.pre_capability_answer,
            small_talk_direct=direct_answer_bundle.small_talk_direct,
            utility_direct=direct_answer_bundle.utility_direct,
            unclear_direct=unclear_direct,
            web_save_sources_direct=direct_answer_bundle.web_save_sources_direct,
            project_sources_direct=direct_answer_bundle.project_sources_direct,
            web_post_search_direct=direct_answer_bundle.web_post_search_direct,
            attachment_welcome_direct=direct_answer_bundle.attachment_welcome_direct,
            routing_disambiguation=direct_answer_bundle.routing_disambiguation,
            routing_disambiguation_answer=direct_answer_bundle.routing_disambiguation_answer,
            routing_disambiguation_suggestions=(
                direct_answer_bundle.routing_disambiguation_suggestions
            ),
            learning_term_confirmation_answer=(
                direct_answer_bundle.learning_term_confirmation_answer
            ),
            session_memory_direct=direct_answer_bundle.session_memory_direct,
            email_writing_mode=direct_answer_bundle.email_writing_mode,
            email_subtype=direct_answer_bundle.email_subtype,
            text_correction_mode=direct_answer_bundle.text_correction_mode,
            text_correction_subtype=direct_answer_bundle.text_correction_subtype,
            interpretation_without_data_answer=interpretation_without_data_answer,
            turn_grounding=turn_grounding_metadata,
            pipeline_stage_additions=stage_additions,
        )
