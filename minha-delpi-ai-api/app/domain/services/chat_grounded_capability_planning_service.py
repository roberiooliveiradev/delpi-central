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

        stage = str(turn_grounding.get("stage") or "").strip()

        if stage == "grounded_revise_query":
            follow_up = turn_grounding.get("followUp") if isinstance(turn_grounding, dict) else None
            slot_delta = (
                follow_up.get("slotDelta")
                if isinstance(follow_up, dict) and isinstance(follow_up.get("slotDelta"), dict)
                else {}
            )
            revised = cls._plan_revise_last_query(
                selection_service,
                message=message,
                allowed_action_ids=allowed_action_ids,
                working_memory=working if isinstance(working, dict) else {},
                previous_messages=previous_messages,
                slot_delta=slot_delta,
            )
            return revised

        if stage in {
            "grounded_challenge_result",
            "grounded_clarify_slot",
            "grounded_narrate_recap",
            "grounded_narrate_insight",
        }:
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
    def _plan_revise_last_query(
        cls,
        selection_service: Any,
        *,
        message: str,
        allowed_action_ids: list[str] | None,
        working_memory: dict[str, Any],
        previous_messages: list | None = None,
        slot_delta: dict[str, Any] | None = None,
    ) -> list[dict]:
        last_action = working_memory.get("lastAction")

        if not isinstance(last_action, dict) or not last_action:
            return []

        target_path = str(last_action.get("path") or "").strip()
        target_operation = str(
            last_action.get("operationId") or last_action.get("operation_id") or ""
        ).strip()
        target_action_id = str(
            last_action.get("actionId") or last_action.get("action_id") or ""
        ).strip()

        if not (target_path or target_operation or target_action_id):
            return []

        matched = cls._resolve_action_from_last(
            selection_service,
            message=message,
            allowed_action_ids=allowed_action_ids or [],
            target_path=target_path,
            target_operation=target_operation,
            target_action_id=target_action_id,
        )

        if not matched:
            return []

        from app.domain.services.operational_api_parameter_builder_service import (
            OperationalApiParameterBuilderService,
        )
        from app.domain.services.external_actions.external_action_response_content_service import (
            ExternalActionResponseContentService,
        )

        base_params = (
            dict(last_action.get("params") or {})
            if isinstance(last_action.get("params"), dict)
            else {}
        )
        builder = OperationalApiParameterBuilderService()
        merged = builder.build_date_branch(
            matched,
            message,
            previous_messages=previous_messages,
            base_params=base_params,
        )

        delta = slot_delta if isinstance(slot_delta, dict) else {}
        for key in ("branch", "start_date", "end_date"):
            value = delta.get(key)
            if value not in (None, ""):
                merged[key] = str(value)

        payload = {
            "name": "execute_external_action",
            "arguments": {
                "actionId": matched.get("actionId"),
                "parameters": merged,
                "body": {"message": message},
            },
            "reason": ExternalActionResponseContentService.get(
                "selectionReasons",
                "reviseLastQuery",
                default="Reexecução da última consulta com filtros atualizados.",
            ),
            "path": matched.get("path"),
            "operationId": matched.get("operationId"),
            "actionId": matched.get("actionId"),
            "parameters": merged,
        }
        return [payload]

    @classmethod
    def _resolve_action_from_last(
        cls,
        selection_service: Any,
        *,
        message: str,
        allowed_action_ids: list[str],
        target_path: str,
        target_operation: str,
        target_action_id: str,
    ) -> dict | None:
        if target_action_id and hasattr(selection_service, "select_registry_route_id"):
            # Preferência por id explícito quando lastAction trouxe actionId de registry.
            try:
                selected = selection_service.select_registry_route_id(
                    target_action_id,
                    message,
                    allowed_action_ids=allowed_action_ids,
                )
                if isinstance(selected, dict) and selected:
                    return selected
            except TypeError:
                pass

        support = getattr(selection_service, "_support", None)
        list_candidates = getattr(support, "list_allowed_candidates", None) if support else None
        if not callable(list_candidates):
            list_candidates = getattr(selection_service, "_list_allowed_candidates", None)

        candidates: list[dict] = []
        if callable(list_candidates):
            candidates = list_candidates(
                message,
                allowed_action_ids=allowed_action_ids,
                limit=200,
            ) or []

        if not candidates:
            repository = getattr(selection_service, "repository", None)
            list_actions = getattr(repository, "list_actions", None) if repository else None
            if callable(list_actions):
                candidates = [
                    action
                    for action in list_actions()
                    if str(action.get("actionId") or "") in set(allowed_action_ids)
                ]

        path_norm = target_path.rstrip("/").lower()
        op_norm = target_operation.lower()
        id_norm = target_action_id.lower()

        for action in candidates:
            if not isinstance(action, dict):
                continue
            action_id = str(action.get("actionId") or "").strip().lower()
            operation_id = str(action.get("operationId") or "").strip().lower()
            path = str(action.get("path") or "").strip().rstrip("/").lower()
            if id_norm and action_id == id_norm:
                return action
            if op_norm and operation_id == op_norm:
                return action
            if path_norm and (path == path_norm or path.endswith(path_norm) or path_norm.endswith(path)):
                return action

        return None

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
