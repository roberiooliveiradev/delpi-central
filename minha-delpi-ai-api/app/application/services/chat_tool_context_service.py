import json

from app.application.dto.execute_tool_request import ExecuteToolRequest
from app.application.use_cases.execute_tool_use_case import ExecuteToolUseCase
from app.domain.entities.tool_result import ToolResult
from app.domain.services.chat_external_action_direct_answer_service import (
    ChatExternalActionDirectAnswerService,
)
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.tool_selection_service import ToolSelectionService
from app.infrastructure.config.settings import Settings
from app.domain.services.external_actions.external_action_result_presenter import ExternalActionResultPresenter


class ChatToolContextService:
    def __init__(
        self,
        tool_selection_service: ToolSelectionService,
        execute_tool_use_case: ExecuteToolUseCase,
        external_action_selection_service=None,
        tool_router_service=None,
        external_action_repository=None,
        native_tool_calling_service=None,
    ):
        self.tool_selection_service = tool_selection_service
        self.execute_tool_use_case = execute_tool_use_case
        self.external_action_selection_service = external_action_selection_service
        self.tool_router_service = tool_router_service
        self.external_action_repository = external_action_repository
        self.native_tool_calling_service = native_tool_calling_service
        self.external_action_result_presenter = ExternalActionResultPresenter()

    def build_context(
        self,
        user_id: str,
        access_token: str,
        message: str,
        allowed_action_ids: list[str] | None = None,
        actions_enabled: bool = True,
        allowed_tool_names: list[str] | None = None,
        fast_path: bool = False,
        conversation_context: str | None = None,
        previous_messages: list | None = None,
        max_external_action_calls: int | None = None,
        on_stream_activity=None,
        agent_context: dict | None = None,
        attachment_context: str | None = None,
        attachment_ids: list[str] | None = None,
        session_id: str | None = None,
    ) -> dict:
        if fast_path:
            return {
                "context": "",
                "toolCalls": [],
                "nativeToolCalling": {"used": False, "providerSupports": False},
            }

        from app.application.services.chat_intelligence_pipeline_service import (
            ChatIntelligencePipelineService,
        )

        raw_message = str(message or "").strip()

        from app.application.services.chat_capabilities_service import ChatCapabilitiesService
        from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService

        if ChatCapabilitiesService.is_capability_inquiry(raw_message):
            return self._finalize_tool_context_result(
                message=raw_message,
                previous_messages=previous_messages,
                result={
                    "context": "",
                    "toolCalls": [],
                    "nativeToolCalling": {"used": False, "providerSupports": False},
                    "currentMessage": raw_message,
                },
            )

        agent_metadata = agent_context.get("metadata") if isinstance(agent_context, dict) else None

        from app.application.services.chat_drawing_follow_up_turn_service import (
            ChatDrawingFollowUpTurnService,
        )

        drawing_follow_up_answer = ChatDrawingFollowUpTurnService.resolve_direct_answer(
            raw_message,
            previous_messages=previous_messages,
            attachment_ids=attachment_ids,
        )

        if drawing_follow_up_answer:
            return self._finalize_tool_context_result(
                message=raw_message,
                previous_messages=previous_messages,
                result={
                    "context": "",
                    "toolCalls": [],
                    "nativeToolCalling": {"used": False, "providerSupports": False},
                    "directAnswer": drawing_follow_up_answer,
                    "skipRag": True,
                    "drawingAnalysisMode": True,
                    "currentMessage": raw_message,
                },
            )

        from app.domain.services.chat_drawing_analysis_turn_service import (
            ChatDrawingAnalysisTurnService,
        )
        from app.domain.skills.chat_skill_registry import ChatSkillRegistry

        drawing_runtime_skills = ChatSkillRegistry.resolve_runtime_flags(
            agent_metadata=agent_metadata if isinstance(agent_metadata, dict) else None,
            allowed_action_ids=allowed_action_ids,
            has_agent=bool(agent_context),
        )

        drawing_turn = ChatDrawingAnalysisTurnService.resolve(
            message=raw_message,
            attachment_ids=attachment_ids,
            agent_metadata=agent_metadata if isinstance(agent_metadata, dict) else None,
            skills=drawing_runtime_skills,
            previous_messages=previous_messages,
            attachment_context=attachment_context,
        )

        if drawing_turn and drawing_turn.direct_answer:
            return self._finalize_tool_context_result(
                message=raw_message,
                previous_messages=previous_messages,
                result={
                    "context": "",
                    "toolCalls": [],
                    "nativeToolCalling": {"used": False, "providerSupports": False},
                    "directAnswer": drawing_turn.direct_answer,
                    "skipRag": True,
                    "drawingAnalysisMode": True,
                    "currentMessage": raw_message,
                },
            )

        drawing_analysis_mode = bool(
            drawing_turn and drawing_turn.active and drawing_turn.skill_enabled
        )
        drawing_product_code = drawing_turn.product_code if drawing_turn else None
        drawing_has_pdf = bool(drawing_turn and drawing_turn.has_pdf_attachment)

        drawing_pdf_extract = None

        if drawing_analysis_mode and drawing_has_pdf:
            from app.application.services.chat_document_vision_service import (
                ChatDocumentVisionService,
            )
            from app.application.services.chat_stream_activity_service import (
                ChatStreamActivityService,
            )
            from app.domain.services.chat_drawing_pdf_extraction_service import (
                ChatDrawingPdfExtractionService,
            )

            vision_will_run = ChatDocumentVisionService.should_run_for_drawing(
                drawing_runtime_skills
            )

            if vision_will_run and on_stream_activity:
                ChatStreamActivityService.emit_document_vision_progress(
                    on_stream_activity,
                    phase="start",
                )
                ChatStreamActivityService.emit_document_vision_progress(
                    on_stream_activity,
                    phase="ocr",
                )

            drawing_pdf_extract = {}
            if attachment_context:
                drawing_pdf_extract = (
                    ChatDrawingPdfExtractionService.parse_from_attachment_context(
                        attachment_context
                    )
                    or {}
                )

            drawing_pdf_extract = ChatDocumentVisionService.enrich_drawing_extract(
                drawing_pdf_extract,
                user_id=str(user_id) if user_id else None,
                session_id=session_id,
                attachment_ids=attachment_ids,
                skills=drawing_runtime_skills,
            )

            if (
                drawing_pdf_extract
                and drawing_pdf_extract.get("productCode")
                and not drawing_product_code
            ):
                drawing_product_code = str(drawing_pdf_extract["productCode"])

            if vision_will_run and on_stream_activity and drawing_pdf_extract:
                char_count = int(drawing_pdf_extract.get("charCount") or 0)
                engine = (
                    drawing_pdf_extract.get("extractor")
                    or drawing_pdf_extract.get("visionEngine")
                    or "document_vision"
                )
                ChatStreamActivityService.emit_document_vision_progress(
                    on_stream_activity,
                    phase="complete",
                    engine=str(engine),
                    char_count=char_count,
                )

        if drawing_analysis_mode and on_stream_activity:
            from app.application.services.chat_stream_activity_service import (
                ChatStreamActivityService,
            )

            ChatStreamActivityService.emit_drawing_analysis_progress(
                on_stream_activity,
                has_pdf=drawing_has_pdf,
                phase="start",
            )

        from app.domain.services.chat_sql_query_refinement_service import (
            ChatSqlQueryRefinementService,
        )

        sql_refinement = ChatSqlQueryRefinementService.resolve(
            raw_message,
            previous_messages=previous_messages,
        )

        if sql_refinement and sql_refinement.mode == "show_sql":
            return self._finalize_tool_context_result(
                message=raw_message,
                previous_messages=previous_messages,
                result={
                    "context": "",
                    "toolCalls": [],
                    "nativeToolCalling": {"used": False, "providerSupports": False},
                    "directAnswer": ChatSqlQueryRefinementService.format_show_sql_answer(
                        sql_refinement
                    ),
                    "skipRag": True,
                    "currentMessage": raw_message,
                },
            )

        from app.domain.services.chat_sql_safety_service import ChatSqlSafetyService

        sql_block_answer = ChatSqlSafetyService.blocked_direct_answer(
            raw_message,
            sql=getattr(sql_refinement, "sql", None) if sql_refinement else None,
        )

        if sql_block_answer:
            return self._finalize_tool_context_result(
                message=raw_message,
                previous_messages=previous_messages,
                result={
                    "context": "",
                    "toolCalls": [],
                    "nativeToolCalling": {"used": False, "providerSupports": False},
                    "directAnswer": sql_block_answer,
                    "skipRag": True,
                    "currentMessage": raw_message,
                },
            )

        if conversation_context is None and previous_messages:
            conversation_context = ChatIntelligencePipelineService.build_conversation_context(
                previous_messages,
            )

        message = ChatMessageNormalizationService.normalize_for_matching(raw_message) or raw_message

        from app.domain.services.chat_web_search_intent_service import (
            ChatWebSearchIntentService,
        )

        web_search_exclusive = ChatWebSearchIntentService.blocks_external_action_selection(
            raw_message
        )

        from app.application.services.chat_paginated_external_action_service import (
            ChatPaginatedExternalActionService,
        )

        paginated_service = ChatPaginatedExternalActionService(self.execute_tool_use_case)
        continue_fetch = paginated_service.fetch_continue_plan(
            user_id=user_id,
            access_token=access_token,
            message=raw_message,
            previous_messages=previous_messages,
            on_stream_activity=on_stream_activity,
        )

        if continue_fetch:
            merged_data, merged_metadata, arguments, continue_prompt = continue_fetch
            return self._finalize_paginated_consolidation_result(
                raw_message=raw_message,
                previous_messages=previous_messages,
                merged_data=merged_data,
                merged_metadata=merged_metadata,
                arguments=arguments,
                continue_prompt=continue_prompt,
                reason="Continuação da consulta paginada consolidada.",
            )

        full_fetch = paginated_service.fetch_full_from_history(
            user_id=user_id,
            access_token=access_token,
            message=raw_message,
            previous_messages=previous_messages,
            on_stream_activity=on_stream_activity,
        )

        if full_fetch:
            merged_data, merged_metadata, arguments, continue_prompt = full_fetch
            return self._finalize_paginated_consolidation_result(
                raw_message=raw_message,
                previous_messages=previous_messages,
                merged_data=merged_data,
                merged_metadata=merged_metadata,
                arguments=arguments,
                continue_prompt=continue_prompt,
                reason="Consolidação completa da consulta paginada.",
            )

        native_meta = {"used": False, "providerSupports": False}
        native_selections: list[dict] = []

        if self.native_tool_calling_service:
            native_result = self.native_tool_calling_service.select_tools(
                message=message,
                allowed_tool_names=allowed_tool_names,
                tools_registry=self.execute_tool_use_case.tools,
                agent_context=agent_context,
            )
            native_meta = native_result.get("meta") or native_meta
            native_selections = list(native_result.get("selections") or [])

        if native_selections:
            selected_tools = native_selections
        else:
            selected_tools = self.tool_selection_service.select_tools(
                message,
                attachment_context=attachment_context,
                previous_messages=previous_messages,
            )

        if allowed_tool_names:
            allowed = {str(item).strip() for item in allowed_tool_names if str(item).strip()}
            selected_tools = [
                item for item in selected_tools if str(item.get("name") or "") in allowed
            ]

        router_suggestion = {"tools": [], "actionId": None}

        if (
            self.tool_router_service
            and actions_enabled
            and not native_selections
            and not web_search_exclusive
        ):
            catalog_actions = []

            if self.external_action_repository and allowed_action_ids:
                catalog_actions = self.external_action_repository.find_candidate_actions(
                    message,
                    limit=Settings.CHAT_TOOL_ROUTER_MAX_ACTIONS,
                    allowed_action_ids=allowed_action_ids,
                )

            router_suggestion = self.tool_router_service.suggest(
                message=message,
                allowed_tool_names=allowed_tool_names,
                allowed_actions=catalog_actions,
            )

            for tool_name in router_suggestion.get("tools") or []:
                if any(str(item.get("name")) == tool_name for item in selected_tools):
                    continue

                selected_tools.append(
                    {
                        "name": tool_name,
                        "arguments": {},
                        "reason": "Ferramenta sugerida pelo roteador inteligente do chat.",
                    }
                )

        selected_external_action = None
        selected_external_action_meta = None

        if (
            self.external_action_selection_service
            and actions_enabled
            and not web_search_exclusive
        ):
            from app.application.services.chat_external_action_orchestration_service import (
                ChatExternalActionOrchestrationService,
            )

            if on_stream_activity:
                from app.application.services.chat_stream_activity_service import (
                    ChatStreamActivityService,
                )

                on_stream_activity(
                    ChatStreamActivityService.plan_step(
                        step=1,
                        total=1,
                        target="consultas OpenAPI",
                        verb="Planejando",
                        state="active",
                        detail="Selecionando rotas e parâmetros para a pergunta.",
                    )
                )

            planned_external_actions = ChatExternalActionOrchestrationService.plan_actions(
                self.external_action_selection_service,
                message=message,
                allowed_action_ids=allowed_action_ids or [],
                conversation_context=conversation_context,
                previous_messages=previous_messages,
                max_calls=max_external_action_calls,
                on_stream_activity=on_stream_activity,
            )

            if planned_external_actions:
                selected_tools = [
                    item
                    for item in selected_tools
                    if str(item.get("name") or "") != "execute_external_action"
                ]
                selected_tools.extend(planned_external_actions)
                first = planned_external_actions[0]
                arguments = first.get("arguments") or {}
                selected_external_action = first
                selected_external_action_meta = {
                    "actionId": arguments.get("actionId") or arguments.get("action_id"),
                    "reason": first.get("reason"),
                    "plannedCount": len(planned_external_actions),
                }

        if not selected_tools:
            from app.domain.services.chat_sql_production_query_service import (
                ChatSqlProductionQueryService,
            )

            sql_resolution = ChatSqlProductionQueryService.resolve(message)
            if sql_resolution and sql_resolution.mode == "authoring":
                return self._finalize_tool_context_result(
                    message=raw_message,
                    previous_messages=previous_messages,
                    result={
                        "context": "",
                        "toolCalls": [],
                        "nativeToolCalling": native_meta,
                        "directAnswer": ChatSqlProductionQueryService.format_authoring_answer(
                            sql_resolution
                        ),
                        "skipRag": True,
                        "currentMessage": raw_message,
                    },
                )

        if (
            actions_enabled
            and not web_search_exclusive
            and not selected_external_action
            and router_suggestion.get("actionId")
            and allowed_action_ids
            and str(router_suggestion["actionId"]) in {str(item) for item in allowed_action_ids}
        ):
            from app.domain.services.chat_analysis_intent_service import (
                ChatAnalysisIntentService,
            )
            from app.domain.services.chat_sql_operational_intent_service import (
                ChatSqlOperationalIntentService,
            )
            from app.domain.services.external_actions.external_action_sql_capability_service import (
                ExternalActionSqlCapabilityService,
            )

            router_action_id = str(router_suggestion["actionId"])
            skip_router_action = (
                ChatAnalysisIntentService.is_data_interpretation_request(
                    raw_message,
                    previous_messages,
                )
                or ExternalActionSqlCapabilityService.is_sql_execution_context(
                    action_id=router_action_id,
                )
            )

            if not skip_router_action and not ChatSqlOperationalIntentService.requires_sql_knowledge(message):
                selected_tools.append(
                    {
                        "name": "execute_external_action",
                        "arguments": {
                            "actionId": router_action_id,
                            "body": {"message": message},
                        },
                        "reason": "Action sugerida pelo roteador inteligente do chat.",
                    }
                )

        if not selected_tools:
            return self._finalize_tool_context_result(
                message=raw_message,
                previous_messages=previous_messages,
                result={
                    "context": "",
                    "toolCalls": [],
                    "nativeToolCalling": native_meta,
                    "currentMessage": raw_message,
                },
            )

        context_blocks: list[str] = []
        safe_tool_calls: list[dict] = []
        direct_answer: str | None = None
        skip_rag = False
        last_external_action_data = None
        last_web_search_data: dict | None = None
        web_sources: list[dict] = []
        web_search_payload: dict | None = None
        external_action_results: list = []
        external_planned = [
            item
            for item in selected_tools
            if str(item.get("name") or "") == "execute_external_action"
        ]
        external_total = len(external_planned)
        external_index = 0
        pagination_continue_prompt: str | None = None

        if on_stream_activity and external_total > 0:
            from app.application.services.chat_stream_activity_service import (
                ChatStreamActivityService,
            )

            on_stream_activity(
                ChatStreamActivityService.entry(
                    verb="Executando",
                    target=f"{external_total} consulta(s) DELPI",
                    phase="tools",
                    state="active",
                    message=f"Executando {external_total} consulta(s) à API DELPI...",
                )
            )

        for selected_tool in selected_tools:
            tool_name = str(selected_tool.get("name") or "")
            arguments = selected_tool.get("arguments") or {}
            action_id = str(arguments.get("actionId") or arguments.get("action_id") or "")
            path_hint = str(arguments.get("path") or "")

            if tool_name == "execute_external_action":
                external_index += 1

                if on_stream_activity:
                    from app.application.services.chat_stream_activity_service import (
                        ChatStreamActivityService,
                    )

                    on_stream_activity(
                        ChatStreamActivityService.tool_started(
                            index=external_index,
                            total=external_total,
                            path=path_hint or None,
                            action_id=action_id or None,
                            reason=selected_tool.get("reason"),
                        )
                    )

            if tool_name == "web_search" and on_stream_activity:
                from app.application.services.chat_stream_activity_service import (
                    ChatStreamActivityService,
                )

                search_query = str(arguments.get("query") or raw_message or "").strip()

                on_stream_activity(
                    ChatStreamActivityService.web_search_started(query=search_query)
                )

            if (
                tool_name == "execute_external_action"
                and action_id
                and self.external_action_repository
            ):
                from app.domain.services.chat_write_confirmation_service import (
                    ChatWriteConfirmationService,
                )

                action_bundle = self.external_action_repository.get_action_for_execution(
                    action_id
                )
                action = (action_bundle or {}).get("action") if action_bundle else None

                if ChatWriteConfirmationService.should_block_execution(
                    message=raw_message,
                    action=action,
                ):
                    prompt = ChatWriteConfirmationService.confirmation_prompt(action)
                    direct_answer = direct_answer or prompt
                    skip_rag = True

                    blocked_metadata = {
                        "ok": False,
                        "blocked": True,
                        "blockReason": "confirmation_required",
                        "actionId": action_id,
                        "path": path_hint or str((action or {}).get("path") or ""),
                        "sensitivity": (action or {}).get("sensitivity"),
                    }
                    blocked_metadata["responsePreview"] = self._build_response_preview(
                        blocked_metadata
                    )

                    safe_tool_calls.append(
                        {
                            "name": tool_name,
                            "arguments": arguments,
                            "reason": selected_tool.get("reason"),
                            "metadata": blocked_metadata,
                        }
                    )

                    if on_stream_activity:
                        from app.application.services.chat_stream_activity_service import (
                            ChatStreamActivityService,
                        )

                        on_stream_activity(
                            ChatStreamActivityService.tool_finished(
                                index=external_index,
                                total=external_total,
                                metadata=blocked_metadata,
                                path=blocked_metadata.get("path"),
                                action_id=action_id,
                            )
                        )

                    continue

            try:
                result = self.execute_tool_use_case.execute(
                    ExecuteToolRequest(
                        user_id=user_id,
                        access_token=access_token,
                        tool_name=selected_tool["name"],
                        arguments=selected_tool.get("arguments") or {},
                    )
                )
            except Exception as exc:
                tool_name = selected_tool.get("name") or "unknown_tool"
                error_metadata = {
                    "ok": False,
                    "error": str(exc),
                    "errorType": exc.__class__.__name__,
                }

                if tool_name == "execute_external_action" and on_stream_activity:
                    from app.application.services.chat_stream_activity_service import (
                        ChatStreamActivityService,
                    )

                    on_stream_activity(
                        ChatStreamActivityService.tool_finished(
                            index=external_index,
                            total=external_total,
                            metadata=error_metadata,
                            path=path_hint or None,
                            action_id=action_id or None,
                        )
                    )

                if tool_name == "execute_external_action":
                    error_metadata["responsePreview"] = self._build_response_preview(
                        error_metadata
                    )

                    from app.application.services.chat_composite_direct_answer_service import (
                        ExternalActionExecutionResult,
                    )

                    external_action_results.append(
                        ExternalActionExecutionResult(
                            metadata=error_metadata,
                            data=None,
                            reason=selected_tool.get("reason"),
                        )
                    )

                safe_tool_calls.append(
                    {
                        "name": tool_name,
                        "arguments": selected_tool.get("arguments") or {},
                        "reason": selected_tool.get("reason"),
                        "metadata": error_metadata,
                    }
                )

                context_blocks.append(
                    self._format_tool_error_context(
                        name=tool_name,
                        reason=selected_tool.get("reason"),
                        error=exc,
                    )
                )
                continue

            result_data = result.data
            result_metadata = dict(result.metadata or {})

            if (
                result.name == "execute_external_action"
                and not self._is_successful_external_action(result_metadata)
            ):
                recovery = self._try_sql_error_recovery(
                    user_id=user_id,
                    access_token=access_token,
                    allowed_action_ids=allowed_action_ids,
                    selected_tool=selected_tool,
                    metadata=result_metadata,
                    safe_tool_calls=safe_tool_calls,
                    context_blocks=context_blocks,
                    on_stream_activity=on_stream_activity,
                )

                if recovery:
                    selected_tool = {
                        **selected_tool,
                        "reason": recovery.plan.reason,
                        "arguments": {
                            **(selected_tool.get("arguments") or {}),
                            "body": {
                                "sql": recovery.plan.corrected_sql,
                                "query": recovery.plan.corrected_sql,
                                "statement": recovery.plan.corrected_sql,
                            },
                        },
                    }
                    result_data = recovery.retry_data
                    result_metadata = dict(recovery.retry_metadata)
                    result = ToolResult(
                        name=result.name,
                        data=result_data,
                        metadata=result_metadata,
                    )

            if (
                result.name == "execute_external_action"
                and self._is_successful_external_action(result_metadata)
            ):
                (
                    result_data,
                    result_metadata,
                    pagination_continue_prompt,
                ) = paginated_service.maybe_consolidate(
                    user_id=user_id,
                    access_token=access_token,
                    message=raw_message,
                    previous_messages=previous_messages,
                    base_arguments=selected_tool.get("arguments") or {},
                    base_metadata=result_metadata,
                    base_data=result_data,
                    on_stream_activity=on_stream_activity,
                )
                result = ToolResult(
                    name=result.name,
                    data=result_data,
                    metadata=result_metadata,
                )

            safe_metadata = self._build_safe_tool_metadata(
                tool_name=result.name,
                metadata=result.metadata,
                data=result.data,
            )

            if result.name == "execute_external_action":
                from app.domain.services.external_actions.external_action_sql_capability_service import (
                    ExternalActionSqlCapabilityService,
                )

                executed_sql = ExternalActionSqlCapabilityService.extract_sql_from_arguments(
                    selected_tool.get("arguments")
                )
                if executed_sql:
                    safe_metadata["executedSql"] = executed_sql

            safe_tool_calls.append(
                {
                    "name": result.name,
                    "arguments": selected_tool.get("arguments") or {},
                    "reason": selected_tool.get("reason"),
                    "metadata": safe_metadata,
                }
            )

            if result.name == "execute_external_action":
                skip_rag = True

                if on_stream_activity:
                    from app.application.services.chat_stream_activity_service import (
                        ChatStreamActivityService,
                    )

                    on_stream_activity(
                        ChatStreamActivityService.tool_finished(
                            index=external_index,
                            total=external_total,
                            metadata=safe_metadata,
                            path=str(safe_metadata.get("path") or path_hint or "") or None,
                            action_id=str(safe_metadata.get("actionId") or action_id or "")
                            or None,
                            data=result.data,
                        )
                    )

                from app.application.services.chat_composite_direct_answer_service import (
                    ExternalActionExecutionResult,
                )

                external_action_results.append(
                    ExternalActionExecutionResult(
                        metadata=safe_metadata,
                        data=result.data,
                        reason=selected_tool.get("reason"),
                    )
                )

                if self._is_successful_external_action(safe_metadata):
                    last_external_action_data = result.data

            if result.name == "web_search" and isinstance(result.data, dict):
                if str(result.data.get("searchStatus") or "") in {"success", "no_results"}:
                    last_web_search_data = result.data

                if on_stream_activity:
                    from app.application.services.chat_stream_activity_service import (
                        ChatStreamActivityService,
                    )

                    on_stream_activity(
                        ChatStreamActivityService.web_search_finished(payload=result.data)
                    )

            context_blocks.append(
                self._format_tool_context(
                    name=result.name,
                    reason=selected_tool.get("reason"),
                    data=result.data,
                    metadata=result.metadata,
                    arguments=selected_tool.get("arguments"),
                )
            )

        context = "\n\n".join(context_blocks)
        context = context[: Settings.MAX_CONTEXT_CHARS]

        if external_action_results:
            from app.application.services.chat_composite_direct_answer_service import (
                ChatCompositeDirectAnswerService,
            )

            if not ChatAnalysisIntentService.is_comparison_or_insight_request(raw_message):
                direct_answer = ChatCompositeDirectAnswerService.build(
                    message,
                    external_action_results,
                )

        if isinstance(last_web_search_data, dict):
            from app.domain.services.chat_web_search_erp_cross_reference_service import (
                ChatWebSearchErpCrossReferenceService,
            )
            from app.domain.services.chat_web_search_direct_answer_service import (
                ChatWebSearchDirectAnswerService,
            )

            direct_answer, last_web_search_data = (
                ChatWebSearchErpCrossReferenceService.append_to_direct_answer(
                    direct_answer=direct_answer,
                    internal_data=last_external_action_data,
                    web_payload=last_web_search_data,
                    message=raw_message,
                )
            )
            web_search_payload = last_web_search_data

            if (
                str(last_web_search_data.get("searchStatus") or "") == "success"
                and not web_sources
            ):
                web_sources = ChatWebSearchDirectAnswerService.build_sources(
                    last_web_search_data
                )
                skip_rag = True

        if (
            not direct_answer
            and len(safe_tool_calls) == 1
            and safe_tool_calls[0].get("name") == "execute_external_action"
            and self._is_successful_external_action(safe_tool_calls[0].get("metadata") or {})
        ):
            action_metadata = safe_tool_calls[0].get("metadata") or {}
            action_arguments = safe_tool_calls[0].get("arguments") or {}
            direct_answer = self._build_direct_answer(
                self._attach_request_sql(
                    last_external_action_data,
                    action_arguments,
                    action_metadata,
                ),
                message=message,
                path=action_metadata.get("path"),
                operation_id=action_metadata.get("operationId"),
            )

        if (
            not direct_answer
            and len(safe_tool_calls) == 1
            and safe_tool_calls[0].get("name") == "web_search"
            and isinstance(last_web_search_data, dict)
        ):
            from app.domain.services.chat_web_search_direct_answer_service import (
                ChatWebSearchDirectAnswerService,
            )

            direct_answer = ChatWebSearchDirectAnswerService.format(
                last_web_search_data,
                message=raw_message,
            )

            if direct_answer:
                skip_rag = True
                web_sources = ChatWebSearchDirectAnswerService.build_sources(
                    last_web_search_data
                )
                web_search_payload = last_web_search_data

        requested_format = self._resolve_consolidation_format(raw_message, previous_messages)
        if requested_format:
            self._apply_format_override(safe_tool_calls, requested_format, last_external_action_data)

        if direct_answer and requested_format != "table":
            self._suppress_redundant_structure_presentations(safe_tool_calls)

        if direct_answer and requested_format != "text":
            direct_answer = self._compact_direct_answer_for_rich_presentation(
                direct_answer,
                safe_tool_calls,
            )

        if pagination_continue_prompt:
            direct_answer = (
                f"{direct_answer}\n\n{pagination_continue_prompt}".strip()
                if direct_answer
                else pagination_continue_prompt
            )

        drawing_analysis_payload = None

        if drawing_analysis_mode:
            drawing_analysis_payload = self._build_drawing_analysis_enrichment(
                safe_tool_calls=safe_tool_calls,
                product_code=drawing_product_code,
                has_pdf_attachment=drawing_has_pdf,
                direct_answer=direct_answer,
                pdf_extract=drawing_pdf_extract,
            )

            if drawing_analysis_payload:
                direct_answer = drawing_analysis_payload.get("directAnswer") or direct_answer

            if drawing_analysis_mode and on_stream_activity:
                from app.application.services.chat_stream_activity_service import (
                    ChatStreamActivityService,
                )

                ChatStreamActivityService.emit_drawing_analysis_progress(
                    on_stream_activity,
                    has_pdf=drawing_has_pdf,
                    phase="complete",
                )

        result_payload = {
            "context": context,
            "toolCalls": safe_tool_calls,
            "nativeToolCalling": native_meta,
            "directAnswer": direct_answer,
            "skipRag": skip_rag,
            "webSources": web_sources,
            "webSearchPayload": web_search_payload,
            "selectedExternalAction": selected_external_action_meta,
            "currentMessage": raw_message,
        }

        if drawing_analysis_mode:
            result_payload["drawingAnalysisMode"] = True

            if drawing_pdf_extract:
                result_payload["drawingPdfExtractSummary"] = {
                    "productCode": drawing_pdf_extract.get("productCode"),
                    "revision": drawing_pdf_extract.get("revision"),
                    "legible": drawing_pdf_extract.get("legible"),
                    "charCount": drawing_pdf_extract.get("charCount"),
                    "componentCount": len(drawing_pdf_extract.get("componentCodes") or []),
                    "reason": drawing_pdf_extract.get("reason"),
                    "extractor": drawing_pdf_extract.get("extractor"),
                    "documentVision": drawing_pdf_extract.get("documentVision"),
                }

                if drawing_pdf_extract.get("documentVision"):
                    result_payload["documentVision"] = drawing_pdf_extract["documentVision"]

            if drawing_analysis_payload and drawing_analysis_payload.get("drawingAnalysis"):
                result_payload["drawingAnalysis"] = drawing_analysis_payload["drawingAnalysis"]

            if drawing_analysis_payload and drawing_analysis_payload.get("drawingAnalysisExport"):
                result_payload["drawingAnalysisExport"] = drawing_analysis_payload[
                    "drawingAnalysisExport"
                ]

        return self._finalize_tool_context_result(
            message=raw_message,
            previous_messages=previous_messages,
            result=result_payload,
        )


    def _finalize_tool_context_result(
        self,
        *,
        message: str,
        previous_messages: list | None,
        result: dict,
    ) -> dict:
        from app.application.services.chat_intelligence_pipeline_service import (
            ChatIntelligencePipelineService,
        )

        post_tool = ChatIntelligencePipelineService.finalize_after_tools(
            message,
            previous_messages,
            result,
        )
        finalized = post_tool.tool_context

        return finalized

    @classmethod
    def _rich_presentation_from_metadata(cls, metadata: dict) -> dict | None:
        for key in (
            "presentation",
            "tablePresentation",
            "treePresentation",
            "chartPresentation",
        ):
            presentation = metadata.get(key)

            if isinstance(presentation, dict):
                presentation_type = str(presentation.get("type") or "").strip().lower()

                if presentation_type in {"table", "chart", "kpi", "tree"}:
                    return presentation

        return None

    @classmethod
    def _external_action_tool_calls(cls, safe_tool_calls: list[dict]) -> list[dict]:
        return [
            tool_call
            for tool_call in safe_tool_calls
            if str(tool_call.get("name") or "") == "execute_external_action"
        ]

    @classmethod
    def _successful_external_action_tool_calls(cls, safe_tool_calls: list[dict]) -> list[dict]:
        successful: list[dict] = []

        for tool_call in cls._external_action_tool_calls(safe_tool_calls):
            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict):
                continue

            if not metadata.get("ok"):
                continue

            successful.append(tool_call)

        return successful

    @classmethod
    def should_answer_with_presentation_only(cls, safe_tool_calls: list[dict]) -> bool:
        external_calls = cls._external_action_tool_calls(safe_tool_calls)

        if not external_calls:
            return False

        if len(cls._successful_external_action_tool_calls(safe_tool_calls)) != len(
            external_calls
        ):
            return False

        return cls._has_rich_presentation(safe_tool_calls)

    @classmethod
    def prefer_presentation_direct_answer(
        cls,
        direct_answer: str | None,
        safe_tool_calls: list[dict],
    ) -> str | None:
        """Resposta curta quando a UI rica já exibe tabela/gráfico/KPI (11.4.1)."""

        if not cls.should_answer_with_presentation_only(safe_tool_calls):
            return direct_answer

        presentation = cls.resolve_presentation_only_answer(safe_tool_calls)

        if not presentation:
            return direct_answer

        continuation = cls._extract_pagination_continuation_suffix(direct_answer)

        if continuation:
            return f"{presentation}\n\n{continuation}".strip()

        normalized = str(direct_answer or "").strip()

        if normalized and normalized != presentation:
            looks_tabular = "|" in normalized or normalized.count("\n") > 6

            if not looks_tabular and (
                "\n" in normalized or len(normalized) > len(presentation) + 30
            ):
                return normalized

        return presentation

    @classmethod
    def _extract_pagination_continuation_suffix(cls, direct_answer: str | None) -> str | None:
        if not direct_answer:
            return None

        marker = "**Deseja que eu continue buscando?**"

        if marker not in direct_answer:
            return None

        start = direct_answer.rfind("Consolidei", 0, direct_answer.index(marker))

        if start >= 0:
            return direct_answer[start:].strip()

        return direct_answer[direct_answer.index(marker) :].strip()

    @classmethod
    def resolve_presentation_only_answer(cls, safe_tool_calls: list[dict]) -> str | None:
        if not cls.should_answer_with_presentation_only(safe_tool_calls):
            return None

        titles = cls._presentation_titles(safe_tool_calls)

        if not titles:
            return "Consulta concluída."

        if len(titles) == 1:
            return titles[0]

        return "\n".join(f"- {title}" for title in titles)

    @classmethod
    def _has_rich_presentation(cls, safe_tool_calls: list[dict]) -> bool:
        for tool_call in safe_tool_calls:
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict):
                continue

            if cls._rich_presentation_from_metadata(metadata):
                return True

        return False

    @classmethod
    def _presentation_titles(cls, safe_tool_calls: list[dict]) -> list[str]:
        titles: list[str] = []

        for tool_call in safe_tool_calls:
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict):
                continue

            presentation = cls._rich_presentation_from_metadata(metadata)

            if not presentation:
                continue

            title = str(presentation.get("title") or "").strip()

            if title and title not in titles:
                titles.append(title)

        return titles

    @classmethod
    def _compact_direct_answer_for_rich_presentation(
        cls,
        direct_answer: str | None,
        safe_tool_calls: list[dict],
    ) -> str | None:
        """Evita repetir em markdown o mesmo conteúdo já exibido em tabela/gráfico/KPI."""

        if not direct_answer or not cls._has_rich_presentation(safe_tool_calls):
            return direct_answer

        normalized = str(direct_answer).strip()

        if not normalized:
            return None

        if (
            len(normalized) <= 180
            and "|" not in normalized
            and normalized.count("\n") <= 3
        ):
            return normalized

        titles = cls._presentation_titles(safe_tool_calls)

        if titles:
            if len(titles) == 1:
                return titles[0]

            return "\n".join(f"- {title}" for title in titles)

        return None

    @classmethod
    def _suppress_redundant_structure_presentations(cls, safe_tool_calls: list[dict]) -> None:
        """Evita card de tabela duplicado quando o markdown da resposta direta já traz as tabelas."""

        for tool_call in safe_tool_calls:
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict):
                continue

            path = str(metadata.get("path") or "").lower()

            if "/structure" not in path and "/analyser" not in path:
                continue

            available_formats = metadata.get("availableFormats") or []

            if "tree" in available_formats:
                continue

            presentation = metadata.get("presentation")

            if isinstance(presentation, dict) and presentation.get("type") == "table":
                metadata["presentation"] = None

            if metadata.get("tablePresentation"):
                metadata["tablePresentation"] = None

    _FORMAT_TABLE_HINTS = (
        "em tabela", "formato tabela", "em formato de tabela",
        "mostra em tabela", "mostre em tabela", "como tabela",
        "exibir tabela", "exiba em tabela",
        "tabela completa", "lista em tabela", "listagem em tabela",
        "completa em tabela", "completo em tabela",
    )
    _FORMAT_CHART_HINTS = (
        "em gráfico", "em grafico", "formato gráfico", "formato grafico",
        "como gráfico", "como grafico", "mostra em gráfico", "mostre em gráfico",
        "em formato de gráfico", "exibir gráfico", "exiba em gráfico",
    )
    _FORMAT_TEXT_HINTS = (
        "em texto", "formato texto", "sem tabela", "sem gráfico",
        "só texto", "so texto", "apenas texto", "formato simples",
        "resumo", "resumido",
    )
    _FORMAT_TREE_HINTS = (
        "em árvore", "em arvore", "formato árvore", "formato arvore",
        "como árvore", "como arvore", "visualização em árvore",
        "visualizacao em arvore", "mostra em árvore", "mostre em árvore",
        "diagrama hierárquico", "diagrama hierarquico",
        "arvore completa", "árvore completa", "completa em arvore",
        "completa em árvore",
    )

    def _resolve_consolidation_format(
        self,
        message: str,
        previous_messages: list | None,
    ) -> str | None:
        requested_format = self._detect_requested_format(message)

        if requested_format:
            return requested_format

        from app.domain.services.chat_pagination_consolidation_service import (
            ChatPaginationConsolidationService,
        )

        return ChatPaginationConsolidationService.collect_last_preferred_format(
            previous_messages,
        )

    def _finalize_paginated_consolidation_result(
        self,
        *,
        raw_message: str,
        previous_messages: list | None,
        merged_data,
        merged_metadata: dict,
        arguments: dict,
        continue_prompt: str | None,
        reason: str,
    ) -> dict:
        safe_metadata = self._build_safe_tool_metadata(
            "execute_external_action",
            merged_metadata,
            merged_data,
        )
        safe_tool_calls = [
            {
                "name": "execute_external_action",
                "arguments": arguments,
                "reason": reason,
                "metadata": safe_metadata,
            }
        ]
        direct_answer = self._build_direct_answer(
            self._attach_request_sql(merged_data, arguments, safe_metadata),
            message=raw_message,
            path=safe_metadata.get("path"),
            operation_id=safe_metadata.get("operationId"),
        )

        requested_format = self._resolve_consolidation_format(raw_message, previous_messages)

        if requested_format:
            self._apply_format_override(
                safe_tool_calls,
                requested_format,
                merged_data,
            )

        if direct_answer and requested_format != "table":
            self._suppress_redundant_structure_presentations(safe_tool_calls)

        if direct_answer and requested_format != "text":
            direct_answer = self._compact_direct_answer_for_rich_presentation(
                direct_answer,
                safe_tool_calls,
            )

        if continue_prompt:
            direct_answer = (
                f"{direct_answer}\n\n{continue_prompt}".strip()
                if direct_answer
                else continue_prompt
            )

        return self._finalize_tool_context_result(
            message=raw_message,
            previous_messages=previous_messages,
            result={
                "context": self._format_tool_context(
                    "execute_external_action",
                    reason,
                    merged_data,
                    merged_metadata,
                ),
                "toolCalls": safe_tool_calls,
                "nativeToolCalling": {"used": False, "providerSupports": False},
                "directAnswer": direct_answer,
                "skipRag": True,
                "currentMessage": raw_message,
            },
        )

    def _detect_requested_format(self, message: str) -> str | None:
        """Detecta se o usuário pediu um formato específico de apresentação."""
        lowered = (message or "").lower()
        if any(h in lowered for h in self._FORMAT_TEXT_HINTS):
            return "text"
        if any(h in lowered for h in self._FORMAT_TREE_HINTS):
            return "tree"
        if any(h in lowered for h in self._FORMAT_TABLE_HINTS):
            return "table"
        if any(h in lowered for h in self._FORMAT_CHART_HINTS):
            return "chart"
        return None

    def _apply_format_override(
        self,
        safe_tool_calls: list[dict],
        requested_format: str,
        last_data,
    ) -> None:
        """Sobrescreve a presentation com base no formato solicitado pelo usuário."""
        for tc in safe_tool_calls:
            if tc.get("name") != "execute_external_action":
                continue
            meta = tc.get("metadata")
            if not meta or not meta.get("ok"):
                continue

            if requested_format == "text":
                meta["preferredFormat"] = "text"

            elif requested_format == "tree":
                meta["preferredFormat"] = "tree"
                tree_pres = meta.get("treePresentation") or meta.get("presentation")
                if tree_pres and tree_pres.get("type") == "tree":
                    meta["presentation"] = tree_pres
                    meta["treePresentation"] = None
                elif last_data:
                    path = meta.get("path") or ""
                    forced_tree = self.external_action_result_presenter.build_tree_presentation(
                        last_data, path=path
                    )
                    if forced_tree:
                        meta["presentation"] = forced_tree
                        meta["treePresentation"] = None

            elif requested_format == "table":
                meta["preferredFormat"] = "table"
                table_pres = meta.get("tablePresentation") or meta.get("presentation")
                if table_pres and table_pres.get("type") == "table":
                    meta["presentation"] = table_pres
                    meta["tablePresentation"] = None
                elif last_data:
                    path = meta.get("path") or ""
                    forced_table = self.external_action_result_presenter.build_presentation(
                        last_data, path=path
                    )
                    if forced_table:
                        meta["presentation"] = forced_table
                        meta["tablePresentation"] = None

            elif requested_format == "chart":
                meta["preferredFormat"] = "chart"
                chart_pres = meta.get("presentation")
                if chart_pres and chart_pres.get("type") == "chart":
                    pass
                elif last_data:
                    path = meta.get("path") or ""
                    forced_chart = self.external_action_result_presenter.build_chart_presentation(
                        last_data, path=path, force=True
                    )
                    if forced_chart:
                        meta["presentation"] = forced_chart
                        meta["tablePresentation"] = None

    def _build_safe_tool_metadata(
        self,
        tool_name: str,
        metadata: dict | None,
        data,
    ) -> dict:
        safe_metadata = dict(metadata or {})

        if tool_name == "execute_external_action":
            safe_metadata["responsePreview"] = self._build_response_preview(data)
            path = str(safe_metadata.get("path") or "")
            humanized = self.external_action_result_presenter.present(
                self._attach_request_sql(data, None, safe_metadata),
                path=path,
            )

            if isinstance(humanized, dict):
                linhas = [
                    str(line).strip()
                    for line in (humanized.get("linhas") or [])
                    if str(line or "").strip()
                ]

                if humanized.get("titulo") or linhas:
                    safe_metadata["humanizedSummary"] = {
                        "titulo": humanized.get("titulo"),
                        "linhas": linhas,
                    }

        return safe_metadata

    def _build_response_preview(self, data, max_chars: int = 12000) -> str:
        if data is None:
            return ""

        try:
            text = json.dumps(data, ensure_ascii=False, indent=2)
        except (TypeError, ValueError):
            text = str(data)

        if len(text) <= max_chars:
            return text

        return f"{text[:max_chars]}\n…"

    def _format_tool_error_context(self, name: str, reason: str | None, error: Exception) -> str:
        payload = {
            "tool": name,
            "reason": reason,
            "ok": False,
            "errorType": error.__class__.__name__,
            "error": str(error),
        }

        return (
            f"[Ferramenta autorizada com erro: {name}]\n"
            "A ferramenta foi selecionada, mas não conseguiu retornar dados.\n"
            "Regra obrigatória: não invente o resultado. Explique o erro em português simples e peça apenas os parâmetros faltantes quando aplicável.\n"
            f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
        )

    def _is_external_action_allowed(
        self,
        selected_external_action: dict,
        allowed_action_ids: list[str] | None,
    ) -> bool:
        if not allowed_action_ids:
            return False

        action_id = (
            selected_external_action.get("arguments", {}).get("actionId")
            or selected_external_action.get("arguments", {}).get("action_id")
            or selected_external_action.get("actionId")
            or selected_external_action.get("action_id")
        )

        if not action_id:
            return False

        return str(action_id) in {str(item) for item in allowed_action_ids}

    def _format_tool_context(
        self,
        name: str,
        reason: str | None,
        data,
        metadata: dict | None,
        arguments: dict | None = None,
    ) -> str:
        if name == "execute_external_action":
            return self._format_external_action_context(
                reason=reason,
                data=data,
                metadata=metadata or {},
                arguments=arguments,
            )

        payload = {
            "tool": name,
            "reason": reason,
            "metadata": metadata or {},
            "authorizedResult": data,
        }

        return (
            f"[Ferramenta autorizada: {name}]\n"
            f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
        )

    def _format_external_action_context(
        self,
        reason: str | None,
        data,
        metadata: dict,
        arguments: dict | None = None,
    ) -> str:
        status_code = metadata.get("statusCode")
        ok = metadata.get("ok")
        action_id = metadata.get("actionId")
        path = metadata.get("path")
        provider = metadata.get("provider")

        humanized = self.external_action_result_presenter.present(
            self._attach_request_sql(data, arguments, metadata),
            path=path or "",
        )

        linhas = list(humanized.get("linhas") or [])
        coverage = metadata.get("dataCoverageNotice")

        if isinstance(coverage, dict) and coverage.get("message"):
            linhas.append(str(coverage["message"]))

        payload = {
            "tool": "execute_external_action",
            "reason": reason,
            "provider": provider,
            "actionId": action_id,
            "path": path,
            "statusCode": status_code,
            "ok": ok,
            "humanizedSummary": {
                "titulo": humanized.get("titulo"),
                "linhas": linhas,
            },
        }

        return (
            "[Ferramenta autorizada: execute_external_action]\n"
            "A API externa/interna foi consultada com o token autorizado do usuário.\n"
            f"Provider: {provider}\n"
            f"Action: {action_id}\n"
            f"Path: {path}\n"
            f"Status HTTP: {status_code}\n"
            f"Sucesso: {ok}\n"
            "Regra obrigatória: responda ao usuário em português natural, sem mostrar JSON bruto.\n"
            "Use o resumo humanizado como fonte principal.\n"
            "Se precisar de algum dado técnico, use apenas o resumo técnico compacto.\n"
            f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
        )

    def _is_successful_external_action(self, metadata: dict) -> bool:
        if not metadata.get("ok"):
            return False

        status_code = metadata.get("statusCode")

        try:
            return 200 <= int(status_code) < 300
        except (TypeError, ValueError):
            return False

    def _attach_request_sql(
        self,
        data,
        arguments: dict | None = None,
        metadata: dict | None = None,
    ):
        from app.domain.services.external_actions.external_action_sql_capability_service import (
            ExternalActionSqlCapabilityService,
        )

        return ExternalActionSqlCapabilityService.attach_request_sql_to_data(
            data,
            arguments=arguments,
            metadata=metadata,
        )

    def _build_drawing_analysis_enrichment(
        self,
        *,
        safe_tool_calls: list[dict],
        product_code: str | None,
        has_pdf_attachment: bool,
        direct_answer: str | None,
        pdf_extract: dict | None = None,
    ) -> dict | None:
        from app.domain.services.chat_drawing_validation_orchestration_service import (
            ChatDrawingValidationOrchestrationService,
        )

        code = str(product_code or "").strip()

        for tool_call in self._successful_external_action_tool_calls(safe_tool_calls):
            metadata = tool_call.get("metadata") or {}
            path = str(metadata.get("path") or "")

            if "/analyser" not in path.lower():
                continue

            if not code:
                arguments = tool_call.get("arguments") or {}
                code = str(arguments.get("code") or arguments.get("productCode") or "").strip()

            data = tool_call.get("data")

            if data is None:
                data = metadata.get("authorizedResult") or metadata.get("data")

            root = data.get("data", data) if isinstance(data, dict) else {}

            if isinstance(root, dict) and isinstance(root.get("data"), dict):
                root = root["data"]

            package = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
                product_code=code or "—",
                payload=root if isinstance(root, dict) else None,
                has_pdf_attachment=has_pdf_attachment,
                api_ok=bool(metadata.get("ok")),
                api_status_code=metadata.get("statusCode"),
                pdf_extract=pdf_extract,
            )

            report_markdown = ChatDrawingValidationOrchestrationService.format_report_markdown(
                package
            )

            from app.application.services.chat_drawing_report_export_service import (
                ChatDrawingReportExportService,
            )

            export_payload = ChatDrawingReportExportService.build_export_payload(
                package=package,
                report_markdown=report_markdown,
            )

            return {
                "directAnswer": ChatDrawingValidationOrchestrationService.wrap_direct_answer(
                    str(direct_answer or ""),
                    package=package,
                ),
                "drawingAnalysis": package.get("drawingAnalysis"),
                "drawingAnalysisExport": export_payload,
            }

        return None

    def _build_direct_answer(
        self,
        data,
        *,
        message: str,
        path: str | None = None,
        operation_id: str | None = None,
    ) -> str | None:
        if not Settings.CHAT_EXTERNAL_ACTION_DIRECT_RESPONSE_ENABLED:
            return None

        humanized = self.external_action_result_presenter.present(data, path=path or "")

        return ChatExternalActionDirectAnswerService.format(
            humanized,
            message=message,
            path=path,
            operation_id=operation_id,
        )

    def _extract_external_action_summary(self, data):
        if not isinstance(data, dict):
            return data

        root = data.get("data", data)

        if isinstance(root, dict) and "data" in root and isinstance(root["data"], dict):
            root = root["data"]

        summary = {}

        product = root.get("product") if isinstance(root, dict) else None
        if isinstance(product, dict):
            summary["product"] = {
                "code": product.get("code"),
                "description": product.get("description"),
                "type": product.get("type"),
                "unit": product.get("unit"),
                "groupCode": product.get("group_code"),
                "active": product.get("active"),
                "defaultWarehouse": product.get("default_warehouse"),
                "lastPurchasePrice": product.get("last_purchase_price"),
                "standardCost": product.get("standard_cost"),
                "lastRevisionDate": product.get("last_revision_date"),
                "ncm": product.get("ncm_ipi_position"),
            }

        stock = root.get("stock") if isinstance(root, dict) else None
        if isinstance(stock, dict):
            summary["stock"] = self._summarize_items(stock.get("items"))

        items = root.get("items") if isinstance(root, dict) else None
        if isinstance(items, list):
            summary["items"] = self._summarize_items(items)

        for key in ["guide", "inspection", "structure", "customers", "suppliers"]:
            value = root.get(key) if isinstance(root, dict) else None
            if isinstance(value, dict):
                summary[key] = {
                    "total": value.get("total"),
                    "items": self._summarize_items(value.get("items")),
                }

        if not summary:
            return root

        return summary

    def _summarize_items(self, items):
        if not isinstance(items, list):
            return []

        return items[:10]

    def _try_sql_error_recovery(
        self,
        *,
        user_id: str,
        access_token: str,
        allowed_action_ids: list[str] | None,
        selected_tool: dict,
        metadata: dict,
        safe_tool_calls: list[dict],
        context_blocks: list[str],
        on_stream_activity=None,
    ):
        if not self.external_action_repository or not allowed_action_ids:
            return None

        from app.application.services.chat_sql_recovery_service import (
            ChatSqlRecoveryService,
        )

        recovery_service = ChatSqlRecoveryService(
            self.execute_tool_use_case,
            self.external_action_repository,
        )
        recovery = recovery_service.maybe_recover(
            user_id=user_id,
            access_token=access_token,
            allowed_action_ids=allowed_action_ids,
            arguments=selected_tool.get("arguments") or {},
            metadata=metadata,
            reason=selected_tool.get("reason"),
            on_stream_activity=on_stream_activity,
        )

        if not recovery:
            return None

        failed_metadata = self._build_safe_tool_metadata(
            tool_name="execute_external_action",
            metadata=recovery.failed_metadata,
            data=None,
        )
        safe_tool_calls.append(
            {
                "name": "execute_external_action",
                "arguments": recovery.failed_arguments,
                "reason": selected_tool.get("reason"),
                "metadata": failed_metadata,
            }
        )
        context_blocks.append(
            self._format_tool_context(
                name="execute_external_action",
                reason=selected_tool.get("reason"),
                data=None,
                metadata=recovery.failed_metadata,
            )
        )

        schema_metadata = self._build_safe_tool_metadata(
            tool_name="execute_external_action",
            metadata=recovery.schema_metadata,
            data=recovery.schema_data,
        )
        safe_tool_calls.append(
            {
                "name": "execute_external_action",
                "arguments": {
                    "parameters": {"tableName": recovery.plan.table_name},
                },
                "reason": (
                    f"Schema da tabela {recovery.plan.table_name} consultado para "
                    "corrigir colunas inválidas no SQL."
                ),
                "metadata": schema_metadata,
            }
        )
        context_blocks.append(
            self._format_tool_context(
                name="execute_external_action",
                reason=(
                    f"Schema da tabela {recovery.plan.table_name} consultado para "
                    "corrigir colunas inválidas no SQL."
                ),
                data=recovery.schema_data,
                metadata=recovery.schema_metadata,
            )
        )

        return recovery
