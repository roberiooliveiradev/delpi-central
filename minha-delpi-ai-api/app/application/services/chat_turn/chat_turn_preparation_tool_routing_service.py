"""Decisão de skip-tools e execução da fase de ferramentas — Fase 3C lote 17."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from app.application.services.chat_intelligence_pipeline_service import (
    ChatIntelligencePipelineService,
)
from app.application.services.chat_pipeline_timings import ChatPipelineTimings
from app.application.services.chat_conversation_context_service import (
    ChatConversationContextService,
)
from app.application.services.chat_assistant_identity_service import (
    ChatAssistantIdentityService,
)
from app.application.services.chat_user_context_service import ChatUserContextService
from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
from app.infrastructure.config.settings import Settings
from app.domain.services.chat_operational_parameter_service import (
    ChatOperationalParameterService,
)


@dataclass(frozen=True)
class ChatTurnPreparationSkipToolFlags:
    skip_tools_for_user_identity: bool
    skip_tools_for_assistant_identity: bool
    skip_tools_for_data_interpretation: bool
    skip_tools_for_attachment_document: bool
    skip_tools_for_inactive_agent: bool
    skip_tools_for_project_sources_content: bool
    skip_tools_for_session_review: bool
    skip_tools_for_grounded_narrate: bool
    request_attachment_ids: list[str]


@dataclass(frozen=True)
class ChatTurnPreparationOperationalGuards:
    missing_product_code_answer: str | None
    ambiguous_period_answer: str | None
    missing_date_answer: str | None
    common_chat_operational_answer: str | None


@dataclass(frozen=True)
class ChatTurnPreparationToolPhaseResult:
    tool_context: dict
    tool_calls: list
    analysis_mode: bool
    operational_optimize: bool


class ChatTurnPreparationToolRoutingService:
    _FOLLOW_UP_STAGES_SUPPRESS_MISSING_DATE = frozenset(
        {
            "grounded_revise_query",
            "grounded_challenge_result",
            "grounded_clarify_slot",
            "grounded_narrate_recap",
            "grounded_narrate_insight",
        }
    )

    @classmethod
    def _suppress_missing_date_for_follow_up(cls, workspace: dict) -> bool:
        turn_grounding = workspace.get("turnGrounding") or {}
        if not isinstance(turn_grounding, dict):
            return False
        stage = str(turn_grounding.get("stage") or "").strip()
        if stage in cls._FOLLOW_UP_STAGES_SUPPRESS_MISSING_DATE:
            return True
        follow_up = turn_grounding.get("followUp")
        if isinstance(follow_up, dict):
            decision = str(follow_up.get("decision") or "").strip()
            if decision in {
                "revise_last_query",
                "challenge_last_result",
                "clarify_slot",
                "narrate_recap",
            }:
                return True
        return False

    @classmethod
    def resolve_operational_guards(
        cls,
        *,
        message: str,
        history_source: list,
        conversation_context: str,
        working_memory_snapshot: dict,
        workspace_context: dict,
        canvas_action,
        pre_capability_answer: str | None,
        analysis_mode: bool,
        text_task_pure: bool,
    ) -> ChatTurnPreparationOperationalGuards:
        from app.domain.services.chat_host_surface_context_service import (
            ChatHostSurfaceContextService,
        )

        workspace = workspace_context if isinstance(workspace_context, dict) else {}
        host_context = (
            workspace.get("tvDashboardHostContext")
            or workspace.get("hostContext")
        )
        if ChatHostSurfaceContextService.is_tv_mutation_turn(
            message,
            host_context if isinstance(host_context, dict) else None,
            workspace_context=workspace,
        ):
            # O surface TV é dono da mutação. Não deixar heurísticas operacionais
            # (ex.: OEE/KPI → missing_params) bloquearem o suggest-ops do BFF.
            return ChatTurnPreparationOperationalGuards(
                missing_product_code_answer=None,
                ambiguous_period_answer=None,
                missing_date_answer=None,
                common_chat_operational_answer=None,
            )

        if canvas_action or pre_capability_answer or analysis_mode or text_task_pure:
            return ChatTurnPreparationOperationalGuards(
                missing_product_code_answer=None,
                ambiguous_period_answer=None,
                missing_date_answer=None,
                common_chat_operational_answer=None,
            )

        from app.domain.services.chat_presentation_format_refinement_service import (
            ChatPresentationFormatRefinementService,
        )
        from app.domain.services.chat_product_query_intent_service import (
            ChatProductQueryIntentService,
        )
        from app.domain.services.chat_sql_operational_intent_service import (
            ChatSqlOperationalIntentService,
        )

        if ChatPresentationFormatRefinementService.looks_like_format_refinement(message):
            return ChatTurnPreparationOperationalGuards(
                missing_product_code_answer=None,
                ambiguous_period_answer=None,
                missing_date_answer=None,
                common_chat_operational_answer=None,
            )

        skip_missing_product_prompt = (
            ChatSqlOperationalIntentService.requires_sql_knowledge(message)
            and not ChatProductQueryIntentService.extract_product_code(message)
        )

        if skip_missing_product_prompt:
            missing_product_code_answer = None
        else:
            from app.domain.services.chat_operational_identifier_resolution_service import (
                ChatOperationalIdentifierResolutionService,
            )

            missing_product_code_answer = (
                ChatOperationalIdentifierResolutionService.resolve_clarification_answer(
                    message
                )
                or ChatOperationalParameterService.resolve_missing_product_code_answer(
                    message,
                    conversation_context=conversation_context,
                    previous_messages=history_source,
                    memory_snapshot=working_memory_snapshot,
                )
            )

        ambiguous_period_answer = (
            ChatOperationalParameterService.resolve_ambiguous_period_answer(
                message,
                previous_messages=history_source,
            )
        )

        if cls._suppress_missing_date_for_follow_up(workspace):
            ambiguous_period_answer = None

        missing_date_answer = None

        if not missing_product_code_answer and not ambiguous_period_answer:
            if not cls._suppress_missing_date_for_follow_up(workspace):
                missing_date_answer = (
                    ChatOperationalParameterService.resolve_missing_date_answer(
                        message,
                        conversation_context=conversation_context,
                        previous_messages=history_source,
                        memory_snapshot=working_memory_snapshot,
                    )
                )

        from app.application.services.chat_common_chat_operational_guidance_service import (
            ChatCommonChatOperationalGuidanceService,
        )

        common_chat_operational_answer = (
            ChatCommonChatOperationalGuidanceService.resolve_direct_answer(
                message,
                workspace_context=workspace_context,
                previous_messages=history_source,
            )
        )

        if common_chat_operational_answer and missing_product_code_answer:
            missing_product_code_answer = None

        if common_chat_operational_answer:
            # Guidance de agente tem prioridade sobre pedir só data/período no chat comum.
            missing_date_answer = None
            ambiguous_period_answer = None

        return ChatTurnPreparationOperationalGuards(
            missing_product_code_answer=missing_product_code_answer,
            ambiguous_period_answer=ambiguous_period_answer,
            missing_date_answer=missing_date_answer,
            common_chat_operational_answer=common_chat_operational_answer,
        )

    @classmethod
    def resolve_skip_tool_flags(
        cls,
        *,
        message: str,
        request,
        history_source: list,
        workspace_context: dict | None = None,
    ) -> ChatTurnPreparationSkipToolFlags:
        from app.application.services.chat_workspace_agent_activation_service import (
            ChatWorkspaceAgentActivationService,
        )
        from app.domain.services.chat_web_search_intent_service import (
            ChatWebSearchIntentService,
        )

        skip_tools_for_user_identity = bool(
            getattr(request, "access_token", None)
            and ChatUserContextService.is_user_identity_question(message)
        )
        from app.application.services.chat_intelligence_runtime_access import (
            resolve_chat_intelligence_runtime,
        )

        skip_tools_for_assistant_identity = bool(
            resolve_chat_intelligence_runtime().assistant_identity_direct_enabled
            and ChatAssistantIdentityService.is_assistant_identity_question(message)
        )
        from app.domain.services.chat_attachment_document_intent_service import (
            ChatAttachmentDocumentIntentService,
        )
        from app.domain.services.chat_document_vision_skill_service import (
            ChatDocumentVisionSkillService,
        )
        from app.domain.services.chat_drawing_intent_service import ChatDrawingIntentService
        from app.domain.skills.chat_skill_registry import ChatSkillRegistry

        workspace = workspace_context if isinstance(workspace_context, dict) else {}
        request_attachment_ids = list(getattr(request, "attachment_ids", None) or [])
        has_agent = bool(workspace.get("agent"))
        runtime_skills = workspace.get("skills")

        if not isinstance(runtime_skills, dict):
            runtime_skills = ChatSkillRegistry.resolve_runtime_flags(
                agent_metadata=workspace.get("agent")
                if isinstance(workspace.get("agent"), dict)
                else None,
                allowed_action_ids=list(workspace.get("allowedActionIds") or []),
                has_agent=has_agent,
            )

        skip_tools_for_attachment_document = bool(
            request_attachment_ids
            and ChatAttachmentDocumentIntentService.is_document_content_question(message)
            and ChatDocumentVisionSkillService.allows_attachment_document_turn(
                runtime_skills=runtime_skills,
                has_agent=has_agent,
                message=message,
            )
            and not ChatDrawingIntentService.is_drawing_analysis_request(
                message,
                attachment_ids=request_attachment_ids,
            )
        )

        skip_tools_for_inactive_agent = False

        if not ChatWorkspaceAgentActivationService.operational_tools_enabled(
            workspace_context
        ):
            from app.domain.services.chat_host_surface_context_service import (
                ChatHostSurfaceContextService,
            )

            # Chat comum bloqueia OpenAPI/agentic; exceções de plataforma:
            # anexos, web_search e copiloto de surface embutido (TV Dashboard).
            skip_tools_for_inactive_agent = not (
                request_attachment_ids
                or ChatWebSearchIntentService.matches(message)
                or ChatHostSurfaceContextService.allows_common_chat_platform_tools(
                    workspace,
                    message=message,
                )
            )

        from app.domain.services.chat_project_sources_intent_service import (
            ChatProjectSourcesIntentService,
        )

        working_memory = workspace.get("workingMemory")
        skip_tools_for_project_sources_content = ChatProjectSourcesIntentService.is_content_question(
            message,
            memory_snapshot=working_memory if isinstance(working_memory, dict) else None,
            previous_messages=history_source,
        )

        from app.domain.services.chat_intent_router.chat_intent_router_heuristics_service import (
            ChatIntentRouterHeuristicsService,
        )

        skip_tools_for_session_review = (
            ChatIntentRouterHeuristicsService.looks_conversation_meta(message)
        )

        turn_grounding = workspace.get("turnGrounding") or {}
        excerpt = (
            working_memory.get("lastResultExcerpt")
            if isinstance(working_memory, dict)
            else None
        )

        if not isinstance(excerpt, dict):
            excerpt = turn_grounding.get("excerpt")

        from app.domain.services.chat_turn_grounding_service import (
            ChatTurnGroundingService,
        )

        skip_tools_for_grounded_narrate = (
            turn_grounding.get("status") == "grounded"
            and ChatTurnGroundingService.resolve_grounded_stage(
                message=message,
                excerpt=excerpt if isinstance(excerpt, dict) else None,
                last_action=working_memory.get("lastAction")
                if isinstance(working_memory, dict)
                and isinstance(working_memory.get("lastAction"), dict)
                else None,
                operational_focus=working_memory.get("operationalFocus")
                if isinstance(working_memory, dict)
                and isinstance(working_memory.get("operationalFocus"), dict)
                else None,
            )
            in {
                "grounded_narrate_recap",
                "grounded_narrate_insight",
                "grounded_challenge_result",
                "grounded_clarify_slot",
            }
        )

        follow_up = turn_grounding.get("followUp") if isinstance(turn_grounding, dict) else None
        requires_last_action_reexec = (
            str(turn_grounding.get("stage") or "").strip() == "grounded_revise_query"
            or (
                isinstance(follow_up, dict)
                and (
                    follow_up.get("requiresLastActionReexec") is True
                    or str(follow_up.get("continuityMode") or "").strip()
                    == "consume_last_action"
                )
            )
        )

        skip_tools_for_data_interpretation = (
            not skip_tools_for_grounded_narrate
            and not requires_last_action_reexec
            and not ChatTurnGroundingService.should_enrich_before_insight(
                message,
                excerpt if isinstance(excerpt, dict) else None,
            )
            and not ChatTurnGroundingService.should_narrate_insight_only(message)
            and ChatAnalysisIntentService.is_data_interpretation_request(
                message,
                history_source,
            )
            and ChatConversationContextService.has_recent_tool_data(history_source)
        )

        return ChatTurnPreparationSkipToolFlags(
            skip_tools_for_user_identity=skip_tools_for_user_identity,
            skip_tools_for_assistant_identity=skip_tools_for_assistant_identity,
            skip_tools_for_data_interpretation=skip_tools_for_data_interpretation,
            skip_tools_for_attachment_document=skip_tools_for_attachment_document,
            skip_tools_for_inactive_agent=skip_tools_for_inactive_agent,
            skip_tools_for_project_sources_content=skip_tools_for_project_sources_content,
            skip_tools_for_session_review=skip_tools_for_session_review,
            skip_tools_for_grounded_narrate=skip_tools_for_grounded_narrate,
            request_attachment_ids=request_attachment_ids,
        )

    @classmethod
    def should_skip_tools(
        cls,
        *,
        canvas_action,
        canvas_operational_update: bool,
        pre_capability_answer: str | None,
        missing_product_code_answer: str | None,
        ambiguous_period_answer: str | None,
        missing_date_answer: str | None,
        common_chat_operational_answer: str | None,
        routing_disambiguation_answer: str | None,
        learning_term_confirmation_answer: str | None,
        interpretation_without_data_answer: str | None,
        skip_flags: ChatTurnPreparationSkipToolFlags,
        small_talk_direct: str | None,
        utility_direct: str | None,
        web_save_sources_direct: str | None,
        project_sources_direct: str | None,
        web_post_search_direct: str | None,
        attachment_welcome_direct: str | None,
        unclear_direct: str | None,
        text_task_pure: bool,
    ) -> bool:
        return bool(
            (
                canvas_action
                or pre_capability_answer
                or missing_product_code_answer
                or ambiguous_period_answer
                or missing_date_answer
                or common_chat_operational_answer
                or learning_term_confirmation_answer
                or routing_disambiguation_answer
                or interpretation_without_data_answer
                or skip_flags.skip_tools_for_user_identity
                or skip_flags.skip_tools_for_assistant_identity
                or skip_flags.skip_tools_for_data_interpretation
                or skip_flags.skip_tools_for_grounded_narrate
                or skip_flags.skip_tools_for_attachment_document
                or skip_flags.skip_tools_for_inactive_agent
                or skip_flags.skip_tools_for_project_sources_content
                or skip_flags.skip_tools_for_session_review
                or small_talk_direct
                or utility_direct
                or web_save_sources_direct
                or project_sources_direct
                or web_post_search_direct
                or attachment_welcome_direct
                or unclear_direct
                or text_task_pure
            )
            and not canvas_operational_update
        )

    @classmethod
    def _append_skip_tool_stage(
        cls,
        *,
        message: str,
        pipeline_stages: list[str],
        skip_flags: ChatTurnPreparationSkipToolFlags,
        grounded_stage: str | None = None,
        canvas_action,
        pre_capability_answer: str | None,
        missing_product_code_answer: str | None,
        ambiguous_period_answer: str | None,
        missing_date_answer: str | None,
        common_chat_operational_answer: str | None,
        routing_disambiguation_answer: str | None,
        learning_term_confirmation_answer: str | None,
        interpretation_without_data_answer: str | None,
        small_talk_direct: str | None,
        utility_direct: str | None,
        web_save_sources_direct: str | None,
        project_sources_direct: str | None,
        web_post_search_direct: str | None,
        attachment_welcome_direct: str | None,
        unclear_direct: str | None,
        text_task_pure: bool,
    ) -> None:
        if skip_flags.skip_tools_for_user_identity:
            pipeline_stages.append("identity_shortcut")
        elif skip_flags.skip_tools_for_assistant_identity:
            pipeline_stages.append("assistant_identity_shortcut")
        elif skip_flags.skip_tools_for_session_review:
            pipeline_stages.append("session_review")
        elif skip_flags.skip_tools_for_grounded_narrate:
            pipeline_stages.append(grounded_stage or "grounded_narrate")
        elif skip_flags.skip_tools_for_data_interpretation:
            pipeline_stages.append("data_interpretation")
        elif canvas_action:
            pipeline_stages.append("canvas")
        elif pre_capability_answer:
            from app.application.services.chat_onboarding_service import (
                ChatOnboardingService,
            )
            from app.application.services.chat_capabilities_service import (
                ChatCapabilitiesService,
            )

            if ChatCapabilitiesService.is_api_action_routes_inquiry(message):
                pipeline_stages.append("api_action_routes")
            elif ChatOnboardingService.is_training_request(message):
                pipeline_stages.append("onboarding_training")
            else:
                pipeline_stages.append("capabilities")
        elif common_chat_operational_answer:
            pipeline_stages.append("common_chat_operational_guidance")
        elif missing_product_code_answer:
            pipeline_stages.append("operational_parameter")
        elif ambiguous_period_answer:
            pipeline_stages.append("operational_parameter")
        elif missing_date_answer:
            pipeline_stages.append("operational_parameter")
        elif learning_term_confirmation_answer:
            pipeline_stages.append("learning_term")
        elif routing_disambiguation_answer:
            pipeline_stages.append("intent_disambiguation")
        elif interpretation_without_data_answer:
            pipeline_stages.append("data_interpretation_empty")
        elif small_talk_direct:
            pipeline_stages.append("small_talk")
        elif utility_direct:
            pipeline_stages.append("utility_direct")
        elif web_save_sources_direct:
            pipeline_stages.append("web_save_sources")
        elif project_sources_direct:
            pipeline_stages.append("project_sources_inventory")
        elif skip_flags.skip_tools_for_project_sources_content:
            pipeline_stages.append("project_sources_content")
        elif web_post_search_direct:
            pipeline_stages.append("web_post_search_follow_up")
        elif attachment_welcome_direct:
            pipeline_stages.append("attachment_welcome")
        elif skip_flags.skip_tools_for_attachment_document:
            pipeline_stages.append("attachment_document")
        elif unclear_direct:
            pipeline_stages.append("unclear_request")
        elif text_task_pure:
            pipeline_stages.append("text_task")
        elif skip_flags.skip_tools_for_inactive_agent:
            pipeline_stages.append("common_chat_no_tools")

    @classmethod
    def run_tool_phase(
        cls,
        *,
        message: str,
        request,
        history_source: list,
        workspace_context: dict,
        conversation_context: str,
        pipeline_stages: list[str],
        pipeline_timings: ChatPipelineTimings,
        canvas_action,
        canvas_operational_update: bool,
        pre_capability_answer: str | None,
        operational_guards: ChatTurnPreparationOperationalGuards,
        routing_disambiguation_answer: str | None,
        learning_term_confirmation_answer: str | None,
        interpretation_without_data_answer: str | None,
        skip_flags: ChatTurnPreparationSkipToolFlags,
        small_talk_direct: str | None,
        utility_direct: str | None,
        web_save_sources_direct: str | None,
        project_sources_direct: str | None,
        web_post_search_direct: str | None,
        attachment_welcome_direct: str | None,
        unclear_direct: str | None,
        text_task_pure: bool,
        fast_path: bool,
        operational_optimize: bool,
        analysis_mode: bool,
        build_tool_context: Callable[..., dict],
        maybe_extend_tool_context: Callable[..., dict],
        max_external_action_calls: int | None,
        on_stream_activity=None,
    ) -> ChatTurnPreparationToolPhaseResult:
        with ChatPipelineTimings.bind(pipeline_timings):
            return cls._run_tool_phase_bound(
                message=message,
                request=request,
                history_source=history_source,
                workspace_context=workspace_context,
                conversation_context=conversation_context,
                pipeline_stages=pipeline_stages,
                pipeline_timings=pipeline_timings,
                canvas_action=canvas_action,
                canvas_operational_update=canvas_operational_update,
                pre_capability_answer=pre_capability_answer,
                operational_guards=operational_guards,
                routing_disambiguation_answer=routing_disambiguation_answer,
                learning_term_confirmation_answer=learning_term_confirmation_answer,
                interpretation_without_data_answer=interpretation_without_data_answer,
                skip_flags=skip_flags,
                small_talk_direct=small_talk_direct,
                utility_direct=utility_direct,
                web_save_sources_direct=web_save_sources_direct,
                project_sources_direct=project_sources_direct,
                web_post_search_direct=web_post_search_direct,
                attachment_welcome_direct=attachment_welcome_direct,
                unclear_direct=unclear_direct,
                text_task_pure=text_task_pure,
                fast_path=fast_path,
                operational_optimize=operational_optimize,
                analysis_mode=analysis_mode,
                build_tool_context=build_tool_context,
                maybe_extend_tool_context=maybe_extend_tool_context,
                max_external_action_calls=max_external_action_calls,
                on_stream_activity=on_stream_activity,
            )

    @classmethod
    def _run_tool_phase_bound(
        cls,
        *,
        message: str,
        request,
        history_source: list,
        workspace_context: dict,
        conversation_context: str,
        pipeline_stages: list[str],
        pipeline_timings: ChatPipelineTimings,
        canvas_action,
        canvas_operational_update: bool,
        pre_capability_answer: str | None,
        operational_guards: ChatTurnPreparationOperationalGuards,
        routing_disambiguation_answer: str | None,
        learning_term_confirmation_answer: str | None,
        interpretation_without_data_answer: str | None,
        skip_flags: ChatTurnPreparationSkipToolFlags,
        small_talk_direct: str | None,
        utility_direct: str | None,
        web_save_sources_direct: str | None,
        project_sources_direct: str | None,
        web_post_search_direct: str | None,
        attachment_welcome_direct: str | None,
        unclear_direct: str | None,
        text_task_pure: bool,
        fast_path: bool,
        operational_optimize: bool,
        analysis_mode: bool,
        build_tool_context: Callable[..., dict],
        maybe_extend_tool_context: Callable[..., dict],
        max_external_action_calls: int | None,
        on_stream_activity=None,
    ) -> ChatTurnPreparationToolPhaseResult:
        if skip_flags.skip_tools_for_attachment_document:
            operational_optimize = False
            analysis_mode = False

        if skip_flags.skip_tools_for_grounded_narrate:
            analysis_mode = True

        if cls.should_skip_tools(
            canvas_action=canvas_action,
            canvas_operational_update=canvas_operational_update,
            pre_capability_answer=pre_capability_answer,
            missing_product_code_answer=operational_guards.missing_product_code_answer,
            ambiguous_period_answer=operational_guards.ambiguous_period_answer,
            missing_date_answer=operational_guards.missing_date_answer,
            common_chat_operational_answer=operational_guards.common_chat_operational_answer,
            routing_disambiguation_answer=routing_disambiguation_answer,
            learning_term_confirmation_answer=learning_term_confirmation_answer,
            interpretation_without_data_answer=interpretation_without_data_answer,
            skip_flags=skip_flags,
            small_talk_direct=small_talk_direct,
            utility_direct=utility_direct,
            web_save_sources_direct=web_save_sources_direct,
            project_sources_direct=project_sources_direct,
            web_post_search_direct=web_post_search_direct,
            attachment_welcome_direct=attachment_welcome_direct,
            unclear_direct=unclear_direct,
            text_task_pure=text_task_pure,
        ):
            cls._append_skip_tool_stage(
                message=message,
                pipeline_stages=pipeline_stages,
                skip_flags=skip_flags,
                grounded_stage=(
                    str((workspace_context.get("turnGrounding") or {}).get("stage") or "").strip()
                    or None
                ),
                canvas_action=canvas_action,
                pre_capability_answer=pre_capability_answer,
                missing_product_code_answer=operational_guards.missing_product_code_answer,
                ambiguous_period_answer=operational_guards.ambiguous_period_answer,
                missing_date_answer=operational_guards.missing_date_answer,
                common_chat_operational_answer=operational_guards.common_chat_operational_answer,
                routing_disambiguation_answer=routing_disambiguation_answer,
                learning_term_confirmation_answer=learning_term_confirmation_answer,
                interpretation_without_data_answer=interpretation_without_data_answer,
                small_talk_direct=small_talk_direct,
                utility_direct=utility_direct,
                web_save_sources_direct=web_save_sources_direct,
                project_sources_direct=project_sources_direct,
                web_post_search_direct=web_post_search_direct,
                attachment_welcome_direct=attachment_welcome_direct,
                unclear_direct=unclear_direct,
                text_task_pure=text_task_pure,
            )
            tool_context: dict[str, Any] = {
                "context": "",
                "toolCalls": [],
                "nativeToolCalling": {},
            }

            if (
                routing_disambiguation_answer
                or operational_guards.missing_product_code_answer
                or operational_guards.ambiguous_period_answer
                or operational_guards.missing_date_answer
            ):
                tool_context["clarifyInsteadOfGuess"] = True

            tool_calls: list = []
            for key in (
                "tools_selection_done",
                "tools_wave1_done",
                "tools_critic_done",
                "tools_wave2_done",
                "tools_assemble_done",
            ):
                pipeline_timings.mark(key)

            if skip_flags.skip_tools_for_attachment_document:
                from app.application.services.chat_document_vision_turn_service import (
                    ChatDocumentVisionTurnService,
                )

                vision_meta, _activation = (
                    ChatDocumentVisionTurnService.run_attachment_vision_with_progress(
                        user_id=str(getattr(request, "user_id", "") or ""),
                        session_id=str(getattr(request, "session_id", "") or ""),
                        attachment_ids=[
                            str(item) for item in skip_flags.request_attachment_ids
                        ],
                        skills=workspace_context.get("skills"),
                        intent_route="attachment_document",
                        has_agent=bool(workspace_context.get("agent")),
                        on_stream_activity=on_stream_activity,
                        message=message,
                    )
                )

                if vision_meta:
                    tool_context["documentVision"] = vision_meta

            pipeline_timings.mark("tools_agentic_done")
            post_tool = ChatIntelligencePipelineService.finalize_after_tools(
                message,
                history_source,
                tool_context,
            )
            tool_context = post_tool.tool_context
            analysis_mode = post_tool.analysis_mode

            if skip_flags.skip_tools_for_grounded_narrate:
                turn_grounding = workspace_context.get("turnGrounding")

                if isinstance(turn_grounding, dict) and turn_grounding:
                    tool_context = dict(tool_context)
                    tool_context["turnGrounding"] = dict(turn_grounding)

                stage = str(turn_grounding.get("stage") or "").strip() if isinstance(turn_grounding, dict) else ""

                if stage == "grounded_narrate_insight":
                    from app.application.services.chat_grounded_insight_answer_service import (
                        ChatGroundedInsightAnswerService,
                    )

                    _, tool_context = ChatGroundedInsightAnswerService.apply_narrate_insight_context(
                        message,
                        history_source,
                        tool_context,
                        workspace_context=workspace_context,
                    )
                    analysis_mode = True
                    tool_context = dict(tool_context)
                    tool_context["requiresDataInterpretationLlm"] = True
                elif stage == "grounded_challenge_result":
                    from app.application.services.chat_follow_up_grounded_answer_service import (
                        ChatFollowUpGroundedAnswerService,
                    )

                    tool_context = ChatFollowUpGroundedAnswerService.inject_challenge_prompt_context(
                        tool_context,
                        workspace_context=workspace_context,
                    )
                    analysis_mode = True
                else:
                    narrate_applied, tool_context = (
                        ChatConversationContextService.apply_grounded_narrate_mode(
                            message,
                            history_source,
                            tool_context,
                            workspace_context=workspace_context,
                        )
                    )

                    if narrate_applied:
                        analysis_mode = True

            pipeline_timings.mark("tools_done")
        else:
            pipeline_stages.append("tools")
            tool_context = build_tool_context(
                request,
                allowed_action_ids=workspace_context.get("allowedActionIds"),
                capabilities=workspace_context.get("capabilities") or {},
                specialization=workspace_context.get("specialization"),
                fast_path=fast_path and not operational_optimize,
                previous_messages=history_source,
                max_external_action_calls=max_external_action_calls,
                on_stream_activity=on_stream_activity,
                # Workspace completo (skills + hostContext TV) — não só agent.
                agent_context=workspace_context,
                working_memory=workspace_context.get("workingMemory"),
            )
            tool_context = maybe_extend_tool_context(
                request=request,
                workspace_context=workspace_context,
                tool_context=tool_context,
                conversation_context=conversation_context,
                previous_messages=history_source,
                on_stream_activity=on_stream_activity,
            )
            pipeline_timings.mark("tools_agentic_done")
            post_tool = ChatIntelligencePipelineService.finalize_after_tools(
                message,
                history_source,
                tool_context,
            )
            tool_context = post_tool.tool_context
            analysis_mode = post_tool.analysis_mode
            tool_calls = tool_context["toolCalls"]
            pipeline_timings.mark("tools_done")

            stage = str(
                (workspace_context.get("turnGrounding") or {}).get("stage") or ""
            ).strip()

            if stage == "grounded_enrich_insight":
                from app.application.services.chat_grounded_insight_answer_service import (
                    ChatGroundedInsightAnswerService,
                )

                _, tool_context = ChatGroundedInsightAnswerService.apply_enrich_context(
                    message,
                    history_source,
                    tool_context,
                    workspace_context=workspace_context,
                )
                analysis_mode = True

        return ChatTurnPreparationToolPhaseResult(
            tool_context=tool_context,
            tool_calls=tool_calls,
            analysis_mode=analysis_mode,
            operational_optimize=operational_optimize,
        )
