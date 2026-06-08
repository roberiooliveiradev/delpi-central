import json

from app.application.use_cases.execute_tool_use_case import ExecuteToolUseCase
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.tool_selection_service import ToolSelectionService
from app.domain.services.external_actions.external_action_result_presenter import ExternalActionResultPresenter
from app.application.services.chat_tool_context_auxiliary_service import (
    ChatToolContextAuxiliaryService,
)
from app.application.services.chat_tool_context_execution_service import (
    ChatToolContextExecutionService,
)
from app.application.services.chat_tool_context_external_action_formatter import (
    ChatToolContextExternalActionFormatter,
)
from app.application.services.chat_tool_context_format_service import (
    ChatToolContextFormatService,
)
from app.application.services.chat_tool_context_result_assembly_service import (
    ChatToolContextResultAssemblyService,
)
from app.application.services.chat_tool_context_selection_service import (
    ChatToolContextSelectionService,
)
from app.domain.services.chat_tool_context_presentation_service import (
    ChatToolContextPresentationService,
)


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
        self._format_service = ChatToolContextFormatService(self.external_action_result_presenter)
        self._external_action_formatter = ChatToolContextExternalActionFormatter(
            self.external_action_result_presenter
        )
        self._auxiliary_service = ChatToolContextAuxiliaryService(
            self.external_action_result_presenter,
            self._external_action_formatter,
            execute_tool_use_case=execute_tool_use_case,
            external_action_repository=external_action_repository,
        )
        self._selection_service = ChatToolContextSelectionService()
        self._execution_service = ChatToolContextExecutionService()
        self._result_assembly_service = ChatToolContextResultAssemblyService()

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
        working_memory: dict | None = None,
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
        workspace = dict(self._resolve_workspace_context(agent_context) or {})
        workspace["actionsEnabled"] = bool(actions_enabled)
        workspace["allowedActionIds"] = list(allowed_action_ids or [])

        memory = working_memory

        if not isinstance(memory, dict) and isinstance(agent_context, dict):
            memory = agent_context.get("workingMemory")

        if isinstance(memory, dict):
            workspace["workingMemory"] = memory

        self._build_workspace_context = workspace

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
        drawing_product_code_source = "turn" if drawing_product_code else None
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

            if drawing_pdf_extract and drawing_pdf_extract.get("productCode"):
                extracted_product_code = str(drawing_pdf_extract["productCode"])
                extracted_source = (
                    "document_vision"
                    if drawing_pdf_extract.get("documentVision")
                    else "attachment_context"
                )

                if not drawing_product_code:
                    drawing_product_code = extracted_product_code
                    drawing_product_code_source = extracted_source
                elif str(drawing_product_code) == extracted_product_code:
                    drawing_product_code_source = extracted_source

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
                result["drawingPdfExtractSummary"] = self._auxiliary_service._build_drawing_pdf_extract_summary(
                    drawing_pdf_extract,
                    product_code_source=drawing_product_code_source,
                )

                if drawing_pdf_extract.get("documentVision"):
                    result["documentVision"] = drawing_pdf_extract["documentVision"]

            return self._finalize_tool_context_result(
                message=raw_message,
                previous_messages=previous_messages,
                result=result,
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

        if (
            web_search_exclusive
            and ChatWebSearchIntentService.matches(raw_message)
            and not ChatWebSearchIntentService.is_feature_enabled()
        ):
            return self._finalize_tool_context_result(
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

        error_recovery = paginated_service.fetch_error_recovery_from_history(
            user_id=user_id,
            access_token=access_token,
            message=raw_message,
            previous_messages=previous_messages,
            on_stream_activity=on_stream_activity,
        )

        if error_recovery:
            merged_data, merged_metadata, arguments, _continue_prompt = error_recovery
            return self._finalize_paginated_consolidation_result(
                raw_message=raw_message,
                previous_messages=previous_messages,
                merged_data=merged_data,
                merged_metadata=merged_metadata,
                arguments=arguments,
                continue_prompt=None,
                reason="Recuperação automática da consulta anterior.",
            )

        format_refinement = paginated_service.fetch_format_refinement_from_history(
            user_id=user_id,
            access_token=access_token,
            message=raw_message,
            previous_messages=previous_messages,
            on_stream_activity=on_stream_activity,
        )

        if format_refinement:
            merged_data, merged_metadata, arguments, _continue_prompt = format_refinement
            return self._finalize_paginated_consolidation_result(
                raw_message=raw_message,
                previous_messages=previous_messages,
                merged_data=merged_data,
                merged_metadata=merged_metadata,
                arguments=arguments,
                continue_prompt=None,
                reason="Reapresentação do último resultado no formato solicitado.",
            )

        selection = self._selection_service.select_tools(
            self,
            message=message,
            raw_message=raw_message,
            allowed_action_ids=allowed_action_ids,
            actions_enabled=actions_enabled,
            allowed_tool_names=allowed_tool_names,
            conversation_context=conversation_context,
            previous_messages=previous_messages,
            max_external_action_calls=max_external_action_calls,
            on_stream_activity=on_stream_activity,
            agent_context=agent_context,
            attachment_context=attachment_context,
            drawing_analysis_mode=drawing_analysis_mode,
            drawing_product_code=drawing_product_code,
            drawing_product_code_source=drawing_product_code_source,
            drawing_runtime_skills=drawing_runtime_skills,
            drawing_pdf_extract=drawing_pdf_extract,
            web_search_exclusive=web_search_exclusive,
        )

        if selection.early_result is not None:
            return selection.early_result

        execution = self._execution_service.execute_selected_tools(
            self,
            user_id=user_id,
            access_token=access_token,
            message=message,
            raw_message=raw_message,
            allowed_action_ids=allowed_action_ids,
            previous_messages=previous_messages,
            selected_tools=selection.selected_tools,
            on_stream_activity=on_stream_activity,
            paginated_service=paginated_service,
        )

        return self._result_assembly_service.assemble_and_finalize(
            self,
            message=message,
            raw_message=raw_message,
            previous_messages=previous_messages,
            user_id=user_id,
            session_id=session_id,
            attachment_ids=attachment_ids,
            native_meta=selection.native_meta,
            selected_external_action_meta=selection.selected_external_action_meta,
            execution=execution,
            drawing_analysis_mode=drawing_analysis_mode,
            drawing_product_code=drawing_product_code,
            drawing_product_code_source=drawing_product_code_source,
            drawing_has_pdf=drawing_has_pdf,
            drawing_pdf_extract=drawing_pdf_extract,
            drawing_runtime_skills=drawing_runtime_skills,
            on_stream_activity=on_stream_activity,
        )



    # --- Apresentação rica (delegação Fase 3C lote 9) ---

    @classmethod
    def _rich_presentation_from_metadata(cls, metadata: dict) -> dict | None:
        return ChatToolContextPresentationService._rich_presentation_from_metadata(metadata)

    @classmethod
    def _external_action_tool_calls(cls, safe_tool_calls: list[dict]) -> list[dict]:
        return ChatToolContextPresentationService._external_action_tool_calls(safe_tool_calls)

    @classmethod
    def _successful_external_action_tool_calls(cls, safe_tool_calls: list[dict]) -> list[dict]:
        return ChatToolContextPresentationService._successful_external_action_tool_calls(safe_tool_calls)

    @classmethod
    def should_answer_with_presentation_only(cls, safe_tool_calls: list[dict]) -> bool:
        return ChatToolContextPresentationService.should_answer_with_presentation_only(safe_tool_calls)

    @classmethod
    def prefer_presentation_direct_answer(cls, direct_answer, safe_tool_calls, *, message=None):
        return ChatToolContextPresentationService.prefer_presentation_direct_answer(
            direct_answer, safe_tool_calls, message=message
        )

    @classmethod
    def _extract_pagination_continuation_suffix(cls, direct_answer):
        return ChatToolContextPresentationService._extract_pagination_continuation_suffix(direct_answer)

    @classmethod
    def resolve_presentation_only_answer(cls, safe_tool_calls):
        return ChatToolContextPresentationService.resolve_presentation_only_answer(safe_tool_calls)

    @classmethod
    def _authorized_body_from_metadata(cls, metadata: dict):
        return ChatToolContextPresentationService._authorized_body_from_metadata(metadata)

    @classmethod
    def build_authorized_answer_from_tool_calls(cls, safe_tool_calls):
        return ChatToolContextPresentationService.build_authorized_answer_from_tool_calls(safe_tool_calls)

    @classmethod
    def should_persist_authorized_tool_answer(cls, safe_tool_calls, *, message=None):
        return ChatToolContextPresentationService.should_persist_authorized_tool_answer(
            safe_tool_calls, message=message
        )

    @classmethod
    def resolve_authorized_persisted_answer(cls, answer, safe_tool_calls, *, message=None, skip_replacement=False):
        return ChatToolContextPresentationService.resolve_authorized_persisted_answer(
            answer, safe_tool_calls, message=message, skip_replacement=skip_replacement
        )

    @classmethod
    def _has_rich_presentation(cls, safe_tool_calls):
        return ChatToolContextPresentationService._has_rich_presentation(safe_tool_calls)

    @classmethod
    def _presentation_titles(cls, safe_tool_calls):
        return ChatToolContextPresentationService._presentation_titles(safe_tool_calls)

    @classmethod
    def _compact_direct_answer_for_rich_presentation(cls, direct_answer, safe_tool_calls):
        return ChatToolContextPresentationService._compact_direct_answer_for_rich_presentation(
            direct_answer, safe_tool_calls
        )

    @classmethod
    def _suppress_redundant_structure_presentations(cls, safe_tool_calls):
        return ChatToolContextPresentationService._suppress_redundant_structure_presentations(safe_tool_calls)

    def _resolve_consolidation_format(self, message: str, previous_messages: list | None) -> str | None:
        return self._format_service.resolve_consolidation_format(
            message,
            previous_messages,
            workspace_context=getattr(self, "_build_workspace_context", None),
        )

    @classmethod
    def _detect_requested_format(cls, message: str) -> str | None:
        return ChatToolContextFormatService.detect_requested_format(message)

    def _apply_format_override(self, safe_tool_calls, requested_format, last_data) -> None:
        return self._format_service.apply_format_override(safe_tool_calls, requested_format, last_data)

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
        safe_metadata = self._external_action_formatter._build_safe_tool_metadata(
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
        direct_answer = self._auxiliary_service._build_direct_answer(
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

        if direct_answer and requested_format != "text":
            ChatToolContextPresentationService._suppress_redundant_structure_presentations(safe_tool_calls)

        if direct_answer and requested_format != "text":
            direct_answer = ChatToolContextPresentationService._compact_direct_answer_for_rich_presentation(
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
                "context": self._external_action_formatter._format_tool_context(
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

        from app.domain.services.chat_advanced_sql_specialist_service import (
            ChatAdvancedSqlSpecialistService,
        )

        finalized = ChatAdvancedSqlSpecialistService.enrich_tool_context(
            message=message,
            result=finalized,
            workspace_context=getattr(self, "_build_workspace_context", None),
            previous_messages=previous_messages,
        )

        return finalized

    @classmethod
    def _resolve_workspace_context(cls, agent_context: dict | None) -> dict | None:
        if not isinstance(agent_context, dict):
            return None

        skills = agent_context.get("skills")

        if isinstance(skills, dict) and skills:
            return {"skills": skills}

        metadata = agent_context.get("metadata")

        if isinstance(metadata, dict):
            runtime_skills = metadata.get("skills")

            if isinstance(runtime_skills, dict) and runtime_skills:
                return {"skills": runtime_skills}

        return None

























    def _build_safe_tool_metadata(self, tool_name: str, metadata: dict | None, data) -> dict:
        return self._external_action_formatter._build_safe_tool_metadata(tool_name, metadata, data)

    def _build_response_preview(self, data, max_chars: int = 12000) -> str:
        return self._external_action_formatter._build_response_preview(data, max_chars=max_chars)

    def _format_tool_context(self, name, reason, data, metadata=None, arguments=None, *, message=None) -> str:
        return self._external_action_formatter._format_tool_context(
            name, reason, data, metadata, arguments, message=message
        )

    def _format_external_action_context(self, reason, data, metadata, arguments=None) -> str:
        return self._external_action_formatter._format_external_action_context(
            reason, data, metadata, arguments
        )

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



    def _is_successful_external_action(self, metadata: dict) -> bool:
        if not metadata.get("ok"):
            return False

        status_code = metadata.get("statusCode")

        try:
            return 200 <= int(status_code) < 300
        except (TypeError, ValueError):
            return False


    def _build_drawing_pdf_extract_summary(self, pdf_extract, *, product_code_source=None) -> dict:
        return self._auxiliary_service._build_drawing_pdf_extract_summary(
            pdf_extract, product_code_source=product_code_source
        )

    def _build_drawing_analysis_enrichment(self, **kwargs) -> dict | None:
        return self._auxiliary_service._build_drawing_analysis_enrichment(**kwargs)

    def _build_direct_answer(self, data, *, message: str, path: str | None = None, operation_id: str | None = None) -> str | None:
        return self._auxiliary_service._build_direct_answer(
            data, message=message, path=path, operation_id=operation_id
        )

    def _extract_external_action_summary(self, data):
        return self._auxiliary_service._extract_external_action_summary(data)

    def _summarize_items(self, items):
        return self._auxiliary_service._summarize_items(items)

    def _try_sql_error_recovery(self, **kwargs):
        return self._auxiliary_service._try_sql_error_recovery(**kwargs)

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






