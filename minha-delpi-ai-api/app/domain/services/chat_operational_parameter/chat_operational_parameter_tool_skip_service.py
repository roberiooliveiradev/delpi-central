"""Delegate — parâmetros operacionais."""

from __future__ import annotations

from datetime import date

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_operational_refinement_service import (
    ChatOperationalRefinementService,
)
from app.domain.services.chat_conversation_context_service import ChatConversationContextService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)
from app.domain.services.chat_operational_parameter.chat_operational_parameter_constants import (
    INTENTS_REQUIRING_CODE,
)
from app.domain.services.chat_operational_parameter.chat_operational_parameter_facade_access import (
    operational_parameter_service,
)
from app.domain.services.chat_operational_parameter.chat_operational_parameter_types import (
    _parameter_content,
)



class ChatOperationalParameterToolSkipService:
    @classmethod
    def should_skip_tools(
        cls,
        message: str,
        *,
        conversation_context: str | None = None,
        previous_messages: list | None = None,
        memory_snapshot: dict | None = None,
    ) -> bool:
        from app.domain.services.chat_analysis_intent_service import (
            ChatAnalysisIntentService,
        )

        if ChatAnalysisIntentService.is_data_interpretation_request(
            message,
            previous_messages,
        ) and ChatConversationContextService.has_recent_tool_data(previous_messages):
            return True

        return operational_parameter_service()._missing_product_code_intent(
            message,
            conversation_context,
            previous_messages=previous_messages,
            memory_snapshot=memory_snapshot,
        ) is not None

    @classmethod
    def should_skip_agentic_loop(
        cls,
        message: str,
        *,
        conversation_context: str | None = None,
        tool_context: dict | None = None,
        previous_messages: list | None = None,
    ) -> bool:
        from app.domain.services.chat_fast_path_service import ChatFastPathService

        if ChatFastPathService.is_small_talk(message):
            return True

        from app.domain.services.chat_sql_authoring_guidance_service import (
            ChatSqlAuthoringGuidanceService,
        )

        # Authoring custom (crie sql…) não deve entrar no loop agentic de execute.
        if ChatSqlAuthoringGuidanceService.is_custom_sql_authoring(message):
            return True

        from app.domain.services.chat_follow_up_chip_query_service import (
            ChatFollowUpChipQueryService,
        )

        if ChatFollowUpChipQueryService.is_explicit_chip_query(message):
            return True

        from app.domain.services.chat_turn_mode_service import ChatTurnModeService

        if isinstance(tool_context, dict):
            turn_mode = ChatTurnModeService.resolve(
                message=message,
                tool_context=tool_context,
                direct_answer=tool_context.get("directAnswer"),
                tool_calls=tool_context.get("toolCalls"),
                pipeline_stages=list(tool_context.get("pipelineStages") or []),
            )

            if ChatTurnModeService.should_skip_agentic(turn_mode):
                return True

            analysis = tool_context.get("turnAnalysis")
            if isinstance(analysis, dict):
                decision = str(analysis.get("decision") or "").strip().lower()
                if decision in {"clarify", "narrate"}:
                    return True

                planned_ids = {
                    str(item).strip()
                    for item in (tool_context.get("turnAnalysisActionIds") or [])
                    if str(item).strip()
                }
                if planned_ids and cls._tool_calls_cover_action_ids(
                    tool_context.get("toolCalls") or [],
                    planned_ids,
                ):
                    return True

        from app.domain.services.chat_technical_description_intent_service import (
            ChatTechnicalDescriptionIntentService,
        )

        if ChatTechnicalDescriptionIntentService.requires_normas_knowledge(message):
            return True

        from app.domain.services.chat_web_search_intent_service import (
            ChatWebSearchIntentService,
        )

        if ChatWebSearchIntentService.blocks_external_action_selection(message):
            return True

        if operational_parameter_service().should_skip_tools(message, conversation_context=conversation_context):
            return True

        if ChatOperationalRefinementService.is_operational_follow_up(
            message,
            conversation_context=conversation_context,
            previous_messages=previous_messages,
        ):
            return True

        if not tool_context:
            return False

        from app.domain.services.chat_tool_context_presentation_service import (
            ChatToolContextPresentationService,
        )

        tool_calls = tool_context.get("toolCalls") or []

        from app.domain.services.chat_operational_pipeline_service import (
            ChatOperationalPipelineService,
        )

        if ChatOperationalPipelineService.should_optimize(message, None):
            for tool_call in tool_calls:
                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                metadata = tool_call.get("metadata") or {}

                if metadata.get("agenticStep"):
                    continue

                return True

        if isinstance(tool_context.get("directAnswer"), str) and str(
            tool_context.get("directAnswer") or ""
        ).strip():
            return True

        if tool_context.get("drawingAnalysisMode") and str(
            tool_context.get("directAnswer") or ""
        ).strip():
            return True

        if ChatToolContextPresentationService.should_answer_with_presentation_only(tool_calls):
            return True

        from app.domain.services.chat_product_overview_intent_service import (
            ChatProductOverviewIntentService,
        )

        if ChatProductOverviewIntentService.should_force_llm_synthesis(message, tool_calls):
            return False

        for tool_call in tool_calls:
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata") or {}

            if metadata.get("agenticStep"):
                continue

            if metadata.get("ok"):
                return True

        return False

    @classmethod
    def _tool_calls_cover_action_ids(
        cls,
        tool_calls: list,
        planned_ids: set[str],
    ) -> bool:
        if not planned_ids:
            return False

        executed: set[str] = set()
        for call in tool_calls or []:
            if not isinstance(call, dict):
                continue
            meta = call.get("metadata") if isinstance(call.get("metadata"), dict) else {}
            action_id = str(
                meta.get("actionId")
                or (call.get("arguments") or {}).get("actionId")
                or (call.get("arguments") or {}).get("action_id")
                or ""
            ).strip()
            if action_id and meta.get("ok") is not False:
                executed.add(action_id)

        return planned_ids.issubset(executed)

    @classmethod
    def should_block_semantic_action_fallback(
        cls,
        message: str,
        *,
        conversation_context: str | None = None,
    ) -> bool:
        from app.domain.services.chat_production_operational_intent_service import (
            ChatProductionOperationalIntentService,
        )
        from app.domain.services.chat_sql_intent_service import ChatSqlIntentService

        # SQL execute/authoring não deve cair em similaridade semântica (ex.: schedule/today).
        if ChatSqlIntentService.should_auto_execute_sql(message):
            return True

        if ChatSqlIntentService.is_authoring_request(message):
            return True

        if ChatProductionOperationalIntentService.matches_rest_route(message):
            return True

        from app.domain.services.chat_playbook_product_intent_service import (
            ChatPlaybookProductIntentService,
        )

        if ChatPlaybookProductIntentService.matches_playbook_product_intent(
            message
        ):
            return True

        from app.domain.services.chat_operational_follow_up_routing_service import (
            ChatOperationalFollowUpRoutingService,
        )

        if ChatOperationalFollowUpRoutingService.should_block_semantic_fallback(message):
            return True

        return operational_parameter_service().should_skip_tools(message, conversation_context=conversation_context)

