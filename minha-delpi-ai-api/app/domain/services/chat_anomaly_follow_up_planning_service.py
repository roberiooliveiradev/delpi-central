"""Follow-up de tools após anomalias — plano declarativo (product enrichment JSON)."""

from __future__ import annotations

from typing import Any, Callable

from app.domain.services.chat_product_enrichment_composition_planning_service import (
    ChatProductEnrichmentCompositionPlanningService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)
from app.domain.services.operational_route_registry_service import (
    OperationalRouteRegistryService,
)


class ChatAnomalyFollowUpPlanningService:
    @classmethod
    def plan_from_tool_calls(
        cls,
        selection_service: Any,
        *,
        message: str,
        tool_calls: list[dict] | None,
        allowed_action_ids: list[str] | None,
        remaining_slots: int,
        previous_messages: list | None = None,
        select_registry_route_id: Callable[..., dict | None] | None = None,
    ) -> list[dict]:
        if remaining_slots < 1 or not isinstance(tool_calls, list):
            return []

        plans = ChatProductEnrichmentCompositionPlanningService.anomaly_follow_up_plans()

        if not plans:
            return []

        already_paths = {
            str((item.get("metadata") or {}).get("path") or "").lower()
            for item in tool_calls
            if isinstance(item, dict)
        }
        already_action_ids = {
            str((item.get("arguments") or {}).get("actionId") or "").strip()
            for item in tool_calls
            if isinstance(item, dict)
        }

        resolve = select_registry_route_id or getattr(
            selection_service,
            "select_registry_route_id",
            None,
        )
        follow_ups: list[dict] = []
        seen_routes: set[str] = set()

        for plan_id, plan in plans.items():
            if not isinstance(plan, dict):
                continue

            if not cls._plan_matches_tool_calls(plan, tool_calls):
                continue

            max_follow = max(0, int(plan.get("maxFollowUps") or 0))

            if max_follow < 1:
                continue

            for route_id in plan.get("followUpRouteIds") or []:
                route_key = str(route_id or "").strip()

                if not route_key or route_key in seen_routes:
                    continue

                if len(follow_ups) >= remaining_slots or len(follow_ups) >= max_follow:
                    break

                if not OperationalRouteRegistryService.route_by_id(route_key):
                    continue

                selected = None

                if callable(resolve):
                    selected = resolve(
                        route_key,
                        message,
                        allowed_action_ids=allowed_action_ids or [],
                        previous_messages=previous_messages,
                    )

                if not isinstance(selected, dict):
                    selected = cls._select_product_route(
                        selection_service,
                        route_id=route_key,
                        message=message,
                        tool_calls=tool_calls,
                        allowed_action_ids=allowed_action_ids,
                        previous_messages=previous_messages,
                    )

                if not isinstance(selected, dict):
                    continue

                action_id = str(
                    (selected.get("arguments") or {}).get("actionId") or ""
                ).strip()

                if not action_id or action_id in already_action_ids:
                    continue

                path_hint = str(
                    (selected.get("arguments") or {}).get("path")
                    or selected.get("path")
                    or ""
                ).lower()

                if path_hint and any(path_hint in existing for existing in already_paths):
                    continue

                seen_routes.add(route_key)
                already_action_ids.add(action_id)
                item = dict(selected)
                item["reason"] = cls._reason(plan_id, route_key)
                item["anomalyFollowUp"] = {
                    "planId": plan_id,
                    "routeId": route_key,
                }
                follow_ups.append(item)

        return follow_ups

    @classmethod
    def _plan_matches_tool_calls(
        cls,
        plan: dict[str, Any],
        tool_calls: list[dict],
    ) -> bool:
        anomaly_types = {
            str(item).strip()
            for item in (plan.get("anomalyTypes") or [])
            if str(item).strip()
        }
        profile_keys = {
            str(item).strip()
            for item in (plan.get("profileKeys") or [])
            if str(item).strip()
        }
        path_markers = [
            str(item).strip().lower()
            for item in (plan.get("pathMarkers") or [])
            if str(item).strip()
        ]

        for tool_call in tool_calls:
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict) or not metadata.get("ok"):
                continue

            path = str(metadata.get("path") or "").lower()

            if path_markers and not any(marker in path for marker in path_markers):
                if profile_keys:
                    profile = cls._profile_key(metadata)

                    if profile not in profile_keys:
                        continue
                else:
                    continue
            elif profile_keys:
                profile = cls._profile_key(metadata)

                if profile not in profile_keys:
                    continue

            anomalies = metadata.get("anomalies") or (
                (metadata.get("dataAnswer") or {}).get("anomalies")
                if isinstance(metadata.get("dataAnswer"), dict)
                else None
            ) or (
                (metadata.get("dataCommentary") or {}).get("anomalies")
                if isinstance(metadata.get("dataCommentary"), dict)
                else None
            )

            if not isinstance(anomalies, list):
                if metadata.get("emptyResult") and "empty_list" in anomaly_types:
                    return True

                continue

            for anomaly in anomalies:
                if not isinstance(anomaly, dict):
                    continue

                if str(anomaly.get("type") or "").strip() in anomaly_types:
                    return True

        return False

    @classmethod
    def _profile_key(cls, metadata: dict[str, Any]) -> str:
        commentary = metadata.get("dataCommentary")

        if isinstance(commentary, dict):
            profile = str(commentary.get("profileKey") or "").strip()

            if profile:
                return profile

        data_answer = metadata.get("dataAnswer")

        if isinstance(data_answer, dict):
            return str(data_answer.get("profileKey") or "").strip()

        return ""

    @classmethod
    def _select_product_route(
        cls,
        selection_service: Any,
        *,
        route_id: str,
        message: str,
        tool_calls: list[dict],
        allowed_action_ids: list[str] | None,
        previous_messages: list | None,
    ) -> dict | None:
        code = cls._product_code_from_tool_calls(tool_calls, message)

        if not code:
            return None

        mapping = {
            "productSales": (ChatProductQueryIntent.SALES, "sales"),
            "productStock": (ChatProductQueryIntent.STOCK, "stock"),
            "productPurchases": (ChatProductQueryIntent.FULL, "purchases"),
        }
        intent, segment = mapping.get(route_id, (None, None))

        if intent is None:
            return None

        return selection_service.select_action_for_product(
            message,
            product_code=code,
            allowed_action_ids=allowed_action_ids,
            intent=intent,
            route_segment=segment,
            previous_messages=previous_messages,
        )

    @classmethod
    def _product_code_from_tool_calls(
        cls,
        tool_calls: list[dict],
        message: str,
    ) -> str:
        for tool_call in tool_calls:
            metadata = tool_call.get("metadata") if isinstance(tool_call, dict) else None

            if not isinstance(metadata, dict):
                continue

            path = str(metadata.get("path") or "")
            parts = [part for part in path.split("/") if part]

            if len(parts) >= 2 and parts[0] == "products" and parts[1].isalnum():
                return ChatProductQueryIntentService.normalize_product_code(parts[1]) or ""

            for key in ("productCode", "code"):
                value = str(metadata.get(key) or "").strip()

                if value:
                    return ChatProductQueryIntentService.normalize_product_code(value) or ""

        return (
            ChatProductQueryIntentService.normalize_product_code(
                ChatProductQueryIntentService.resolve_product_code(message) or ""
            )
            or ""
        )

    @classmethod
    def _reason(cls, plan_id: str, route_id: str) -> str:
        base = ChatProductEnrichmentCompositionPlanningService._reason("compose")
        return f"{base} (follow-up {plan_id}/{route_id})"
