"""Classificação pré-execução de intenção — Playbook 02."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_intent_router.chat_intent_router_entity_resolution_service import (
    ChatIntentRouterEntityResolutionService,
)
from app.domain.services.chat_intent_router.chat_intent_router_heuristics_service import (
    ChatIntentRouterHeuristicsService,
)
from app.domain.services.chat_intent_router.chat_intent_router_models import IntentRouteResult
from app.domain.services.chat_intent_router.chat_intent_router_support_service import (
    ChatIntentRouterSupportService,
)


class ChatIntentRouterClassifyService:
    @classmethod
    def classify(
        cls,
        message: str,
        *,
        previous_messages: list[Any] | None = None,
        workspace_context: dict | None = None,
        attachment_ids: list[str] | None = None,
        allowed_action_ids: list[str] | None = None,
        text_task_pure: bool = False,
        text_task_category: str | None = None,
        analysis_mode: bool = False,
        operational_optimize: bool = False,
        canvas_operational_update: bool = False,
    ) -> IntentRouteResult:
        """Classificação pré-execução (prioridade Playbook 02)."""
        from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
        from app.domain.services.chat_canvas_intent_service import ChatCanvasIntentService
        from app.domain.services.chat_sql_safety_service import ChatSqlSafetyService
        from app.domain.services.chat_text_task_intent_service import ChatTextTaskIntentService

        history = previous_messages or []
        normalized = str(message or "").strip()

        if not normalized:
            return ChatIntentRouterSupportService.with_decision(
                IntentRouteResult(
                    intent="llm_general",
                    confidence=0.3,
                    priority_applied=11,
                ),
                decision="llm_fallback",
                reason="empty_message",
            )

        from app.domain.services.chat_active_pending_service import (
            ChatActivePendingService,
        )

        pending = ChatActivePendingService.find_from_messages(history)

        if pending:
            resolved = ChatActivePendingService.try_resolve(normalized, pending)

            if resolved:
                params = resolved.get("resolvedParams")

                return ChatIntentRouterSupportService.with_decision(
                    IntentRouteResult(
                        intent="clarification",
                        sub_intent=str(pending.get("kind") or "pending"),
                        confidence=0.93,
                        requires_tool=bool(resolved.get("requiresTool")),
                        requires_rag=False,
                        requires_llm=False,
                        priority_applied=2,
                        resolved_params=dict(params) if isinstance(params, dict) else None,
                        flags=("active_pending_resolved", "clarification_answer"),
                    ),
                    decision="clarification_resume",
                    reason="active_pending_resolved",
                )

        if ChatSqlSafetyService.blocked_direct_answer(normalized):
            return ChatIntentRouterSupportService.with_decision(
                IntentRouteResult(
                    intent="security",
                    sub_intent="sql_blocked",
                    confidence=0.99,
                    requires_llm=False,
                    priority_applied=1,
                    flags=("sql_safety",),
                ),
                decision="block_sql",
                reason="destructive_sql_blocked",
            )

        if attachment_ids and ChatIntentRouterHeuristicsService.looks_attachment_summary(normalized):
            return ChatIntentRouterSupportService.with_decision(
                IntentRouteResult(
                    intent="attachment_task",
                    sub_intent="summary",
                    confidence=0.9,
                    requires_rag=True,
                    requires_llm=True,
                    priority_applied=7,
                    flags=("attachment_summary",),
                ),
                decision="attachment_summary",
                reason="summarize_attachment",
            )

        from app.domain.services.chat_drawing_intent_service import ChatDrawingIntentService

        if ChatDrawingIntentService.is_drawing_analysis_request(
            normalized,
            attachment_ids=attachment_ids,
        ):
            code = ChatDrawingIntentService.resolve_product_code(normalized)
            params = {"productCode": code} if code else None

            return ChatIntentRouterSupportService.with_decision(
                IntentRouteResult(
                    intent="drawing_analysis",
                    sub_intent="pdf_api_validation",
                    confidence=0.94,
                    requires_tool=bool(code and allowed_action_ids),
                    requires_rag=bool(attachment_ids),
                    requires_llm=not bool(code),
                    priority_applied=5,
                    resolved_params=params,
                    flags=("drawing_analysis_delpi",),
                ),
                decision="drawing_analysis",
                reason="drawing_request",
            )

        from app.domain.services.chat_attachment_document_intent_service import (
            ChatAttachmentDocumentIntentService,
        )

        if (
            attachment_ids
            and ChatAttachmentDocumentIntentService.is_document_content_question(normalized)
        ):
            return ChatIntentRouterSupportService.with_decision(
                IntentRouteResult(
                    intent="attachment_task",
                    sub_intent="read_content",
                    confidence=0.91,
                    requires_tool=False,
                    requires_rag=True,
                    requires_llm=True,
                    priority_applied=7,
                    flags=("attachment_document", "document_vision"),
                ),
                decision="attachment_read",
                reason="document_question_with_files",
            )

        if text_task_pure or ChatTextTaskIntentService.is_pure_text_task(
            normalized,
            previous_messages=history,
        ):
            sub = text_task_category or ChatTextTaskIntentService.classify(normalized)
            intent = "email_task" if sub == "email" else "text_task"

            return ChatIntentRouterSupportService.with_decision(
                IntentRouteResult(
                    intent=intent,
                    sub_intent=sub,
                    confidence=0.92,
                    requires_tool=False,
                    requires_rag=False,
                    requires_llm=True,
                    priority_applied=3,
                    flags=("text_task_pure", "skip_tools"),
                ),
                decision="skip_tools",
                reason="explicit_text_task",
            )

        if history and ChatAnalysisIntentService.is_data_interpretation_request(
            normalized,
            history,
        ):
            from app.domain.services.chat_conversation_context_service import (
                ChatConversationContextService,
            )

            if ChatConversationContextService.has_recent_tool_data(history):
                return ChatIntentRouterSupportService.with_decision(
                    IntentRouteResult(
                        intent="follow_up",
                        sub_intent="data_interpretation",
                        is_follow_up=True,
                        confidence=0.9,
                        requires_tool=False,
                        requires_rag=False,
                        requires_llm=True,
                        priority_applied=5,
                    ),
                    decision="follow_up",
                    reason="data_interpretation",
                )

        sql_sub = ChatIntentRouterHeuristicsService.sql_sub_intent(normalized)
        operational_sub = ChatIntentRouterHeuristicsService.operational_sub_intent(normalized)

        if sql_sub and operational_sub != "system_metadata":
            execute = sql_sub == "sql_execute"

            return ChatIntentRouterSupportService.with_decision(
                IntentRouteResult(
                    intent="sql_task",
                    sub_intent=sql_sub,
                    confidence=0.87,
                    requires_tool=execute,
                    requires_llm=True,
                    priority_applied=9,
                    flags=("sql_task",),
                ),
                decision="sql_route",
                reason=sql_sub,
            )

        compound_steps = ChatIntentRouterHeuristicsService.mixed_compound_steps(normalized)

        if compound_steps:
            return ChatIntentRouterSupportService.with_decision(
                IntentRouteResult(
                    intent="mixed_task",
                    sub_intent="compound",
                    confidence=0.86,
                    requires_tool=True,
                    requires_rag="attachment_summary" in compound_steps,
                    requires_web="web_search" in compound_steps,
                    requires_llm=True,
                    priority_applied=3,
                    mixed_steps=compound_steps,
                    flags=("mixed_task", "mixed_compound"),
                ),
                decision="mixed_decompose",
                reason="compound_mixed_task",
            )

        if ChatTextTaskIntentService.is_mixed_text_and_operational(normalized):
            steps = ChatIntentRouterHeuristicsService.mixed_task_steps(normalized)

            return ChatIntentRouterSupportService.with_decision(
                IntentRouteResult(
                    intent="mixed_task",
                    sub_intent="operational_then_text",
                    confidence=0.88,
                    requires_tool=True,
                    requires_rag=False,
                    requires_llm=True,
                    priority_applied=3,
                    mixed_steps=steps,
                    flags=("mixed_task",),
                ),
                decision="mixed_decompose",
                reason="operational_plus_text",
            )

        if ChatCanvasIntentService.is_canvas_request(normalized) or canvas_operational_update:
            return ChatIntentRouterSupportService.with_decision(
                IntentRouteResult(
                    intent="canvas_task",
                    sub_intent="operational_update" if canvas_operational_update else "placement",
                    confidence=0.9,
                    requires_tool=canvas_operational_update,
                    requires_canvas=True,
                    requires_rag=False,
                    requires_llm=not canvas_operational_update,
                    priority_applied=4,
                ),
                decision="canvas_route",
                reason="canvas_request",
            )

        from app.domain.services.chat_presentation_format_refinement_service import (
            ChatPresentationFormatRefinementService,
        )

        if ChatIntentRouterHeuristicsService.looks_presentation(normalized) and not (
            ChatPresentationFormatRefinementService.looks_like_format_refinement(normalized)
        ):
            return ChatIntentRouterSupportService.with_decision(
                IntentRouteResult(
                    intent="presentation_task",
                    sub_intent=ChatIntentRouterHeuristicsService.presentation_sub_intent(normalized),
                    confidence=0.86,
                    requires_tool=False,
                    requires_llm=True,
                    priority_applied=8,
                    flags=("presentation_task",),
                ),
                decision="presentation",
                reason="chart_or_table_request",
            )

        memory_entities = ChatIntentRouterEntityResolutionService.resolve_entities_from_memory(
            normalized,
            previous_messages=history,
            workspace_context=workspace_context,
        )
        resolved_params = ChatIntentRouterEntityResolutionService.build_resolved_params(
            normalized,
            previous_messages=history,
            memory_entities=memory_entities,
            workspace_context=workspace_context,
        )

        from app.domain.services.chat_follow_up_intent_service import ChatFollowUpIntentService

        is_follow_up = bool(memory_entities) or ChatFollowUpIntentService.is_operational_follow_up(
            normalized
        )

        from app.domain.services.chat_web_search_history_service import (
            ChatWebSearchHistoryService,
        )
        from app.domain.services.chat_web_search_source_follow_up_service import (
            ChatWebSearchSourceFollowUpService,
        )

        if history and ChatWebSearchHistoryService.has_recent_web_search(history):
            if ChatWebSearchSourceFollowUpService.is_list_sources_request(normalized):
                return ChatIntentRouterSupportService.with_decision(
                    IntentRouteResult(
                        intent="follow_up",
                        sub_intent="web_list_sources",
                        is_follow_up=True,
                        confidence=0.92,
                        requires_tool=False,
                        requires_rag=False,
                        requires_llm=False,
                        priority_applied=5,
                    ),
                    decision="follow_up",
                    reason="web_search_list_sources",
                )

            if ChatWebSearchSourceFollowUpService.is_summarize_request(normalized):
                return ChatIntentRouterSupportService.with_decision(
                    IntentRouteResult(
                        intent="follow_up",
                        sub_intent="web_summarize",
                        is_follow_up=True,
                        confidence=0.9,
                        requires_tool=False,
                        requires_rag=False,
                        requires_llm=False,
                        priority_applied=5,
                    ),
                    decision="follow_up",
                    reason="web_search_summarize",
                )

            if ChatWebSearchSourceFollowUpService.is_extract_params_request(normalized):
                return ChatIntentRouterSupportService.with_decision(
                    IntentRouteResult(
                        intent="follow_up",
                        sub_intent="web_extract_params",
                        is_follow_up=True,
                        confidence=0.9,
                        requires_tool=False,
                        requires_rag=False,
                        requires_llm=False,
                        priority_applied=5,
                    ),
                    decision="follow_up",
                    reason="web_search_extract_params",
                )

            if ChatWebSearchSourceFollowUpService.is_compare_sources_request(normalized):
                return ChatIntentRouterSupportService.with_decision(
                    IntentRouteResult(
                        intent="follow_up",
                        sub_intent="web_compare_sources",
                        is_follow_up=True,
                        confidence=0.9,
                        requires_tool=False,
                        requires_rag=False,
                        requires_llm=False,
                        priority_applied=5,
                    ),
                    decision="follow_up",
                    reason="web_search_compare_sources",
                )

        if history and ChatAnalysisIntentService.is_data_interpretation_request(normalized, history):
            return ChatIntentRouterSupportService.with_decision(
                IntentRouteResult(
                    intent="follow_up",
                    sub_intent="data_interpretation",
                    is_follow_up=True,
                    confidence=0.9,
                    requires_tool=False,
                    requires_rag=False,
                    requires_llm=True,
                    priority_applied=5,
                    resolved_params=resolved_params,
                ),
                decision="follow_up",
                reason="data_interpretation",
            )

        if analysis_mode or ChatAnalysisIntentService.is_comparison_or_insight_request(normalized):
            return ChatIntentRouterSupportService.with_decision(
                IntentRouteResult(
                    intent="operational_query",
                    sub_intent="analysis",
                    confidence=0.85,
                    requires_tool=True,
                    requires_rag=False,
                    requires_llm=True,
                    priority_applied=6,
                    flags=("analysis_mode",),
                    resolved_params=resolved_params,
                    is_follow_up=is_follow_up,
                ),
                decision="operational_action",
                reason="analysis_mode",
            )

        ambiguous, candidates = ChatIntentRouterHeuristicsService.operational_ambiguity(normalized, resolved_params)

        department_kpi = ChatIntentRouterHeuristicsService.resolve_department_kpi(normalized)

        if (
            operational_optimize
            or ChatIntentRouterHeuristicsService.looks_operational(normalized)
            or department_kpi
            or is_follow_up
        ):
            sub = ChatIntentRouterHeuristicsService.operational_sub_intent(normalized)

            if not sub and department_kpi:
                sub = "department_kpi"

            if is_follow_up and not sub:
                sub = ChatFollowUpIntentService.follow_up_type(normalized)
                sub = ChatIntentRouterHeuristicsService.map_follow_up_sub_intent(sub)

            return ChatIntentRouterSupportService.with_decision(
                IntentRouteResult(
                    intent="operational_query",
                    sub_intent=sub,
                    is_follow_up=is_follow_up,
                    confidence=0.63 if ambiguous else 0.82,
                    requires_tool=bool(allowed_action_ids),
                    requires_rag=False,
                    requires_llm=False,
                    priority_applied=6,
                    resolved_params=resolved_params,
                    ambiguous=ambiguous,
                    candidates=candidates,
                ),
                decision="operational_action" if not ambiguous else "clarify_operational",
                reason=(
                    "department_kpi_keywords"
                    if department_kpi and not ambiguous
                    else "operational_keywords"
                    if not ambiguous
                    else "ambiguous_operational_scope"
                ),
            )

        if attachment_ids:
            return ChatIntentRouterSupportService.with_decision(
                IntentRouteResult(
                    intent="attachment_task",
                    sub_intent="with_files",
                    confidence=0.8,
                    requires_tool=False,
                    requires_rag=True,
                    requires_llm=True,
                    priority_applied=7,
                ),
                decision="attachment_generic",
                reason="files_attached",
            )

        if not ChatIntentRouterHeuristicsService.blocks_web_search(normalized) and ChatIntentRouterHeuristicsService.looks_web_search(normalized):
            return ChatIntentRouterSupportService.with_decision(
                IntentRouteResult(
                    intent="web_search",
                    confidence=0.9,
                    requires_web=True,
                    requires_tool=True,
                    requires_rag=False,
                    requires_llm=True,
                    priority_applied=7,
                    flags=("web_search_explicit",),
                ),
                decision="web_search",
                reason="explicit_web_request",
            )

        if ChatIntentRouterHeuristicsService.looks_rag_document(normalized):
            return ChatIntentRouterSupportService.with_decision(
                IntentRouteResult(
                    intent="rag_question",
                    confidence=0.75,
                    requires_rag=True,
                    requires_llm=True,
                    priority_applied=8,
                    flags=("internal_document",),
                ),
                decision="rag_internal",
                reason="documental_wording",
            )

        if ChatIntentRouterHeuristicsService.looks_self_help(normalized):
            return ChatIntentRouterSupportService.with_decision(
                IntentRouteResult(
                    intent="self_help",
                    sub_intent="capabilities_catalog",
                    confidence=0.88,
                    requires_llm=False,
                    priority_applied=10,
                    flags=("self_help", "capabilities_catalog"),
                ),
                decision="self_help",
                reason="capabilities_question",
            )

        if ChatIntentRouterHeuristicsService.looks_identity_question(normalized):
            return ChatIntentRouterSupportService.with_decision(
                IntentRouteResult(
                    intent="identity",
                    confidence=0.88,
                    requires_llm=False,
                    priority_applied=10,
                ),
                decision="identity",
                reason="identity_question",
            )

        from app.domain.services.chat_small_talk_service import ChatSmallTalkService

        if ChatSmallTalkService.is_small_talk(normalized):
            return ChatIntentRouterSupportService.with_decision(
                IntentRouteResult(
                    intent="small_talk",
                    confidence=0.95,
                    requires_llm=False,
                    priority_applied=10,
                ),
                decision="small_talk",
                reason="greeting_or_thanks",
            )

        from app.domain.services.chat_utility_direct_answer_service import (
            ChatUtilityDirectAnswerService,
        )

        if ChatUtilityDirectAnswerService.build_direct_answer(message=normalized):
            return ChatIntentRouterSupportService.with_decision(
                IntentRouteResult(
                    intent="utility",
                    confidence=0.9,
                    requires_llm=False,
                    priority_applied=10,
                ),
                decision="utility_direct",
                reason="utility_pattern",
            )

        return ChatIntentRouterSupportService.with_decision(
            IntentRouteResult(
                intent="llm_general",
                confidence=0.5,
                requires_rag=True,
                requires_llm=True,
                priority_applied=11,
                flags=("low_confidence_fallback",),
            ),
            decision="llm_fallback",
            reason="no_clear_intent",
        )

