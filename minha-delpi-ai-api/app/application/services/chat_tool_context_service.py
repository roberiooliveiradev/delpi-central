import json

from app.application.use_cases.execute_tool_use_case import ExecuteToolUseCase
from app.domain.services.tool_selection_service import ToolSelectionService
from app.domain.services.external_actions.external_action_result_presenter import ExternalActionResultPresenter
from app.application.services.chat_tool_context_auxiliary_service import (
    ChatToolContextAuxiliaryService,
)
from app.domain.services.chat_tool_context_content_service import (
    ChatToolContextContentService,
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
from app.application.services.chat_tool_context_pre_turn_service import (
    ChatToolContextPreTurnService,
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
        format_refinement_resolver_service=None,
    ):
        self.tool_selection_service = tool_selection_service
        self.execute_tool_use_case = execute_tool_use_case
        self.external_action_selection_service = external_action_selection_service
        self.tool_router_service = tool_router_service
        self.external_action_repository = external_action_repository
        self.native_tool_calling_service = native_tool_calling_service
        self.format_refinement_resolver_service = format_refinement_resolver_service
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
        self._pre_turn_service = ChatToolContextPreTurnService()
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

        from app.domain.services.chat_operational_retry_message_service import (
            ChatOperationalRetryMessageService,
        )

        rewritten, did_rewrite = ChatOperationalRetryMessageService.rewrite_if_needed(
            message,
            previous_messages,
        )
        effective_message = rewritten if did_rewrite else message

        preparation = self._pre_turn_service.prepare_turn(
            self,
            user_id=user_id,
            access_token=access_token,
            message=effective_message,
            allowed_action_ids=allowed_action_ids,
            actions_enabled=actions_enabled,
            conversation_context=conversation_context,
            previous_messages=previous_messages,
            on_stream_activity=on_stream_activity,
            agent_context=agent_context,
            working_memory=working_memory,
            attachment_context=attachment_context,
            attachment_ids=attachment_ids,
            session_id=session_id,
        )

        if preparation.early_result is not None:
            return preparation.early_result

        raw_message = preparation.raw_message
        message = preparation.message
        conversation_context = preparation.conversation_context
        web_search_exclusive = preparation.web_search_exclusive
        drawing_analysis_mode = preparation.drawing_analysis_mode
        drawing_product_code = preparation.drawing_product_code
        drawing_product_codes = preparation.drawing_product_codes
        drawing_product_code_source = preparation.drawing_product_code_source
        drawing_has_pdf = preparation.drawing_has_pdf
        drawing_pdf_extract = preparation.drawing_pdf_extract
        drawing_library_fetch = preparation.drawing_library_fetch
        drawing_runtime_skills = preparation.drawing_runtime_skills
        paginated_service = preparation.paginated_service

        from app.domain.services.chat_tool_grounding_context_service import (
            ChatToolGroundingContextService,
        )

        memory_snapshot = working_memory if isinstance(working_memory, dict) else None

        if memory_snapshot is None and isinstance(agent_context, dict):
            candidate = agent_context.get("workingMemory")
            memory_snapshot = candidate if isinstance(candidate, dict) else None

        with ChatToolGroundingContextService.scope(
            message=message,
            conversation_context=conversation_context,
            previous_messages=previous_messages,
            memory_snapshot=memory_snapshot,
        ):
            return self._build_context_with_grounding_scope(
                user_id=user_id,
                access_token=access_token,
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
                working_memory=working_memory,
                attachment_context=attachment_context,
                attachment_ids=attachment_ids,
                session_id=session_id,
                web_search_exclusive=web_search_exclusive,
                drawing_analysis_mode=drawing_analysis_mode,
                drawing_product_code=drawing_product_code,
                drawing_product_codes=drawing_product_codes,
                drawing_product_code_source=drawing_product_code_source,
                drawing_has_pdf=drawing_has_pdf,
                drawing_pdf_extract=drawing_pdf_extract,
                drawing_library_fetch=drawing_library_fetch,
                drawing_runtime_skills=drawing_runtime_skills,
                paginated_service=paginated_service,
            )

    def _build_context_with_grounding_scope(
        self,
        *,
        user_id: str,
        access_token: str,
        message: str,
        raw_message: str,
        allowed_action_ids: list[str] | None,
        actions_enabled: bool,
        allowed_tool_names: list[str] | None,
        conversation_context: str | None,
        previous_messages: list | None,
        max_external_action_calls: int | None,
        on_stream_activity,
        agent_context: dict | None,
        working_memory: dict | None,
        attachment_context: str | None,
        attachment_ids: list[str] | None,
        session_id: str | None,
        web_search_exclusive: bool,
        drawing_analysis_mode: bool,
        drawing_product_code,
        drawing_product_codes,
        drawing_product_code_source,
        drawing_has_pdf: bool,
        drawing_pdf_extract,
        drawing_library_fetch,
        drawing_runtime_skills,
        paginated_service,
    ) -> dict:
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

        execution = self._maybe_apply_sufficiency_critic(
            execution,
            user_id=user_id,
            access_token=access_token,
            message=message,
            raw_message=raw_message,
            allowed_action_ids=allowed_action_ids,
            previous_messages=previous_messages,
            max_external_action_calls=max_external_action_calls,
            on_stream_activity=on_stream_activity,
            paginated_service=paginated_service,
            selected_external_action_meta=selection.selected_external_action_meta,
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
            drawing_product_codes=drawing_product_codes,
            drawing_product_code_source=drawing_product_code_source,
            drawing_has_pdf=drawing_has_pdf,
            drawing_pdf_extract=drawing_pdf_extract,
            drawing_library_fetch=drawing_library_fetch,
            drawing_runtime_skills=drawing_runtime_skills,
            on_stream_activity=on_stream_activity,
        )

    def run_post_rag_web_fallback(
        self,
        *,
        user_id: str,
        access_token: str,
        message: str,
        previous_messages: list | None = None,
        on_stream_activity=None,
    ) -> dict | None:
        from app.domain.services.chat_web_search_intent_service import (
            ChatWebSearchIntentService,
        )

        selected_tool = ChatWebSearchIntentService.resolve_for_post_rag_fallback(
            message,
            previous_messages=previous_messages,
        )

        if not selected_tool:
            return None

        from app.application.services.chat_paginated_external_action_service import (
            ChatPaginatedExternalActionService,
        )

        execution = self._execution_service.execute_selected_tools(
            self,
            user_id=user_id,
            access_token=access_token,
            message=message,
            raw_message=message,
            allowed_action_ids=None,
            previous_messages=previous_messages,
            selected_tools=[selected_tool],
            on_stream_activity=on_stream_activity,
            paginated_service=ChatPaginatedExternalActionService(self.execute_tool_use_case),
        )

        return self._result_assembly_service.assemble_and_finalize(
            self,
            message=message,
            raw_message=message,
            previous_messages=previous_messages,
            user_id=user_id,
            session_id=None,
            attachment_ids=None,
            native_meta={"used": False, "providerSupports": False},
            selected_external_action_meta=None,
            execution=execution,
            drawing_analysis_mode=False,
            drawing_product_code=None,
            drawing_product_codes=(),
            drawing_product_code_source=None,
            drawing_has_pdf=False,
            drawing_pdf_extract=None,
            drawing_library_fetch=None,
            drawing_runtime_skills=None,
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
    def resolve_authorized_persisted_answer(
        cls,
        answer,
        safe_tool_calls,
        *,
        message=None,
        skip_replacement=False,
        response_mode_effect=None,
        response_mode=None,
    ):
        return ChatToolContextPresentationService.resolve_authorized_persisted_answer(
            answer,
            safe_tool_calls,
            message=message,
            skip_replacement=skip_replacement,
            response_mode_effect=response_mode_effect,
            response_mode=response_mode,
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

    def _format_refinement_chart_failure_answer(
        self,
        safe_tool_calls: list[dict],
        *,
        raw_message: str,
        previous_messages: list | None,
    ) -> str | None:
        from app.application.services.chat_presentation_format_refinement_resolver_service import (
            ChatPresentationFormatRefinementResolverService,
        )

        for tool_call in safe_tool_calls:
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict) or not metadata.get("ok"):
                continue

            presentation = metadata.get("presentation")

            if isinstance(presentation, dict) and str(presentation.get("type") or "").lower() == "chart":
                return None

            chart_slot = metadata.get("chartPresentation")

            if isinstance(chart_slot, dict) and str(chart_slot.get("type") or "").lower() == "chart":
                return None

        resolver = self.format_refinement_resolver_service or ChatPresentationFormatRefinementResolverService()

        return resolver.build_failure_direct_answer(
            raw_message,
            previous_messages=previous_messages,
            reason="chart_build_failed",
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

        from app.domain.services.chat_presentation_prose_delivery_service import (
            ChatPresentationProseDeliveryService,
        )

        if ChatPresentationProseDeliveryService.should_omit_legacy_tool_context_direct_answer(
            safe_metadata,
        ):
            direct_answer = None

        requested_format = self._resolve_consolidation_format(raw_message, previous_messages)

        if requested_format:
            self._apply_format_override(
                safe_tool_calls,
                requested_format,
                merged_data,
            )

            if requested_format == "chart":
                chart_failure = self._format_refinement_chart_failure_answer(
                    safe_tool_calls,
                    raw_message=raw_message,
                    previous_messages=previous_messages,
                )

                if chart_failure:
                    return self._finalize_tool_context_result(
                        message=raw_message,
                        previous_messages=previous_messages,
                        result={
                            "context": "",
                            "toolCalls": [],
                            "nativeToolCalling": {"used": False, "providerSupports": False},
                            "directAnswer": chart_failure,
                            "skipRag": True,
                            "currentMessage": raw_message,
                        },
                    )

        if direct_answer and requested_format != "text":
            ChatToolContextPresentationService._suppress_redundant_structure_presentations(safe_tool_calls)

        if direct_answer and requested_format != "text":
            direct_answer = ChatToolContextPresentationService._compact_direct_answer_for_rich_presentation(
                direct_answer,
                safe_tool_calls,
            )

        presentation_answer = ChatToolContextPresentationService.prefer_presentation_direct_answer(
            direct_answer,
            safe_tool_calls,
            message=raw_message,
        )

        if presentation_answer:
            direct_answer = presentation_answer

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

    def _maybe_apply_sufficiency_critic(
        self,
        execution,
        *,
        user_id: str,
        access_token: str,
        message: str,
        raw_message: str,
        allowed_action_ids: list[str] | None,
        previous_messages: list | None,
        max_external_action_calls: int | None,
        on_stream_activity,
        paginated_service,
        selected_external_action_meta: dict | None,
    ):
        from app.application.services.chat_tool_context_execution_service import (
            ToolExecutionState,
        )
        from app.domain.services.chat_operational_sufficiency_critic_service import (
            ChatOperationalSufficiencyCriticService,
        )

        if not isinstance(execution, ToolExecutionState):
            return execution

        used = sum(
            1
            for item in execution.safe_tool_calls
            if isinstance(item, dict)
            and str(item.get("name") or "") == "execute_external_action"
        )
        limit = max(1, int(max_external_action_calls or used or 1))
        remaining = max(0, limit - used)

        enrichment_plan = None

        if isinstance(selected_external_action_meta, dict):
            candidate = selected_external_action_meta.get("enrichmentPlan")
            enrichment_plan = candidate if isinstance(candidate, dict) else None

        verdict = ChatOperationalSufficiencyCriticService.evaluate(
            tool_calls=execution.safe_tool_calls,
            enrichment_plan=enrichment_plan,
            remaining_slots=remaining,
            user_message=raw_message or message,
        )

        if isinstance(selected_external_action_meta, dict):
            audit = selected_external_action_meta.setdefault("enrichmentPlan", {})

            if isinstance(audit, dict):
                audit["sufficiency"] = ChatOperationalSufficiencyCriticService.audit_payload(
                    verdict
                )

        suggestions = ChatOperationalSufficiencyCriticService.build_clarification_suggestions(
            verdict=verdict,
            tool_calls=execution.safe_tool_calls,
            message=raw_message or message,
            enrichment_plan=enrichment_plan,
        )

        if verdict.action != "execute" or remaining < 1:
            if suggestions and isinstance(selected_external_action_meta, dict):
                selected_external_action_meta["anomalyClarificationSuggestions"] = (
                    suggestions
                )

            return execution

        follow_ups = ChatOperationalSufficiencyCriticService.plan_follow_up_selections(
            self.external_action_selection_service,
            verdict=verdict,
            message=raw_message or message,
            tool_calls=execution.safe_tool_calls,
            allowed_action_ids=allowed_action_ids,
            previous_messages=previous_messages,
        )

        if not follow_ups:
            if suggestions and isinstance(selected_external_action_meta, dict):
                selected_external_action_meta["anomalyClarificationSuggestions"] = (
                    suggestions
                )

            return execution

        follow_state = self._execution_service.execute_selected_tools(
            self,
            user_id=user_id,
            access_token=access_token,
            message=message,
            raw_message=raw_message,
            allowed_action_ids=allowed_action_ids,
            previous_messages=previous_messages,
            selected_tools=follow_ups,
            on_stream_activity=on_stream_activity,
            paginated_service=paginated_service,
        )

        if isinstance(selected_external_action_meta, dict):
            audit = selected_external_action_meta.setdefault("enrichmentPlan", {})

            if isinstance(audit, dict):
                follow_ids = [
                    str((item.get("sufficiencyFollowUp") or item.get("anomalyFollowUp") or {}).get("routeId") or "").strip()
                    for item in follow_ups
                    if isinstance(item, dict)
                ]
                audit["anomalyFollowUps"] = [item for item in follow_ids if item]
                sufficiency = audit.get("sufficiency")

                if isinstance(sufficiency, dict):
                    sufficiency["executedRouteIds"] = [
                        item for item in follow_ids if item
                    ]

                audit["executedCount"] = int(audit.get("executedCount") or used) + len(
                    follow_state.safe_tool_calls
                )

        post_suggestions = ChatOperationalSufficiencyCriticService.build_clarification_suggestions(
            verdict=verdict,
            tool_calls=[*execution.safe_tool_calls, *follow_state.safe_tool_calls],
            message=raw_message or message,
            enrichment_plan=enrichment_plan,
        )

        if post_suggestions and isinstance(selected_external_action_meta, dict):
            selected_external_action_meta["anomalyClarificationSuggestions"] = (
                post_suggestions
            )

        merged_context = execution.context

        if follow_state.context:
            merged_context = (
                f"{execution.context}\n\n{follow_state.context}".strip()
                if execution.context
                else follow_state.context
            )

        return ToolExecutionState(
            context=merged_context,
            safe_tool_calls=[*execution.safe_tool_calls, *follow_state.safe_tool_calls],
            direct_answer=follow_state.direct_answer or execution.direct_answer,
            skip_rag=execution.skip_rag or follow_state.skip_rag,
            last_external_action_data=(
                follow_state.last_external_action_data
                or execution.last_external_action_data
            ),
            last_web_search_data=execution.last_web_search_data,
            last_platform_tool_result=execution.last_platform_tool_result,
            web_sources=execution.web_sources,
            web_search_payload=execution.web_search_payload,
            external_action_results=[
                *execution.external_action_results,
                *follow_state.external_action_results,
            ],
            pagination_continue_prompt=(
                follow_state.pagination_continue_prompt
                or execution.pagination_continue_prompt
            ),
        )

    def _maybe_execute_anomaly_follow_ups(
        self,
        execution,
        *,
        user_id: str,
        access_token: str,
        message: str,
        raw_message: str,
        allowed_action_ids: list[str] | None,
        previous_messages: list | None,
        max_external_action_calls: int | None,
        on_stream_activity,
        paginated_service,
        selected_external_action_meta: dict | None,
    ):
        """Compat: delega ao entry point único do critic de suficiência."""
        return self._maybe_apply_sufficiency_critic(
            execution,
            user_id=user_id,
            access_token=access_token,
            message=message,
            raw_message=raw_message,
            allowed_action_ids=allowed_action_ids,
            previous_messages=previous_messages,
            max_external_action_calls=max_external_action_calls,
            on_stream_activity=on_stream_activity,
            paginated_service=paginated_service,
            selected_external_action_meta=selected_external_action_meta,
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
        """Extrai skills + host ambient do workspace do turno (ou do agent legado)."""
        if not isinstance(agent_context, dict):
            return None

        resolved: dict = {}

        skills = agent_context.get("skills")
        if isinstance(skills, dict) and skills:
            resolved["skills"] = dict(skills)
        else:
            metadata = agent_context.get("metadata")
            if isinstance(metadata, dict):
                runtime_skills = metadata.get("skills")
                if isinstance(runtime_skills, dict) and runtime_skills:
                    resolved["skills"] = dict(runtime_skills)

        host = agent_context.get("tvDashboardHostContext") or agent_context.get(
            "hostContext"
        )
        if isinstance(host, dict) and host:
            resolved["tvDashboardHostContext"] = dict(host)

        return resolved or None

























    def _build_safe_tool_metadata(self, tool_name: str, metadata: dict | None, data) -> dict:
        return self._external_action_formatter._build_safe_tool_metadata(tool_name, metadata, data)

    def _build_response_preview(self, data, max_chars: int | None = None) -> str:
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

        return "\n".join(
            [
                ChatToolContextContentService.format("toolError", "header", tool_name=name),
                ChatToolContextContentService.get("toolError", "selectionFailed"),
                ChatToolContextContentService.get("toolError", "policy"),
                json.dumps(payload, ensure_ascii=False, indent=2),
            ]
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






