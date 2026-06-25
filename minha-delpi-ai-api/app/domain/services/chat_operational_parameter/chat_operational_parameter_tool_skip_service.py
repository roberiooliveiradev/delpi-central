"""Delegate — parâmetros operacionais."""

from __future__ import annotations

from datetime import date

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_operational_refinement_service import (
    ChatOperationalRefinementService,
)
from app.application.services.chat_conversation_context_service import ChatConversationContextService
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

        from app.domain.services.chat_follow_up_chip_query_service import (
            ChatFollowUpChipQueryService,
        )

        if ChatFollowUpChipQueryService.is_explicit_chip_query(message):
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

        from app.application.services.chat_tool_context_service import (
            ChatToolContextService,
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

        if ChatToolContextService.should_answer_with_presentation_only(tool_calls):
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
    def should_block_semantic_action_fallback(
        cls,
        message: str,
        *,
        conversation_context: str | None = None,
    ) -> bool:
        from app.domain.services.chat_production_operational_intent_service import (
            ChatProductionOperationalIntentService,
        )

        if ChatProductionOperationalIntentService.matches_rest_route(message):
            return True

        from app.application.services.chat_playbook_product_action_readiness_service import (
            ChatPlaybookProductActionReadinessService,
        )

        if ChatPlaybookProductActionReadinessService.matches_playbook_product_intent(
            message
        ):
            return True

        from app.domain.services.chat_operational_follow_up_routing_service import (
            ChatOperationalFollowUpRoutingService,
        )

        if ChatOperationalFollowUpRoutingService.should_block_semantic_fallback(message):
            return True

        return operational_parameter_service().should_skip_tools(message, conversation_context=conversation_context)

