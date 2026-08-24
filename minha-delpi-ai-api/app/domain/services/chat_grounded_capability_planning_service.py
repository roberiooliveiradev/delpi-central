"""Planejamento de rotas extras a partir do excerpt grounded (follow-up)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
from app.domain.services.chat_entity_capability_catalog_service import (
    ChatEntityCapabilityCatalogService,
)
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
from app.domain.services.chat_turn_grounding_service import ChatTurnGroundingService


class ChatGroundedCapabilityPlanningService:
    @classmethod
    def plan_actions(
        cls,
        selection_service: Any,
        *,
        message: str,
        allowed_action_ids: list[str] | None,
        workspace_context: dict | None,
        previous_messages: list | None = None,
        max_calls: int | None = None,
    ) -> list[dict]:
        if not selection_service or not allowed_action_ids:
            return []

        if not isinstance(workspace_context, dict):
            return []

        turn_grounding = workspace_context.get("turnGrounding") or {}

        if turn_grounding.get("status") != "grounded":
            return []

        working = workspace_context.get("workingMemory") or {}
        excerpt = working.get("lastResultExcerpt") if isinstance(working, dict) else None

        if not isinstance(excerpt, dict):
            excerpt = turn_grounding.get("excerpt")

        if not isinstance(excerpt, dict):
            return []

        if ChatTurnGroundingService.should_narrate_excerpt(message, excerpt):
            return []

        if not ChatTurnGroundingService.should_expand_from_excerpt(message, excerpt):
            return []

        explicit_codes = ChatAnalysisIntentService.extract_product_codes_for_action_planning(
            message,
            None,
            previous_messages=previous_messages,
            memory_snapshot=working if isinstance(working, dict) else None,
        )

        if explicit_codes:
            return []

        scopes = ChatProductMultiScopePlanningService.extract_requested_scopes(message)

        if not scopes:
            return []

        product_codes = cls._resolve_product_codes(
            message,
            excerpt=excerpt,
            working_memory=working if isinstance(working, dict) else {},
        )

        if not product_codes:
            return []

        limit = min(
            cls._resolve_max_calls(max_calls),
            ChatEntityCapabilityCatalogService.max_extra_routes_per_turn(),
        )
        planned: list[dict] = []

        for scope in scopes:
            if len(planned) >= limit:
                break

            intent, route_segment = cls._scope_to_intent(scope)

            for code in product_codes:
                if len(planned) >= limit:
                    break

                selected = selection_service.select_action_for_product(
                    message,
                    product_code=code,
                    allowed_action_ids=allowed_action_ids,
                    intent=intent,
                    route_segment=route_segment,
                    previous_messages=previous_messages,
                )

                if not selected:
                    continue

                payload = dict(selected)
                payload["reason"] = f"grounded_follow_up:{scope}:{code}"
                planned.append(payload)

        return planned

    @classmethod
    def _resolve_product_codes(
        cls,
        message: str,
        *,
        excerpt: dict[str, Any],
        working_memory: dict[str, Any],
    ) -> list[str]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message) or ""
        top_keys = [
            ChatProductQueryIntentService.normalize_product_code(str(item))
            for item in (excerpt.get("topKeys") or [])
            if str(item).strip()
        ]
        top_keys = [code for code in top_keys if code]

        from app.domain.services.chat_turn_grounding_content_service import (
            ChatTurnGroundingContentService,
        )

        fan_out = any(
            token in normalized
            for token in ChatTurnGroundingContentService.fan_out_on_referent_items()
            if ChatMessageNormalizationService.normalize_for_matching(token) in normalized
        )

        if fan_out and top_keys:
            cap = ChatEntityCapabilityCatalogService.max_fan_out_keys()
            return top_keys[:cap]

        operational_focus = working_memory.get("operationalFocus") or {}
        focus_code = ChatProductQueryIntentService.normalize_product_code(
            str(operational_focus.get("productCode") or ""),
        )

        if focus_code:
            return [focus_code]

        if top_keys:
            return [top_keys[0]]

        return []

    @classmethod
    def _scope_to_intent(cls, scope: str) -> tuple[str, str | None]:
        mapping = {
            "profile": (ChatProductQueryIntent.DESCRIPTION, None),
            "stock": (ChatProductQueryIntent.STOCK, "stock"),
            "sales": (ChatProductQueryIntent.SALES, "sales"),
            "structure": (ChatProductQueryIntent.STRUCTURE, "structure"),
            "parents": (ChatProductQueryIntent.PARENTS, "parents"),
            "purchases": (ChatProductQueryIntent.FULL, "purchases"),
            "suppliers": (ChatProductQueryIntent.FULL, "suppliers"),
        }

        return mapping.get(scope, (ChatProductQueryIntent.FULL, None))

    @staticmethod
    def _resolve_max_calls(max_calls: int | None) -> int:
        if max_calls is None:
            return ChatEntityCapabilityCatalogService.max_extra_routes_per_turn()

        return max(1, min(int(max_calls), 12))
