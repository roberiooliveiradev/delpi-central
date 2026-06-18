"""Respostas diretas pré-tool do turno — Fase 3C lote 15."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.application.services.chat_attachment_welcome_service import (
    ChatAttachmentWelcomeService,
)
from app.application.services.chat_capabilities_service import ChatCapabilitiesService
from app.application.services.chat_meta_direct_answer_service import (
    ChatMetaDirectAnswerService,
)
from app.application.services.chat_project_sources_direct_answer_service import (
    ChatProjectSourcesDirectAnswerService,
)
from app.application.services.chat_session_memory_direct_answer_service import (
    ChatSessionMemoryDirectAnswerService,
)
from app.application.services.chat_small_talk_service import ChatSmallTalkService
from app.application.services.chat_turn.chat_turn_preparation_content_service import (
    ChatTurnPreparationContentService,
)
from app.application.services.chat_utility_direct_answer_service import (
    ChatUtilityDirectAnswerService,
)
from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
from app.domain.services.chat_email_intent_service import ChatEmailIntentService
from app.domain.services.chat_fast_path_service import ChatFastPathService
from app.domain.services.chat_intent_disambiguation_service import (
    ChatIntentDisambiguationService,
)
from app.domain.services.chat_sql_query_refinement_service import (
    ChatSqlQueryRefinementService,
)
from app.domain.services.chat_text_correction_intent_service import (
    ChatTextCorrectionIntentService,
)
from app.domain.services.chat_unclear_request_service import ChatUnclearRequestService
from app.domain.services.chat_web_search_source_follow_up_service import (
    ChatWebSearchSourceFollowUpService,
)


@dataclass(frozen=True)
class ChatTurnPreparationDirectAnswerBundle:
    compound_meta_question: bool
    fast_path: bool
    pre_capability_answer: str | None
    small_talk_direct: str | None
    utility_direct: str | None
    unclear_direct: str | None
    web_save_sources_direct: str | None
    project_sources_direct: str | None
    web_post_search_direct: str | None
    attachment_welcome_direct: str | None
    routing_disambiguation: dict | None
    routing_disambiguation_answer: str | None
    routing_disambiguation_suggestions: list[dict[str, str]] | None
    learning_term_confirmation_answer: str | None
    learning_term_working_memory_patch: dict[str, Any] | None
    session_memory_direct: str | None
    email_writing_mode: bool
    email_subtype: str | None
    text_correction_mode: bool
    text_correction_subtype: str | None
    interpretation_without_data_answer: str | None
    workspace_context_patches: dict[str, Any]
    pipeline_stage_additions: list[str]


class ChatTurnPreparationDirectAnswerService:
    @classmethod
    def build_early_bundle(
        cls,
        *,
        message: str,
        workspace_context: dict,
        history_source: list,
        attachments: list[dict],
        attachment_ids,
        session,
        user_id,
        allowed_action_ids: list,
        canvas_action,
        analysis_mode: bool,
        text_task_pure: bool,
        text_task_category: str | None,
        fast_path_enabled: bool,
        fast_path_max_chars: int,
    ) -> ChatTurnPreparationDirectAnswerBundle:
        meta_intents = ChatMetaDirectAnswerService.detect_intents(message)
        compound_meta_question = meta_intents.count >= 2

        pre_capability_answer = None
        if not compound_meta_question:
            pre_capability_answer = ChatCapabilitiesService.resolve_capability_answer(
                message=message,
                workspace_context=workspace_context,
                allowed_action_ids=allowed_action_ids,
                action_catalog=ChatCapabilitiesService.load_action_catalog_for_agent(
                    allowed_action_ids,
                ),
            )

        fast_path = ChatFastPathService.should_use(
            message,
            enabled=fast_path_enabled,
            max_chars=fast_path_max_chars,
            attachment_ids=attachment_ids,
            previous_messages=history_source,
        )

        if canvas_action:
            fast_path = True

        small_talk_direct = ChatSmallTalkService.build_direct_answer(
            message=message,
            workspace_context=workspace_context,
            previous_messages=history_source,
        )
        utility_direct = ChatUtilityDirectAnswerService.build_direct_answer(
            message=message,
        )

        unclear_direct = None
        if not attachment_ids and not small_talk_direct and not utility_direct:
            unclear_direct = ChatUnclearRequestService.build_direct_answer(
                message=message,
                previous_messages=history_source,
            )

        from app.application.services.chat_web_search_save_sources_service import (
            ChatWebSearchSaveSourcesService,
        )

        web_save_sources_direct = ChatWebSearchSaveSourcesService.build_direct_answer(
            message=message,
            user_id=str(user_id),
            session=session,
            previous_messages=history_source,
        )

        project_sources_direct = ChatProjectSourcesDirectAnswerService.build_direct_answer(
            message=message,
            user_id=str(user_id),
            session=session,
            workspace_context=workspace_context,
        )

        web_post_search_direct = (
            ChatWebSearchSourceFollowUpService.build_post_search_follow_up_answer(
                message,
                history_source,
            )
        )

        attachment_welcome_direct = None

        if ChatAttachmentWelcomeService.should_welcome(
            message,
            attachment_ids=attachment_ids,
        ):
            attachment_welcome_direct = ChatAttachmentWelcomeService.build_direct_answer(
                attachments=attachments,
            )

        routing_disambiguation = None
        routing_disambiguation_answer = None
        routing_disambiguation_suggestions: list[dict[str, str]] | None = None

        if (
            not canvas_action
            and not pre_capability_answer
            and not analysis_mode
            and not text_task_pure
        ):
            routing_disambiguation = ChatIntentDisambiguationService.try_build(
                message,
                previous_messages=history_source,
                workspace_context=workspace_context,
                allowed_action_ids=allowed_action_ids,
            )

            if routing_disambiguation:
                routing_disambiguation_answer = routing_disambiguation.get("directAnswer")
                raw_suggestions = routing_disambiguation.get("suggestions")

                if isinstance(raw_suggestions, list):
                    routing_disambiguation_suggestions = [
                        dict(item) for item in raw_suggestions if isinstance(item, dict)
                    ]

        learning_term_confirmation_answer = None
        learning_term_working_memory_patch = None

        if (
            not canvas_action
            and not pre_capability_answer
            and not analysis_mode
            and not text_task_pure
            and not small_talk_direct
            and not utility_direct
        ):
            from app.application.services.chat_learning_term_confirmation_service import (
                ChatLearningTermConfirmationService,
            )

            project_id = getattr(session, "project_id", None)
            learning_term = ChatLearningTermConfirmationService().try_build(
                message=message,
                workspace_context=workspace_context,
                project_id=str(project_id) if project_id else None,
                created_by=str(user_id),
            )

            if learning_term:
                learning_term_confirmation_answer = learning_term.get("directAnswer")
                patch = learning_term.get("workingMemoryPatch")

                if isinstance(patch, dict):
                    learning_term_working_memory_patch = patch

        session_memory_direct = ChatSessionMemoryDirectAnswerService.build(
            message=message,
            workspace_context=workspace_context,
        )

        email_writing_mode = bool(
            text_task_pure and ChatEmailIntentService.is_email_writing(message)
        )
        email_subtype = (
            ChatEmailIntentService.classify_subtype(message) if email_writing_mode else None
        )

        text_correction_mode = bool(
            text_task_pure
            and not email_writing_mode
            and ChatTextCorrectionIntentService.is_text_correction(message)
        )
        text_correction_subtype = (
            ChatTextCorrectionIntentService.classify_subtype(message)
            if text_correction_mode
            else None
        )

        workspace_context_patches: dict[str, Any] = {}
        pipeline_stage_additions: list[str] = []

        if text_task_pure:
            workspace_context_patches["textTaskMode"] = True
            workspace_context_patches["textTaskCategory"] = text_task_category

        if email_writing_mode:
            workspace_context_patches["emailWritingMode"] = True
            workspace_context_patches["emailSubtype"] = email_subtype
            pipeline_stage_additions.append("email_writing")

        if learning_term_confirmation_answer and "learning_term" not in pipeline_stage_additions:
            pipeline_stage_additions.append("learning_term")

        if session_memory_direct and "session_memory" not in pipeline_stage_additions:
            pipeline_stage_additions.append("session_memory")

        if project_sources_direct and "project_sources_inventory" not in pipeline_stage_additions:
            pipeline_stage_additions.append("project_sources_inventory")

            from app.domain.services.chat_project_sources_inventory_service import (
                ChatProjectSourcesInventoryService,
            )

            sources = ChatProjectSourcesDirectAnswerService.list_project_sources(
                user_id=str(user_id),
                session=session,
                workspace_context=workspace_context,
            )

            if sources:
                workspace_context_patches["pendingProjectSourcesInventory"] = (
                    ChatProjectSourcesInventoryService.serialize_sources(sources)
                )

        if text_correction_mode:
            workspace_context_patches["textCorrectionMode"] = True
            workspace_context_patches["textCorrectionSubtype"] = text_correction_subtype
            pipeline_stage_additions.append("text_correction")

        return ChatTurnPreparationDirectAnswerBundle(
            compound_meta_question=compound_meta_question,
            fast_path=fast_path,
            pre_capability_answer=pre_capability_answer,
            small_talk_direct=small_talk_direct,
            utility_direct=utility_direct,
            unclear_direct=unclear_direct,
            web_save_sources_direct=web_save_sources_direct,
            project_sources_direct=project_sources_direct,
            web_post_search_direct=web_post_search_direct,
            attachment_welcome_direct=attachment_welcome_direct,
            routing_disambiguation=routing_disambiguation,
            routing_disambiguation_answer=routing_disambiguation_answer,
            routing_disambiguation_suggestions=routing_disambiguation_suggestions,
            learning_term_confirmation_answer=learning_term_confirmation_answer,
            learning_term_working_memory_patch=learning_term_working_memory_patch,
            session_memory_direct=session_memory_direct,
            email_writing_mode=email_writing_mode,
            email_subtype=email_subtype,
            text_correction_mode=text_correction_mode,
            text_correction_subtype=text_correction_subtype,
            interpretation_without_data_answer=None,
            workspace_context_patches=workspace_context_patches,
            pipeline_stage_additions=pipeline_stage_additions,
        )

    @classmethod
    def resolve_interpretation_without_data(
        cls,
        *,
        message: str,
        history_source: list,
        canvas_action,
        pre_capability_answer: str | None,
        analysis_mode: bool,
        text_task_pure: bool,
    ) -> str | None:
        if canvas_action or pre_capability_answer or analysis_mode or text_task_pure:
            return None

        if ChatAnalysisIntentService.is_data_reference_without_tool_data(
            message,
            history_source,
        ) and not ChatSqlQueryRefinementService.is_sql_follow_up(
            message,
            previous_messages=history_source,
        ):
            return ChatTurnPreparationContentService.get(
                "directAnswers",
                "interpretationWithoutData",
            )

        return None
