"""Preparação do turno antes de seleção/execução de tools — Fase 3C lote 13."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from app.application.services.chat_tool_context_content_service import (
    ChatToolContextContentService,
)
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)

if TYPE_CHECKING:
    from app.application.services.chat_paginated_external_action_service import (
        ChatPaginatedExternalActionService,
    )
    from app.application.services.chat_tool_context_service import ChatToolContextService


@dataclass
class ToolTurnPreparation:
    early_result: dict | None = None
    raw_message: str = ""
    message: str = ""
    conversation_context: str | None = None
    web_search_exclusive: bool = False
    drawing_analysis_mode: bool = False
    drawing_product_code: str | None = None
    drawing_product_codes: tuple[str, ...] = ()
    drawing_product_code_source: str | None = None
    drawing_has_pdf: bool = False
    drawing_pdf_extract: dict | None = None
    drawing_library_fetch: dict | None = None
    drawing_runtime_skills: dict | None = None
    paginated_service: ChatPaginatedExternalActionService | None = None


class ChatToolContextPreTurnService:
    def prepare_turn(
        self,
        host: ChatToolContextService,
        *,
        user_id: str,
        access_token: str,
        message: str,
        allowed_action_ids: list[str] | None,
        actions_enabled: bool,
        conversation_context: str | None,
        previous_messages: list | None,
        on_stream_activity,
        agent_context: dict | None,
        working_memory: dict | None,
        attachment_context: str | None,
        attachment_ids: list[str] | None,
        session_id: str | None,
    ) -> ToolTurnPreparation:
        from app.application.services.chat_intelligence_pipeline_service import (
            ChatIntelligencePipelineService,
        )

        raw_message = str(message or "").strip()
        workspace = dict(host._resolve_workspace_context(agent_context) or {})
        workspace["actionsEnabled"] = bool(actions_enabled)
        workspace["allowedActionIds"] = list(allowed_action_ids or [])

        memory = working_memory

        if not isinstance(memory, dict) and isinstance(agent_context, dict):
            memory = agent_context.get("workingMemory")

        if isinstance(memory, dict):
            workspace["workingMemory"] = memory

        user_context_items = (
            list(memory.get("userContextItems") or [])
            if isinstance(memory, dict)
            else None
        )

        host._build_workspace_context = workspace

        from app.application.services.chat_capabilities_service import ChatCapabilitiesService

        if ChatCapabilitiesService.is_capability_inquiry(raw_message):
            return ToolTurnPreparation(
                early_result=host._finalize_tool_context_result(
                    message=raw_message,
                    previous_messages=previous_messages,
                    result={
                        "context": "",
                        "toolCalls": [],
                        "nativeToolCalling": {"used": False, "providerSupports": False},
                        "currentMessage": raw_message,
                    },
                ),
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
            return ToolTurnPreparation(
                early_result=host._finalize_tool_context_result(
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
                ),
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
            user_context_items=user_context_items,
        )

        if drawing_turn and drawing_turn.direct_answer:
            return ToolTurnPreparation(
                early_result=host._finalize_tool_context_result(
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
                ),
            )

        drawing_analysis_mode = bool(
            drawing_turn and drawing_turn.active and drawing_turn.skill_enabled
        )
        drawing_product_code = drawing_turn.product_code if drawing_turn else None
        drawing_product_codes = drawing_turn.product_codes if drawing_turn else ()
        drawing_product_code_source = (
            drawing_turn.product_code_source if drawing_turn else None
        )
        drawing_has_pdf = bool(drawing_turn and drawing_turn.has_pdf_attachment)
        drawing_pdf_extract = None
        drawing_library_fetch = None

        if (
            drawing_analysis_mode
            and not drawing_has_pdf
            and drawing_product_code
        ):
            from app.application.services.chat_stream_activity_service import (
                ChatStreamActivityService,
            )
            from app.domain.services.chat_drawing_library_service import (
                ChatDrawingLibraryService,
            )

            if on_stream_activity:
                on_stream_activity(
                    ChatStreamActivityService.drawing_analysis_step(
                        step_key="fetch_library_pdf",
                        message=ChatStreamActivityService.drawing_stage_message(
                            "fetch_library_pdf"
                        )
                        or "Buscando desenho na biblioteca corporativa…",
                        state="active",
                    )
                )

            library_result = ChatDrawingLibraryService.fetch_pdf(
                product_code=drawing_product_code,
                access_token=access_token,
            )

            if library_result:
                drawing_has_pdf = True
                drawing_library_fetch = {
                    "productCode": library_result.product_code,
                    "filename": library_result.filename,
                    "storagePath": library_result.storage_path,
                    "source": library_result.source,
                    "metadata": library_result.metadata,
                }
            elif drawing_turn and drawing_turn.requires_pdf:
                from app.domain.services.chat_drawing_intent_service import (
                    ChatDrawingIntentService,
                )

                return ToolTurnPreparation(
                    early_result=host._finalize_tool_context_result(
                        message=raw_message,
                        previous_messages=previous_messages,
                        result={
                            "context": "",
                            "toolCalls": [],
                            "nativeToolCalling": {
                                "used": False,
                                "providerSupports": False,
                            },
                            "directAnswer": ChatDrawingIntentService.build_drawing_library_not_found_answer(
                                drawing_product_code
                            ),
                            "skipRag": True,
                            "drawingAnalysisMode": True,
                            "currentMessage": raw_message,
                        },
                    ),
                )

        if drawing_analysis_mode and drawing_has_pdf:
            from app.application.services.chat_document_vision_turn_service import (
                ChatDocumentVisionTurnService,
            )
            from app.application.services.chat_stream_activity_service import (
                ChatStreamActivityService,
            )
            from app.domain.services.chat_drawing_pdf_extraction_service import (
                ChatDrawingPdfExtractionService,
            )

            if on_stream_activity:
                ChatStreamActivityService.emit_drawing_analysis_progress(
                    on_stream_activity,
                    has_pdf=drawing_has_pdf,
                    phase="start",
                )

            drawing_pdf_extract = {}

            if drawing_library_fetch:
                drawing_pdf_extract, _vision_activation = (
                    ChatDocumentVisionTurnService.run_drawing_vision_from_storage_path(
                        parsed=drawing_pdf_extract,
                        storage_path=str(drawing_library_fetch["storagePath"]),
                        filename=str(drawing_library_fetch["filename"]),
                        skills=drawing_runtime_skills,
                        on_stream_activity=on_stream_activity,
                    )
                )
            else:
                if attachment_context:
                    drawing_pdf_extract = (
                        ChatDrawingPdfExtractionService.parse_from_attachment_context(
                            attachment_context
                        )
                        or {}
                    )

                drawing_pdf_extract, _vision_activation = (
                    ChatDocumentVisionTurnService.run_drawing_vision_with_progress(
                        parsed=drawing_pdf_extract,
                        user_id=str(user_id) if user_id else None,
                        session_id=session_id,
                        attachment_ids=attachment_ids,
                        skills=drawing_runtime_skills,
                        on_stream_activity=on_stream_activity,
                    )
                )

            if drawing_pdf_extract.get("memoryLimited"):
                from app.domain.services.chat_drawing_intent_service import (
                    ChatDrawingIntentService,
                )

                memory_result: dict[str, Any] = {
                    "context": "",
                    "toolCalls": [],
                    "nativeToolCalling": {"used": False, "providerSupports": False},
                    "directAnswer": ChatDrawingIntentService.build_memory_limited_answer(),
                    "skipRag": True,
                    "drawingAnalysisMode": True,
                    "currentMessage": raw_message,
                }

                if drawing_pdf_extract:
                    memory_result["drawingPdfExtractSummary"] = (
                        host._auxiliary_service._build_drawing_pdf_extract_summary(
                            drawing_pdf_extract,
                            product_code_source=drawing_product_code_source,
                        )
                    )

                return ToolTurnPreparation(
                    early_result=host._finalize_tool_context_result(
                        message=raw_message,
                        previous_messages=previous_messages,
                        result=memory_result,
                    ),
                )

            from app.domain.services.chat_drawing_product_code_resolution_service import (
                ChatDrawingProductCodeResolutionService,
            )

            attachment_filename = None

            if drawing_library_fetch:
                attachment_filename = str(drawing_library_fetch.get("filename") or "")
            else:
                attachment_filename = (
                    ChatDrawingProductCodeResolutionService.resolve_attachment_filename(
                        user_id=str(user_id) if user_id else None,
                        session_id=session_id,
                        attachment_ids=attachment_ids,
                    )
                )
            drawing_pdf_extract = (
                ChatDrawingProductCodeResolutionService.enrich_pdf_extract_conflicts(
                    drawing_pdf_extract,
                    attachment_filename=attachment_filename,
                )
            )
            resolved_code, resolved_source = (
                ChatDrawingProductCodeResolutionService.resolve(
                    message=raw_message,
                    has_pdf_attachment=drawing_has_pdf,
                    pdf_extract=drawing_pdf_extract,
                    attachment_filename=attachment_filename,
                )
            )
            drawing_product_code, drawing_product_code_source = (
                ChatDrawingProductCodeResolutionService.merge_precedence(
                    current_code=drawing_product_code,
                    current_source=drawing_product_code_source,
                    resolved_code=resolved_code,
                    resolved_source=resolved_source,
                )
            )

            if drawing_product_code and drawing_pdf_extract:
                from app.application.services.chat_drawing_analyser_bom_confirmation_orchestration_service import (
                    ChatDrawingAnalyserBomConfirmationOrchestrationService,
                )

                anchor_storage_path = ""

                if drawing_library_fetch:
                    anchor_storage_path = str(
                        drawing_library_fetch.get("storagePath") or ""
                    ).strip()
                else:
                    source_meta = drawing_pdf_extract.get("sourceMetadata")

                    if isinstance(source_meta, dict):
                        anchor_storage_path = str(
                            source_meta.get("storagePath") or ""
                        ).strip()

                drawing_pdf_extract = (
                    ChatDrawingAnalyserBomConfirmationOrchestrationService.try_anchor_after_code_resolution(
                        pdf_extract=drawing_pdf_extract,
                        product_code=drawing_product_code,
                        access_token=access_token,
                        storage_path=anchor_storage_path,
                        filename=str(attachment_filename or ""),
                    )
                )

        if drawing_analysis_mode and drawing_has_pdf and not drawing_product_code:
            from app.domain.services.chat_drawing_intent_service import (
                ChatDrawingIntentService,
            )

            result = {
                "context": "",
                "toolCalls": [],
                "nativeToolCalling": {"used": False, "providerSupports": False},
                "directAnswer": ChatDrawingIntentService.build_missing_product_code_answer(),
                "skipRag": True,
                "drawingAnalysisMode": True,
                "currentMessage": raw_message,
            }

            if drawing_pdf_extract:
                result["drawingPdfExtractSummary"] = host._auxiliary_service._build_drawing_pdf_extract_summary(
                    drawing_pdf_extract,
                    product_code_source=drawing_product_code_source,
                )

                if drawing_pdf_extract.get("documentVision"):
                    result["documentVision"] = drawing_pdf_extract["documentVision"]

            return ToolTurnPreparation(
                early_result=host._finalize_tool_context_result(
                    message=raw_message,
                    previous_messages=previous_messages,
                    result=result,
                ),
            )

        from app.domain.services.chat_sql_query_refinement_service import (
            ChatSqlQueryRefinementService,
        )

        sql_refinement = ChatSqlQueryRefinementService.resolve(
            raw_message,
            previous_messages=previous_messages,
        )

        if sql_refinement and sql_refinement.mode == "show_sql":
            return ToolTurnPreparation(
                early_result=host._finalize_tool_context_result(
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
                ),
            )

        from app.domain.services.chat_sql_safety_service import ChatSqlSafetyService

        sql_block_answer = ChatSqlSafetyService.blocked_direct_answer(
            raw_message,
            sql=getattr(sql_refinement, "sql", None) if sql_refinement else None,
        )

        if sql_block_answer:
            return ToolTurnPreparation(
                early_result=host._finalize_tool_context_result(
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
                ),
            )

        if conversation_context is None and previous_messages:
            conversation_context = ChatIntelligencePipelineService.build_conversation_context(
                previous_messages,
            )

        normalized_message = (
            ChatMessageNormalizationService.normalize_for_matching(raw_message) or raw_message
        )

        from app.domain.services.chat_web_search_intent_service import (
            ChatWebSearchIntentService,
        )

        web_search_exclusive = ChatWebSearchIntentService.blocks_external_action_selection(
            raw_message
        )

        if (
            web_search_exclusive
            and ChatWebSearchIntentService.matches(raw_message)
            and not ChatWebSearchIntentService.is_feature_enabled()
        ):
            return ToolTurnPreparation(
                early_result=host._finalize_tool_context_result(
                    message=raw_message,
                    previous_messages=previous_messages,
                    result={
                        "context": "",
                        "toolCalls": [],
                        "nativeToolCalling": {"used": False, "providerSupports": False},
                        "directAnswer": ChatWebSearchIntentService.format_disabled_notice(
                            raw_message
                        ),
                        "skipRag": True,
                        "currentMessage": raw_message,
                    },
                ),
            )

        paginated_early = self._resolve_paginated_shortcuts(
            host,
            user_id=user_id,
            access_token=access_token,
            raw_message=raw_message,
            previous_messages=previous_messages,
            on_stream_activity=on_stream_activity,
        )

        if paginated_early is not None:
            return ToolTurnPreparation(early_result=paginated_early)

        from app.application.services.chat_paginated_external_action_service import (
            ChatPaginatedExternalActionService,
        )

        return ToolTurnPreparation(
            raw_message=raw_message,
            message=normalized_message,
            conversation_context=conversation_context,
            web_search_exclusive=web_search_exclusive,
            drawing_analysis_mode=drawing_analysis_mode,
            drawing_product_code=drawing_product_code,
            drawing_product_codes=drawing_product_codes,
            drawing_product_code_source=drawing_product_code_source,
            drawing_has_pdf=drawing_has_pdf,
            drawing_pdf_extract=drawing_pdf_extract,
            drawing_library_fetch=drawing_library_fetch,
            drawing_runtime_skills=drawing_runtime_skills,
            paginated_service=ChatPaginatedExternalActionService(
                host.execute_tool_use_case,
                format_refinement_resolver=getattr(
                    host,
                    "format_refinement_resolver_service",
                    None,
                ),
            ),
        )

    def _resolve_paginated_shortcuts(
        self,
        host: ChatToolContextService,
        *,
        user_id: str,
        access_token: str,
        raw_message: str,
        previous_messages: list | None,
        on_stream_activity,
    ) -> dict | None:
        from app.application.services.chat_paginated_external_action_service import (
            ChatPaginatedExternalActionService,
        )

        paginated_service = ChatPaginatedExternalActionService(
            host.execute_tool_use_case,
            format_refinement_resolver=getattr(
                host,
                "format_refinement_resolver_service",
                None,
            ),
        )

        format_turn = paginated_service.resolve_format_refinement_turn(
            user_id=user_id,
            access_token=access_token,
            message=raw_message,
            previous_messages=previous_messages,
            on_stream_activity=on_stream_activity,
        )

        if format_turn.kind == "failure" and format_turn.direct_answer:
            return host._finalize_tool_context_result(
                message=raw_message,
                previous_messages=previous_messages,
                result={
                    "context": "",
                    "toolCalls": [],
                    "nativeToolCalling": {"used": False, "providerSupports": False},
                    "directAnswer": format_turn.direct_answer,
                    "skipRag": True,
                    "currentMessage": raw_message,
                },
            )

        if format_turn.kind == "success" and format_turn.payload:
            merged_data, merged_metadata, arguments, continue_prompt = format_turn.payload

            return host._finalize_paginated_consolidation_result(
                raw_message=raw_message,
                previous_messages=previous_messages,
                merged_data=merged_data,
                merged_metadata=merged_metadata,
                arguments=arguments,
                continue_prompt=None,
                reason=ChatToolContextContentService.get("pagination", "formatRefinement"),
            )

        group_by_turn = paginated_service.resolve_group_by_session_refinement_turn(
            message=raw_message,
            previous_messages=previous_messages,
        )

        if group_by_turn.kind == "success" and group_by_turn.payload:
            merged_data, merged_metadata, arguments, _continue = group_by_turn.payload

            return host._finalize_paginated_consolidation_result(
                raw_message=raw_message,
                previous_messages=previous_messages,
                merged_data=merged_data,
                merged_metadata=merged_metadata,
                arguments=arguments,
                continue_prompt=None,
                reason=ChatToolContextContentService.get("pagination", "groupBySessionRefinement"),
            )

        shortcuts = (
            (
                paginated_service.fetch_continue_plan,
                ChatToolContextContentService.get("pagination", "continueConsolidation"),
                True,
            ),
            (
                paginated_service.fetch_full_from_history,
                ChatToolContextContentService.get("pagination", "fullConsolidation"),
                True,
            ),
            (
                paginated_service.fetch_error_recovery_from_history,
                ChatToolContextContentService.get("pagination", "errorRecovery"),
                False,
            ),
        )

        for fetcher, reason, has_continue_prompt in shortcuts:
            payload = fetcher(
                user_id=user_id,
                access_token=access_token,
                message=raw_message,
                previous_messages=previous_messages,
                on_stream_activity=on_stream_activity,
            )

            if not payload:
                continue

            merged_data, merged_metadata, arguments, continue_prompt = payload

            return host._finalize_paginated_consolidation_result(
                raw_message=raw_message,
                previous_messages=previous_messages,
                merged_data=merged_data,
                merged_metadata=merged_metadata,
                arguments=arguments,
                continue_prompt=continue_prompt if has_continue_prompt else None,
                reason=reason,
            )

        return None
