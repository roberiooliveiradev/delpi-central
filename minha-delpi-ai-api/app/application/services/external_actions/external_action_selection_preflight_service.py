"""Guards e SQL preflight antes do loop DOCIE — Fase 11."""

from __future__ import annotations

from typing import Callable

from app.application.services.chat_conversation_context_service import (
    ChatConversationContextService,
)
from app.application.services.external_actions.external_action_sql_fallback_policy_service import (
    ExternalActionSqlFallbackPolicyService,
)
from app.application.services.external_actions.external_action_route_selection_service import (
    ExternalActionRouteSelectionService,
)
from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
from app.domain.services.chat_canvas_intent_service import ChatCanvasIntentService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_production_operational_intent_service import (
    ChatProductionOperationalIntentService,
)
from app.domain.services.chat_sql_intent_service import ChatSqlIntentService
from app.domain.services.chat_sql_query_refinement_service import (
    ChatSqlQueryRefinementService,
)
from app.domain.services.chat_technical_description_intent_service import (
    ChatTechnicalDescriptionIntentService,
)
from app.domain.services.chat_web_search_intent_service import (
    ChatWebSearchIntentService,
)
from app.domain.services.chat_web_search_source_follow_up_service import (
    ChatWebSearchSourceFollowUpService,
)
from app.domain.services.operational_route_matcher_service import (
    OperationalRouteMatcherService,
)
from app.domain.services.operational_route_registry_service import (
    OperationalRouteRegistryService,
)


class ExternalActionSelectionPreflightService:
    """Bloqueios e fast paths SQL antes de ``sessionRefinement`` / registry."""

    @staticmethod
    def blocks_selection(
        message: str,
        *,
        previous_messages: list | None = None,
    ) -> bool:
        if ChatAnalysisIntentService.is_data_interpretation_request(
            message,
            previous_messages,
        ) and ChatConversationContextService.has_recent_tool_data(previous_messages):
            return True

        if ChatAnalysisIntentService.is_comparison_or_insight_request(message):
            if not ChatProductionOperationalIntentService.matches_rest_route(message):
                return True

        if ChatCanvasIntentService.blocks_external_action_selection(message):
            return True

        if ChatWebSearchIntentService.blocks_external_action_selection(message):
            return True

        if ChatWebSearchSourceFollowUpService.blocks_external_action_selection(
            message,
            previous_messages,
        ):
            return True

        if ChatTechnicalDescriptionIntentService.requires_normas_knowledge(message):
            return True

        return False

    @staticmethod
    def try_sql_authoring_system_metadata(
        message: str,
        *,
        route_selection: ExternalActionRouteSelectionService,
        allowed_action_ids: list[str],
        candidates_loader: Callable[..., list[dict]],
    ) -> dict | None | str:
        """Retorna action, None (bloqueia seleção) ou ``skip`` se não for authoring."""

        if not ChatSqlIntentService.is_authoring_request(message):
            return "skip"

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if OperationalRouteMatcherService.looks_like_system_metadata_question(normalized):
            return route_selection.select_system_metadata(
                message,
                allowed_action_ids=allowed_action_ids,
                candidates_loader=candidates_loader,
            )

        return None

    @staticmethod
    def try_preflight_sql_policies(
        message: str,
        *,
        sql_source: str,
        allowed_action_ids: list[str],
        select_sql: Callable[..., dict | None],
        action_repository=None,
    ) -> dict | None:
        for policy in OperationalRouteRegistryService.preflight_sql_fallback_policies():
            selected = ExternalActionSqlFallbackPolicyService.try_policy(
                policy,
                message=message,
                sql_source=sql_source,
                allowed_action_ids=allowed_action_ids,
                select_sql=select_sql,
                action_repository=action_repository,
            )

            if selected:
                return selected

        return None

    @staticmethod
    def blocks_sql_show_mode(
        message: str,
        *,
        previous_messages: list | None = None,
    ) -> bool:
        sql_refinement = ChatSqlQueryRefinementService.resolve(
            message,
            previous_messages=previous_messages,
        )

        return bool(sql_refinement and sql_refinement.mode == "show_sql")

    @staticmethod
    def try_sql_refinement_execute(
        message: str,
        *,
        sql_source: str,
        allowed_action_ids: list[str],
        previous_messages: list | None = None,
        select_sql: Callable[..., dict | None],
    ) -> dict | None:
        sql_refinement = ChatSqlQueryRefinementService.resolve(
            message,
            previous_messages=previous_messages,
        )

        if not sql_refinement or sql_refinement.mode != "execute":
            return None

        return ExternalActionSqlFallbackPolicyService.try_sql_refinement(
            message=message,
            sql_source=sql_source,
            allowed_action_ids=allowed_action_ids,
            previous_messages=previous_messages,
            select_sql=select_sql,
            policy=OperationalRouteRegistryService.sql_refinement_policy(),
        )
