"""Resolução de direct-answer e skip_rag após a fase de ferramentas — Fase 3C lote 18."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from app.application.services.chat_assistant_identity_service import (
    ChatAssistantIdentityService,
)
from app.application.services.chat_agent_skills_service import ChatAgentSkillsService
from app.application.services.chat_intelligence_pipeline_service import (
    ChatIntelligencePipelineService,
)
from app.application.services.chat_meta_direct_answer_service import (
    ChatMetaDirectAnswerService,
)
from app.domain.services.chat_external_action_direct_response_service import (
    ChatExternalActionDirectResponseService,
)
from app.domain.services.chat_text_task_intent_service import ChatTextTaskIntentService
from app.infrastructure.config.settings import Settings


@dataclass(frozen=True)
class ChatTurnPreparationPostToolResult:
    direct_answer: str | None
    skip_rag: bool
    tool_context: dict
    assistant_identity_direct: str | None


class ChatTurnPreparationPostToolResolutionService:
    @classmethod
    def resolve(
        cls,
        *,
        message: str,
        workspace_context: dict,
        history_source: list,
        pipeline_stages: list[str],
        tool_context: dict,
        tool_calls: list,
        fast_path: bool,
        analysis_mode: bool,
        operational_optimize: bool,
        text_task_pure: bool,
        canvas_action,
        pre_capability_answer: str | None,
        small_talk_direct: str | None,
        utility_direct: str | None,
        web_post_search_direct: str | None,
        web_save_sources_direct: str | None,
        attachment_welcome_direct: str | None,
        session_memory_direct: str | None,
        interpretation_without_data_answer: str | None,
        unclear_direct: str | None,
        missing_product_code_answer: str | None,
        ambiguous_period_answer: str | None,
        common_chat_operational_answer: str | None,
        routing_disambiguation_answer: str | None,
        skip_tools_for_data_interpretation: bool,
        resolve_user_identity_answer: Callable[[str], str | None],
        resolve_capabilities_answer: Callable[[str], str | None],
    ) -> ChatTurnPreparationPostToolResult:
        resolved_skills = workspace_context.get("skills") or {}
        assistant_identity_question = ChatAssistantIdentityService.is_assistant_identity_question(
            message
        )
        assistant_identity_direct = None

        if (
            assistant_identity_question
            and Settings.CHAT_ASSISTANT_IDENTITY_DIRECT_ENABLED
        ):
            assistant_identity_direct = ChatAssistantIdentityService.build_direct_answer(
                message=message,
                workspace_context=workspace_context,
            )

        skip_rag = (
            (
                fast_path
                and not ChatAgentSkillsService.preserves_rag_on_fast_path(resolved_skills)
            )
            or bool(small_talk_direct)
            or bool(utility_direct)
            or bool(web_save_sources_direct)
            or bool(web_post_search_direct)
            or bool(attachment_welcome_direct)
            or bool(text_task_pure)
            or operational_optimize
            or analysis_mode
            or ChatExternalActionDirectResponseService.should_skip_rag(tool_context)
            or bool(assistant_identity_direct)
        )

        from app.domain.services.chat_sql_intent_service import ChatSqlIntentService
        from app.domain.services.chat_sql_query_refinement_service import (
            ChatSqlQueryRefinementService,
        )

        if canvas_action:
            direct_answer = canvas_action.answer
        elif pre_capability_answer:
            direct_answer = pre_capability_answer
        elif small_talk_direct:
            direct_answer = small_talk_direct
        elif utility_direct:
            direct_answer = utility_direct
        elif web_post_search_direct:
            direct_answer = web_post_search_direct
        elif web_save_sources_direct:
            direct_answer = web_save_sources_direct
        elif (
            isinstance(tool_context, dict)
            and str(tool_context.get("directAnswer") or "").strip()
            and (
                ChatSqlQueryRefinementService.is_sql_follow_up(
                    message,
                    previous_messages=history_source,
                )
                or ChatSqlIntentService.is_sql_conversation_turn(message)
            )
        ):
            direct_answer = str(tool_context.get("directAnswer") or "").strip()
        elif session_memory_direct:
            direct_answer = session_memory_direct
        elif attachment_welcome_direct:
            direct_answer = attachment_welcome_direct
        elif interpretation_without_data_answer:
            direct_answer = interpretation_without_data_answer
        elif analysis_mode:
            direct_answer = ChatIntelligencePipelineService.resolve_analysis_direct_answer(
                message,
                history_source,
                current_tool_calls=tool_calls,
            )

            if not direct_answer:
                direct_answer = ChatIntelligencePipelineService.resolve_direct_answer(
                    tool_context,
                    analysis_mode=analysis_mode,
                )
        else:
            direct_answer = ChatIntelligencePipelineService.resolve_direct_answer(
                tool_context,
                analysis_mode=analysis_mode,
            )

        if canvas_action or pre_capability_answer or small_talk_direct or utility_direct or (
            web_post_search_direct
        ) or (
            web_save_sources_direct
        ) or (
            session_memory_direct
        ) or (
            attachment_welcome_direct
        ) or (
            analysis_mode and direct_answer
        ) or interpretation_without_data_answer:
            skip_rag = True

        if not direct_answer:
            meta_direct = ChatMetaDirectAnswerService.build(
                message=message,
                workspace_context=workspace_context,
                resolve_user_identity_answer=resolve_user_identity_answer,
                resolve_capabilities_answer=resolve_capabilities_answer,
            )

            if meta_direct:
                direct_answer = meta_direct
                skip_rag = True
                pipeline_stages.append("meta_direct_answer")

        if not direct_answer:
            user_direct = resolve_user_identity_answer(message)

            if user_direct:
                direct_answer = user_direct
                skip_rag = True

        if not direct_answer:
            caps_direct = resolve_capabilities_answer(message)

            if caps_direct:
                direct_answer = caps_direct
                skip_rag = True

        if not direct_answer and assistant_identity_direct:
            direct_answer = assistant_identity_direct
            skip_rag = True

        if not direct_answer and missing_product_code_answer:
            direct_answer = missing_product_code_answer
            skip_rag = True

        if not direct_answer and ambiguous_period_answer:
            direct_answer = ambiguous_period_answer
            skip_rag = True

        if not direct_answer and common_chat_operational_answer:
            direct_answer = common_chat_operational_answer
            skip_rag = True

        if not direct_answer and routing_disambiguation_answer:
            direct_answer = routing_disambiguation_answer
            skip_rag = True

        if not direct_answer and interpretation_without_data_answer:
            direct_answer = interpretation_without_data_answer
            skip_rag = True

        if not direct_answer and unclear_direct:
            direct_answer = unclear_direct
            skip_rag = True

            if "unclear_request" not in pipeline_stages:
                pipeline_stages.append("unclear_request")

        if not direct_answer and skip_tools_for_data_interpretation:
            from app.application.services.chat_data_interpretation_answer_service import (
                ChatDataInterpretationAnswerService,
            )

            interpreted = ChatDataInterpretationAnswerService.build_answer(
                message,
                history_source,
            )

            if interpreted:
                direct_answer = interpreted
                skip_rag = True

                from app.application.services.chat_text_task_composer_service import (
                    ChatTextTaskComposerService,
                )

                draft_meta = ChatTextTaskComposerService.build_operational_email_with_metadata(
                    message=message,
                    previous_messages=history_source,
                )

                if draft_meta:
                    tool_context["operationalEmailDraft"] = draft_meta

                    if "email_operational" not in pipeline_stages:
                        pipeline_stages.append("email_operational")

        if tool_calls:
            from app.application.services.chat_tool_context_service import (
                ChatToolContextService,
            )

            if not (
                isinstance(tool_context, dict) and tool_context.get("sqlRequiresLlm")
            ):
                presentation_answer = ChatToolContextService.prefer_presentation_direct_answer(
                    direct_answer,
                    tool_calls,
                    message=message,
                )

                if presentation_answer:
                    direct_answer = presentation_answer
                    skip_rag = True

            from app.domain.services.chat_rich_presentation_text_service import (
                ChatRichPresentationTextService,
            )

            authorized_tool_answer = (
                ChatToolContextService.build_authorized_answer_from_tool_calls(
                    tool_calls
                )
            )

            if (
                authorized_tool_answer
                and ChatRichPresentationTextService.should_prefer_authorized_answer_over_llm(
                    tool_calls
                )
            ):
                direct_answer = authorized_tool_answer
                skip_rag = True
            else:
                from app.domain.services.chat_product_overview_intent_service import (
                    ChatProductOverviewIntentService,
                )

                if ChatProductOverviewIntentService.should_force_llm_synthesis(
                    message,
                    tool_calls,
                ):
                    if authorized_tool_answer:
                        direct_answer = authorized_tool_answer
                        skip_rag = True
                    else:
                        direct_answer = None
                        skip_rag = False

        if ChatTextTaskIntentService.is_mixed_text_and_operational(message):
            from app.application.services.chat_text_task_composer_service import (
                ChatTextTaskComposerService,
            )

            mixed_draft = ChatTextTaskComposerService.build_operational_email_with_metadata(
                message=message,
                tool_calls=tool_calls,
            )

            if mixed_draft:
                from app.application.services.chat_email_answer_guard_service import (
                    ChatEmailAnswerGuardService,
                )

                mixed_text, _guard = ChatEmailAnswerGuardService.apply(
                    str(mixed_draft.get("text") or ""),
                    message=message,
                    workspace_context={"emailWritingMode": True},
                )
                tool_context["operationalEmailDraft"] = mixed_draft

                if mixed_text:
                    if direct_answer:
                        direct_answer = f"{direct_answer.strip()}\n\n---\n\n{mixed_text}"
                    else:
                        direct_answer = mixed_text

                skip_rag = True

                if "text_task_mixed" not in pipeline_stages:
                    pipeline_stages.append("text_task_mixed")

                if "email_operational" not in pipeline_stages:
                    pipeline_stages.append("email_operational")

        if direct_answer:
            skip_rag = True

            if "direct_answer" not in pipeline_stages:
                pipeline_stages.append("direct_answer")

        if text_task_pure and not direct_answer:
            skip_rag = True

        return ChatTurnPreparationPostToolResult(
            direct_answer=direct_answer,
            skip_rag=skip_rag,
            tool_context=tool_context,
            assistant_identity_direct=assistant_identity_direct,
        )
