"""Planejamento de dossier multi-rota para overview vago de produto (Playbook agentic)."""

from __future__ import annotations

from typing import Any, Callable

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_product_multi_scope_planning_service import (
    ChatProductMultiScopePlanningService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)
from app.domain.services.operational_route_registry_service import (
    OperationalRouteRegistryService,
)

_BUNDLE = "product_enrichment_composition"


class ChatProductEnrichmentCompositionPlanningService:
    @classmethod
    def looks_like_product_overview(cls, message: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if any(
            str(term).strip() and str(term) in normalized
            for term in ChatAssistantContentService.list(_BUNDLE, "narrowExcludeTerms")
        ):
            return False

        # Escopos explícitos (estoque, vendas, …) ficam no multi-scope / rota única.
        if ChatProductMultiScopePlanningService.extract_requested_scopes(message):
            return False

        return cls._has_overview_trigger(normalized)

    @classmethod
    def _has_overview_trigger(cls, normalized: str) -> bool:
        triggers = ChatAssistantContentService.list(_BUNDLE, "triggerTerms")

        return any(str(term).strip() and str(term) in normalized for term in triggers)

    @classmethod
    def should_use_analyser_only(cls, message: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        return any(
            str(term).strip() and str(term) in normalized
            for term in ChatAssistantContentService.list(_BUNDLE, "analyserOnlyTerms")
        )

    @classmethod
    def compose_route_ids(cls, *, include_optional: bool = False) -> list[str]:
        ids = [
            str(item).strip()
            for item in ChatAssistantContentService.list(_BUNDLE, "composeRouteIds")
            if str(item).strip()
        ]

        if include_optional:
            for item in ChatAssistantContentService.list(_BUNDLE, "optionalRouteIds"):
                route_id = str(item).strip()

                if route_id and route_id not in ids:
                    ids.append(route_id)

        return ids

    @classmethod
    def plan(
        cls,
        selection_service: Any,
        *,
        message: str,
        product_code: str,
        allowed_action_ids: list[str] | None,
        previous_messages: list | None = None,
        max_calls: int = 4,
        select_registry_route_id: Callable[..., dict | None] | None = None,
    ) -> list[dict]:
        code = ChatProductQueryIntentService.normalize_product_code(product_code)

        if not code:
            return []

        if cls.should_use_analyser_only(message):
            selected = selection_service.select_action_for_product(
                message,
                product_code=code,
                allowed_action_ids=allowed_action_ids,
                intent=ChatProductQueryIntent.ANALYSER,
                previous_messages=previous_messages,
            )

            if not selected:
                return []

            item = dict(selected)
            item["reason"] = cls._reason("analyser")
            return [item]

        if not cls.looks_like_product_overview(message):
            return []

        route_ids = cls.compose_route_ids(include_optional=False)
        min_compose = int(
            ChatAssistantContentService.get(_BUNDLE, "minComposeRoutes", default="2") or "2"
        )

        if len(route_ids) < min_compose:
            return []

        resolve = select_registry_route_id or getattr(
            selection_service,
            "select_registry_route_id",
            None,
        )
        limit = max(1, min(int(max_calls), 12))
        planned: list[dict] = []
        seen_action_ids: set[str] = set()

        for index, route_id in enumerate(route_ids):
            if len(planned) >= limit:
                break

            if not OperationalRouteRegistryService.route_by_id(route_id):
                continue

            selected = None

            if callable(resolve):
                selected = resolve(
                    route_id,
                    message,
                    allowed_action_ids=allowed_action_ids or [],
                    previous_messages=previous_messages,
                )

            if not isinstance(selected, dict):
                selected = cls._select_via_product_intent(
                    selection_service,
                    route_id=route_id,
                    message=message,
                    product_code=code,
                    allowed_action_ids=allowed_action_ids,
                    previous_messages=previous_messages,
                )

            if not isinstance(selected, dict):
                continue

            action_id = str(
                (selected.get("arguments") or {}).get("actionId") or ""
            ).strip()

            if not action_id or action_id in seen_action_ids:
                continue

            seen_action_ids.add(action_id)
            item = dict(selected)
            item["reason"] = cls._reason_for_route(route_id, index=index)
            item["enrichmentScope"] = route_id
            planned.append(item)

        if len(planned) < min_compose:
            return planned if planned else []

        return planned

    @classmethod
    def _select_via_product_intent(
        cls,
        selection_service: Any,
        *,
        route_id: str,
        message: str,
        product_code: str,
        allowed_action_ids: list[str] | None,
        previous_messages: list | None,
    ) -> dict | None:
        mapping = {
            "productSummary": (ChatProductQueryIntent.DESCRIPTION, None),
            "productDescription": (ChatProductQueryIntent.DESCRIPTION, None),
            "productStock": (ChatProductQueryIntent.STOCK, "stock"),
            "productSales": (ChatProductQueryIntent.SALES, "sales"),
            "productPurchases": (ChatProductQueryIntent.FULL, "purchases"),
            "productAnalyser": (ChatProductQueryIntent.ANALYSER, None),
        }
        intent, segment = mapping.get(route_id, (None, None))

        if intent is None:
            return None

        return selection_service.select_action_for_product(
            message,
            product_code=product_code,
            allowed_action_ids=allowed_action_ids,
            intent=intent,
            route_segment=segment,
            previous_messages=previous_messages,
        )

    @classmethod
    def _reason_for_route(cls, route_id: str, *, index: int) -> str:
        key_by_route = {
            "productSummary": "primary",
            "productDescription": "primary",
            "productStock": "stock",
            "productSales": "sales",
            "productPurchases": "purchases",
            "productAnalyser": "analyser",
        }
        key = key_by_route.get(route_id) or ("primary" if index == 0 else "compose")

        return cls._reason(key)

    @classmethod
    def _reason(cls, key: str) -> str:
        return str(
            ChatAssistantContentService.get(
                _BUNDLE,
                "selectionReasons",
                key,
                default="Consulta operacional do dossier do produto.",
            )
        )

    @classmethod
    def anomaly_follow_up_plans(cls) -> dict[str, Any]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "anomalyFollowUpPlans")

        return node if isinstance(node, dict) else {}
