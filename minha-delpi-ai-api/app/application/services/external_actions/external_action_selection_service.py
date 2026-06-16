from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
from app.domain.services.chat_route_context_service import ChatRouteContextService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)
from app.application.services.external_actions.external_action_route_selection_service import (
    ExternalActionRouteSelectionService,
)
from app.application.services.external_actions.external_action_product_search_route_selection_service import (
    ExternalActionProductSearchRouteSelectionService,
)
from app.application.services.external_actions.external_action_selection_support_service import (
    ExternalActionSelectionSupportService,
)
from app.application.services.external_actions.external_action_selection_dispatch_service import (
    ExternalActionSelectionDispatchService,
)


class ExternalActionSelectionService:
    HIERARCHICAL_PRODUCT_MAX_DEPTH = 15

    def __init__(self, repository, semantic_ranker=None):
        self.repository = repository
        self.semantic_ranker = semantic_ranker
        self._route_selection = ExternalActionRouteSelectionService(repository)
        self._support = ExternalActionSelectionSupportService(
            repository,
            semantic_ranker=semantic_ranker,
        )
        self._dispatch = ExternalActionSelectionDispatchService(
            self._route_selection,
            self._support,
        )

    def select_action_for_product(
        self,
        message: str,
        *,
        product_code: str,
        allowed_action_ids: list[str] | None = None,
        intent: str | None = None,
        route_segment: str | None = None,
        previous_messages: list | None = None,
    ) -> dict | None:
        code = ChatProductQueryIntentService.normalize_product_code(product_code)

        if not code or ChatAnalysisIntentService.looks_like_path_placeholder(code):
            return None

        resolved_intent = intent or ChatProductQueryIntentService.detect(message)
        resolved_segment = route_segment or ChatRouteContextService.resolve_product_route_segment(
            message
        )
        preferred_action_id = None

        if previous_messages and resolved_intent == ChatProductQueryIntent.STOCK:
            preferred_action_id = self._support.resolve_previous_external_action_id(
                previous_messages,
                path_fragment="/stock",
            )

        return self._select_product_action(
            message,
            code,
            allowed_action_ids=allowed_action_ids or [],
            intent=resolved_intent,
            route_segment=resolved_segment,
            preferred_action_id=preferred_action_id,
            previous_messages=previous_messages,
        )

    def select_action(
        self,
        message: str,
        allowed_action_ids: list[str] | None = None,
        conversation_context: str | None = None,
        previous_messages: list | None = None,
        *,
        raw_message: str | None = None,
        memory_snapshot: dict | None = None,
    ) -> dict | None:
        return self._dispatch.dispatch(
            message,
            allowed_action_ids=allowed_action_ids or [],
            conversation_context=conversation_context,
            previous_messages=previous_messages,
            raw_message=raw_message,
            memory_snapshot=memory_snapshot,
        )

    @staticmethod
    def _looks_like_product_search(value: str) -> bool:
        return ExternalActionProductSearchRouteSelectionService.looks_like_product_search(
            value
        )

    def _build_date_branch_parameters(
        self,
        action: dict,
        message: str,
        *,
        previous_messages: list | None = None,
    ) -> dict:
        return self._route_selection.parameter_builder.build_date_branch(
            action,
            message,
            previous_messages=previous_messages,
        )

    def _select_product_action(
        self,
        message: str,
        product_code: str,
        allowed_action_ids: list[str],
        intent: str = ChatProductQueryIntent.FULL,
        route_segment: str | None = None,
        preferred_action_id: str | None = None,
        previous_messages: list | None = None,
    ) -> dict | None:
        return self._route_selection.select_product(
            message,
            product_code,
            allowed_action_ids=allowed_action_ids,
            intent=intent,
            route_segment=route_segment,
            preferred_action_id=preferred_action_id,
            candidates_loader=self._list_allowed_candidates,
            previous_messages=previous_messages,
        )

    def _build_product_parameters(
        self,
        action: dict,
        code: str,
        *,
        message: str | None = None,
        previous_messages: list | None = None,
    ) -> dict:
        return self._route_selection.build_product_parameters(
            action,
            code,
            message=message,
            previous_messages=previous_messages,
        )

    def _list_allowed_candidates(
        self,
        message: str,
        *,
        allowed_action_ids: list[str],
        limit: int,
    ) -> list[dict]:
        return self._support.list_allowed_candidates(
            message,
            allowed_action_ids=allowed_action_ids,
            limit=limit,
        )
