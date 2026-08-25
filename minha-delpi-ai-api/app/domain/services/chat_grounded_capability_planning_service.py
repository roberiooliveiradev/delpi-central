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
from app.domain.services.chat_grounded_enrich_planning_service import (
    ChatGroundedEnrichPlanningService,
    ChatGroundedEnrichPlan,
)


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

        if ChatTurnGroundingService.should_enrich_before_insight(message, excerpt):
            enrich_plan = ChatGroundedEnrichPlanningService.build_plan(
                message=message,
                workspace_context=workspace_context,
                excerpt=excerpt,
                response_mode=(
                    str(workspace_context.get("responseMode") or "").strip() or None
                ),
            )

            if enrich_plan:
                return cls._plan_from_enrich_plan(
                    selection_service,
                    message=message,
                    allowed_action_ids=allowed_action_ids,
                    enrich_plan=enrich_plan,
                    previous_messages=previous_messages,
                )

            return cls._plan_enrich_insight_actions(
                selection_service,
                message=message,
                allowed_action_ids=allowed_action_ids,
                excerpt=excerpt,
                previous_messages=previous_messages,
                max_calls=max_calls,
            )

        if ChatTurnGroundingService.should_narrate_insight_only(message):
            return []

        if ChatTurnGroundingService.should_narrate_excerpt(message, excerpt):
            return []

        if not ChatTurnGroundingService.should_expand_from_excerpt(message, excerpt):
            return []

        explicit_codes = ChatAnalysisIntentService.extract_all_product_codes(message)

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
    def _plan_from_enrich_plan(
        cls,
        selection_service: Any,
        *,
        message: str,
        allowed_action_ids: list[str] | None,
        enrich_plan: ChatGroundedEnrichPlan,
        previous_messages: list | None = None,
    ) -> list[dict]:
        limit = enrich_plan.max_calls
        planned: list[dict] = []
        fan_out_cap = enrich_plan.max_fan_out

        for scope in enrich_plan.planned_scopes:
            if len(planned) >= limit:
                break

            intent, route_segment = cls._scope_to_intent(scope)

            for code in enrich_plan.product_codes[:fan_out_cap]:
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
                payload["reason"] = f"{enrich_plan.reason}:{scope}:{code}"
                planned.append(payload)

        return planned

    @classmethod
    def _plan_enrich_insight_actions(
        cls,
        selection_service: Any,
        *,
        message: str,
        allowed_action_ids: list[str] | None,
        excerpt: dict[str, Any],
        previous_messages: list | None = None,
        max_calls: int | None = None,
    ) -> list[dict]:
        product_codes = cls._resolve_enrich_product_codes(message, excerpt=excerpt)

        if not product_codes:
            return []

        artifact_key = ChatEntityCapabilityCatalogService.artifact_enrich_key(
            str(excerpt.get("entity") or "").strip() or None,
            str(excerpt.get("profileKey") or "").strip() or None,
        )
        scopes = ChatEntityCapabilityCatalogService.enrich_insight_scopes(artifact_key)

        if not scopes:
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
                payload["reason"] = f"grounded_enrich_insight:{scope}:{code}"
                planned.append(payload)

        return planned

    @classmethod
    def _dedupe_codes(cls, codes: list[str]) -> list[str]:
        ordered: list[str] = []

        for code in codes:
            token = str(code or "").strip()

            if token and token not in ordered:
                ordered.append(token)

        return ordered

    @classmethod
    def _resolve_product_codes(
        cls,
        message: str,
        *,
        excerpt: dict[str, Any],
        working_memory: dict[str, Any],
    ) -> list[str]:
        top_keys = [
            ChatProductQueryIntentService.normalize_product_code(str(item))
            for item in (excerpt.get("topKeys") or [])
            if str(item).strip()
        ]
        top_keys = [code for code in top_keys if code]

        referent_type = ChatTurnGroundingService.resolve_referent_component_type(message)

        if referent_type:
            typed_keys = cls._codes_for_component_type(excerpt, referent_type)

            if typed_keys:
                cap = ChatEntityCapabilityCatalogService.max_fan_out_keys()
                return cls._dedupe_codes(typed_keys)[:cap]

            # Pedido tipado (MP/PI) sem bucket: não cair no primeiro PI/topKey.
            return []

        from app.domain.services.chat_turn_grounding_content_service import (
            ChatTurnGroundingContentService,
        )

        fan_out = cls._message_requests_fan_out(message)

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
    def _resolve_enrich_product_codes(
        cls,
        message: str,
        *,
        excerpt: dict[str, Any],
    ) -> list[str]:
        referent_type = ChatTurnGroundingService.resolve_referent_component_type(message)

        if referent_type:
            typed_keys = cls._codes_for_component_type(excerpt, referent_type)

            if typed_keys:
                cap = ChatEntityCapabilityCatalogService.max_fan_out_keys()
                return cls._dedupe_codes(typed_keys)[:cap]

            return []

        merged: list[str] = []
        keys_by_type = excerpt.get("keysByComponentType")

        if isinstance(keys_by_type, dict):
            for values in keys_by_type.values():
                if not isinstance(values, list):
                    continue

                for item in values:
                    code = ChatProductQueryIntentService.normalize_product_code(str(item))

                    if code and code not in merged:
                        merged.append(code)

        if merged:
            cap = ChatEntityCapabilityCatalogService.max_fan_out_keys()
            return cls._dedupe_codes(merged)[:cap]

        if cls._message_requests_fan_out(message):
            top_keys = [
                ChatProductQueryIntentService.normalize_product_code(str(item))
                for item in (excerpt.get("topKeys") or [])
                if str(item).strip()
            ]
            top_keys = [code for code in top_keys if code]

            if top_keys:
                cap = ChatEntityCapabilityCatalogService.max_fan_out_keys()
                return top_keys[:cap]

        top_keys = [
            ChatProductQueryIntentService.normalize_product_code(str(item))
            for item in (excerpt.get("topKeys") or [])
            if str(item).strip()
        ]
        top_keys = [code for code in top_keys if code]

        return top_keys[:1]

    @classmethod
    def _codes_for_component_type(
        cls,
        excerpt: dict[str, Any],
        component_type: str,
    ) -> list[str]:
        keys_by_type = excerpt.get("keysByComponentType")

        if not isinstance(keys_by_type, dict):
            return []

        raw = keys_by_type.get(str(component_type or "").strip().upper())

        if not isinstance(raw, list):
            return []

        codes: list[str] = []

        for item in raw:
            code = ChatProductQueryIntentService.normalize_product_code(str(item))

            if code and code not in codes:
                codes.append(code)

        return codes

    @classmethod
    def _message_requests_fan_out(cls, message: str) -> bool:
        from app.domain.services.chat_turn_grounding_content_service import (
            ChatTurnGroundingContentService,
        )

        normalized = ChatMessageNormalizationService.normalize_for_matching(message) or ""

        if not normalized:
            return False

        for token in ChatTurnGroundingContentService.fan_out_on_referent_items():
            candidate = ChatMessageNormalizationService.normalize_for_matching(token)

            if candidate and candidate in normalized:
                return True

        return False

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
