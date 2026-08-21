"""Critic declarativo pós-retrieve — follow-up só via routeId/clarifyKey do catálogo."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from app.domain.services.chat_anomaly_follow_up_planning_service import (
    ChatAnomalyFollowUpPlanningService,
)
from app.domain.services.chat_operational_sufficiency_critic_content_service import (
    ChatOperationalSufficiencyCriticContentService,
)
from app.domain.services.operational_route_registry_service import (
    OperationalRouteRegistryService,
)


@dataclass(frozen=True)
class SufficiencyVerdict:
    action: str  # sufficient | execute | chips
    plan_id: str | None = None
    reason_key: str = "sufficient"
    reason: str = ""
    follow_up_route_ids: list[str] = field(default_factory=list)
    clarify_key: str | None = None
    deferred_to_chips: bool = False


class ChatOperationalSufficiencyCriticService:
    @classmethod
    def evaluate(
        cls,
        *,
        tool_calls: list[dict] | None,
        enrichment_plan: dict | None = None,
        remaining_slots: int = 0,
        user_message: str | None = None,
        llm_classify: Callable[[dict[str, Any]], dict[str, Any] | None] | None = None,
    ) -> SufficiencyVerdict:
        _ = user_message
        calls = tool_calls if isinstance(tool_calls, list) else []
        enrichment = enrichment_plan if isinstance(enrichment_plan, dict) else {}

        heuristic = cls._evaluate_heuristic(
            calls=calls,
            enrichment=enrichment,
            remaining_slots=remaining_slots,
        )

        return cls.apply_llm_assist(
            heuristic,
            tool_calls=calls,
            enrichment_plan=enrichment,
            remaining_slots=remaining_slots,
            llm_classify=llm_classify,
        )

    @classmethod
    def apply_llm_assist(
        cls,
        heuristic: SufficiencyVerdict,
        *,
        tool_calls: list[dict],
        enrichment_plan: dict,
        remaining_slots: int,
        llm_classify: Callable[[dict[str, Any]], dict[str, Any] | None] | None = None,
    ) -> SufficiencyVerdict:
        if not ChatOperationalSufficiencyCriticContentService.llm_assist_enabled():
            return heuristic

        if not callable(llm_classify):
            return heuristic

        if heuristic.action != "sufficient":
            return heuristic

        if not cls._looks_uncertain(tool_calls, enrichment_plan):
            return heuristic

        try:
            raw = llm_classify(
                {
                    "planIds": ChatOperationalSufficiencyCriticContentService.plan_ids(),
                    "clarifyKeys": ChatOperationalSufficiencyCriticContentService.clarify_keys(),
                    "systemPrompt": ChatOperationalSufficiencyCriticContentService.llm_system_prompt(),
                }
            )
        except Exception:
            return heuristic

        resolved = cls.resolve_from_llm_classification(
            raw if isinstance(raw, dict) else {},
            remaining_slots=remaining_slots,
            fallback=heuristic,
        )
        return resolved

    @classmethod
    def resolve_from_llm_classification(
        cls,
        raw: dict[str, Any],
        *,
        remaining_slots: int,
        fallback: SufficiencyVerdict,
    ) -> SufficiencyVerdict:
        plan_id = str(raw.get("followUpPlanId") or "").strip() or None
        clarify_key = str(raw.get("clarifyKey") or "").strip() or None
        verdict = str(raw.get("verdict") or "").strip()
        allowed = {
            str(item).strip()
            for item in (
                ChatOperationalSufficiencyCriticContentService.llm_assist_node().get(
                    "allowedVerdicts"
                )
                or []
            )
            if str(item).strip()
        }

        if verdict and allowed and verdict not in allowed:
            return fallback

        if plan_id and plan_id not in ChatOperationalSufficiencyCriticContentService.plan_ids():
            return SufficiencyVerdict(
                action=fallback.action,
                plan_id=fallback.plan_id,
                reason_key="invalidLlmPlan",
                reason=ChatOperationalSufficiencyCriticContentService.reason("invalidLlmPlan"),
                follow_up_route_ids=list(fallback.follow_up_route_ids),
                clarify_key=fallback.clarify_key,
                deferred_to_chips=fallback.deferred_to_chips,
            )

        if clarify_key and clarify_key not in ChatOperationalSufficiencyCriticContentService.clarify_keys():
            return SufficiencyVerdict(
                action=fallback.action,
                plan_id=fallback.plan_id,
                reason_key="invalidLlmPlan",
                reason=ChatOperationalSufficiencyCriticContentService.reason("invalidLlmPlan"),
                follow_up_route_ids=list(fallback.follow_up_route_ids),
                clarify_key=fallback.clarify_key,
                deferred_to_chips=fallback.deferred_to_chips,
            )

        if plan_id:
            plan = ChatOperationalSufficiencyCriticContentService.plan_by_id(plan_id)
            return cls._verdict_from_plan(plan, remaining_slots=remaining_slots) or fallback

        if clarify_key:
            return SufficiencyVerdict(
                action="chips",
                plan_id=None,
                reason_key="deferredToChips",
                reason=ChatOperationalSufficiencyCriticContentService.reason("deferredToChips"),
                clarify_key=clarify_key,
                deferred_to_chips=True,
            )

        if verdict == "sufficient":
            return fallback

        return fallback

    @classmethod
    def _looks_uncertain(
        cls,
        tool_calls: list[dict],
        enrichment: dict,
    ) -> bool:
        if int(enrichment.get("skippedByCap") or 0) > 0:
            return True

        for item in tool_calls:
            if not isinstance(item, dict):
                continue
            if str(item.get("name") or "") != "execute_external_action":
                continue
            meta = item.get("metadata")
            if not isinstance(meta, dict) or not meta.get("ok"):
                continue
            if meta.get("emptyResult"):
                return True
            anomalies = meta.get("anomalies")
            if isinstance(anomalies, list) and anomalies:
                return True

        return False

    @classmethod
    def _verdict_from_plan(
        cls,
        plan: dict[str, Any],
        *,
        remaining_slots: int,
    ) -> SufficiencyVerdict | None:
        if not plan:
            return None

        plan_id = str(plan.get("id") or "").strip()
        then = plan.get("then") if isinstance(plan.get("then"), dict) else {}
        reason_key = str(plan.get("reasonKey") or "sufficient").strip() or "sufficient"
        reason = ChatOperationalSufficiencyCriticContentService.reason(reason_key)
        clarify_key = str(then.get("clarifyKey") or "").strip() or None
        route_ids = [
            str(item).strip()
            for item in (then.get("followUpRouteIds") or [])
            if str(item).strip()
        ]

        try:
            max_follow = max(0, int(then.get("maxAutoFollowUps")))
        except (TypeError, ValueError):
            max_follow = (
                ChatOperationalSufficiencyCriticContentService.max_auto_follow_ups_default()
            )

        if clarify_key and not route_ids:
            return SufficiencyVerdict(
                action="chips",
                plan_id=plan_id,
                reason_key=reason_key,
                reason=reason,
                clarify_key=clarify_key,
                deferred_to_chips=True,
            )

        if route_ids and max_follow > 0:
            capped = route_ids[:max_follow]
            if remaining_slots > 0:
                return SufficiencyVerdict(
                    action="execute",
                    plan_id=plan_id,
                    reason_key=reason_key,
                    reason=reason,
                    follow_up_route_ids=capped[:remaining_slots],
                    clarify_key=clarify_key,
                )
            return SufficiencyVerdict(
                action="chips",
                plan_id=plan_id,
                reason_key="deferredToChips",
                reason=ChatOperationalSufficiencyCriticContentService.reason("deferredToChips"),
                follow_up_route_ids=capped,
                clarify_key=clarify_key,
                deferred_to_chips=True,
            )

        return None

    @classmethod
    def _evaluate_heuristic(
        cls,
        *,
        calls: list[dict],
        enrichment: dict,
        remaining_slots: int,
    ) -> SufficiencyVerdict:
        for plan in ChatOperationalSufficiencyCriticContentService.plans():
            if not cls._plan_matches(plan, calls, enrichment):
                continue

            plan_id = str(plan.get("id") or "").strip()
            then = plan.get("then") if isinstance(plan.get("then"), dict) else {}
            reason_key = str(plan.get("reasonKey") or "sufficient").strip() or "sufficient"
            reason = ChatOperationalSufficiencyCriticContentService.reason(reason_key)
            clarify_key = str(then.get("clarifyKey") or "").strip() or None
            route_ids = [
                str(item).strip()
                for item in (then.get("followUpRouteIds") or [])
                if str(item).strip()
            ]

            if then.get("skipAlreadyExecutedPaths"):
                route_ids = cls._filter_unused_route_ids(route_ids, calls)

            try:
                max_follow = max(0, int(then.get("maxAutoFollowUps")))
            except (TypeError, ValueError):
                max_follow = (
                    ChatOperationalSufficiencyCriticContentService.max_auto_follow_ups_default()
                )

            if clarify_key and not route_ids:
                return SufficiencyVerdict(
                    action="chips",
                    plan_id=plan_id,
                    reason_key=reason_key,
                    reason=reason,
                    clarify_key=clarify_key,
                    deferred_to_chips=True,
                )

            if route_ids and max_follow > 0:
                capped = route_ids[:max_follow]

                if remaining_slots > 0:
                    return SufficiencyVerdict(
                        action="execute",
                        plan_id=plan_id,
                        reason_key=reason_key,
                        reason=reason,
                        follow_up_route_ids=capped[:remaining_slots],
                        clarify_key=clarify_key,
                    )

                return SufficiencyVerdict(
                    action="chips",
                    plan_id=plan_id,
                    reason_key="deferredToChips",
                    reason=ChatOperationalSufficiencyCriticContentService.reason(
                        "deferredToChips"
                    ),
                    follow_up_route_ids=capped,
                    clarify_key=clarify_key,
                    deferred_to_chips=True,
                )

        return SufficiencyVerdict(
            action="sufficient",
            reason_key="sufficient",
            reason=ChatOperationalSufficiencyCriticContentService.reason("sufficient"),
        )

    @classmethod
    def plan_follow_up_selections(
        cls,
        selection_service: Any,
        *,
        verdict: SufficiencyVerdict,
        message: str,
        tool_calls: list[dict] | None,
        allowed_action_ids: list[str] | None,
        previous_messages: list | None = None,
        select_registry_route_id: Callable[..., dict | None] | None = None,
    ) -> list[dict]:
        if verdict.action != "execute" or not verdict.follow_up_route_ids:
            return []

        # Reusa seleção/registry do anomaly planner com um plano sintético.
        synthetic = {
            str(verdict.plan_id or "sufficiency"): {
                "anomalyTypes": ["negative_value", "zero_value", "empty_list"],
                "profileKeys": [],
                "pathMarkers": [],
                "followUpRouteIds": list(verdict.follow_up_route_ids),
                "maxFollowUps": len(verdict.follow_up_route_ids),
            }
        }

        # Seleção direta por routeId (sem depender do match de anomaly).
        resolve = select_registry_route_id or getattr(
            selection_service,
            "select_registry_route_id",
            None,
        )
        already_action_ids = {
            str((item.get("arguments") or {}).get("actionId") or "").strip()
            for item in (tool_calls or [])
            if isinstance(item, dict)
        }
        already_paths = {
            str((item.get("metadata") or {}).get("path") or "").lower()
            for item in (tool_calls or [])
            if isinstance(item, dict)
        }
        follow_ups: list[dict] = []

        for route_key in verdict.follow_up_route_ids:
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
                selected = ChatAnomalyFollowUpPlanningService._select_product_route(
                    selection_service,
                    route_id=route_key,
                    message=message,
                    tool_calls=tool_calls or [],
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

            already_action_ids.add(action_id)
            item = dict(selected)
            item["reason"] = verdict.reason or ChatOperationalSufficiencyCriticContentService.reason(
                verdict.reason_key
            )
            item["sufficiencyFollowUp"] = {
                "planId": verdict.plan_id,
                "routeId": route_key,
            }
            item["anomalyFollowUp"] = {
                "planId": verdict.plan_id,
                "routeId": route_key,
            }
            follow_ups.append(item)

        _ = synthetic
        return follow_ups

    @classmethod
    def build_clarification_suggestions(
        cls,
        *,
        verdict: SufficiencyVerdict,
        tool_calls: list[dict] | None,
        message: str = "",
        enrichment_plan: dict | None = None,
    ) -> list[dict[str, str]]:
        if verdict.action != "chips" and not verdict.clarify_key:
            return []

        clarify_key = verdict.clarify_key

        if clarify_key == "clarifyInvoiceDirection":
            return ChatAnomalyFollowUpPlanningService.build_clarification_suggestions(
                tool_calls,
                message=message,
            ) or cls._invoice_chips_from_catalog(tool_calls, message=message)

        if clarify_key == "deferredScopes":
            return cls._deferred_scope_chips(
                enrichment_plan if isinstance(enrichment_plan, dict) else {},
                tool_calls=tool_calls,
                message=message,
            )

        if verdict.follow_up_route_ids and verdict.deferred_to_chips:
            return cls._route_id_chips(
                verdict.follow_up_route_ids,
                tool_calls=tool_calls,
                message=message,
            )

        return []

    @classmethod
    def audit_payload(cls, verdict: SufficiencyVerdict) -> dict[str, Any]:
        return {
            "verdict": verdict.action,
            "planId": verdict.plan_id,
            "reasonKey": verdict.reason_key,
            "reason": verdict.reason,
            "executedRouteIds": list(verdict.follow_up_route_ids)
            if verdict.action == "execute"
            else [],
            "deferredToChips": bool(verdict.deferred_to_chips),
            "clarifyKey": verdict.clarify_key,
        }

    @classmethod
    def _plan_matches(
        cls,
        plan: dict[str, Any],
        tool_calls: list[dict],
        enrichment: dict[str, Any],
    ) -> bool:
        when = plan.get("when") if isinstance(plan.get("when"), dict) else {}

        if when.get("enrichmentSkippedByCap"):
            skipped = int(enrichment.get("skippedByCap") or 0)

            if skipped < 1:
                return False

            return True

        enrichment_kind = str(when.get("enrichmentKind") or "").strip()

        if enrichment_kind:
            if str(enrichment.get("kind") or "").strip() != enrichment_kind:
                return False

            planned_min = when.get("enrichmentPlannedMin")

            if planned_min is not None:
                planned = enrichment.get("plannedScopes") or []
                count = len(planned) if isinstance(planned, list) else 0

                if count < int(planned_min):
                    return False

            ok_max = when.get("okCountMax")

            if ok_max is not None:
                ok_count = sum(
                    1
                    for item in tool_calls
                    if isinstance(item, dict)
                    and str(item.get("name") or "") == "execute_external_action"
                    and isinstance(item.get("metadata"), dict)
                    and item["metadata"].get("ok")
                )

                if ok_count > int(ok_max):
                    return False

            return True

        anomaly_plan = {
            "anomalyTypes": when.get("anomalyTypes") or [],
            "profileKeys": when.get("profileKeys") or [],
            "pathMarkers": when.get("pathMarkers") or [],
        }

        if not any(anomaly_plan.values()):
            return False

        return ChatAnomalyFollowUpPlanningService._plan_matches_tool_calls(
            anomaly_plan,
            tool_calls,
        )

    @classmethod
    def _filter_unused_route_ids(
        cls,
        route_ids: list[str],
        tool_calls: list[dict],
    ) -> list[str]:
        paths = {
            str((item.get("metadata") or {}).get("path") or "").lower()
            for item in tool_calls
            if isinstance(item, dict)
        }
        markers = {
            "productSales": "/sales",
            "productStock": "/stock",
            "productSummary": "/summary",
            "productPurchases": "/purchases",
        }
        unused: list[str] = []

        for route_id in route_ids:
            marker = markers.get(route_id)

            if marker and any(marker in path for path in paths):
                continue

            unused.append(route_id)

        return unused

    @classmethod
    def _invoice_chips_from_catalog(
        cls,
        tool_calls: list[dict] | None,
        *,
        message: str,
    ) -> list[dict[str, str]]:
        node = ChatOperationalSufficiencyCriticContentService.clarify_node(
            "clarifyInvoiceDirection"
        )
        code = (
            ChatAnomalyFollowUpPlanningService._product_code_from_tool_calls(
                tool_calls or [],
                message,
            )
            or "{code}"
        )
        suggestions: list[dict[str, str]] = []

        for side in ("inbound", "outbound"):
            side_node = node.get(side) if isinstance(node.get(side), dict) else {}
            label = str(side_node.get("label") or "").strip()
            template = str(side_node.get("queryTemplate") or "").strip()
            query = template.replace("{code}", code) if template else ""

            if label and query:
                suggestions.append({"label": label, "query": query})

        return suggestions

    @classmethod
    def _deferred_scope_chips(
        cls,
        enrichment: dict[str, Any],
        *,
        tool_calls: list[dict] | None,
        message: str,
    ) -> list[dict[str, str]]:
        scopes = enrichment.get("plannedScopes") or []

        if not isinstance(scopes, list):
            return []

        executed = int(enrichment.get("executedCount") or 0)
        deferred = [str(s).strip() for s in scopes[executed:] if str(s).strip()]
        node = ChatOperationalSufficiencyCriticContentService.clarify_node("deferredScopes")
        code = (
            ChatAnomalyFollowUpPlanningService._product_code_from_tool_calls(
                tool_calls or [],
                message,
            )
            or "{code}"
        )
        label_t = str(node.get("labelTemplate") or "Consultar {scope}").strip()
        query_t = str(node.get("queryTemplate") or "{scope} do produto {code}").strip()
        chips: list[dict[str, str]] = []

        for scope in deferred[:4]:
            chips.append(
                {
                    "label": label_t.replace("{scope}", scope).replace("{code}", code),
                    "query": query_t.replace("{scope}", scope).replace("{code}", code),
                }
            )

        return chips

    @classmethod
    def _route_id_chips(
        cls,
        route_ids: list[str],
        *,
        tool_calls: list[dict] | None,
        message: str,
    ) -> list[dict[str, str]]:
        code = (
            ChatAnomalyFollowUpPlanningService._product_code_from_tool_calls(
                tool_calls or [],
                message,
            )
            or "{code}"
        )
        catalog = ChatOperationalSufficiencyCriticContentService.clarify_node(
            "routeFollowUps"
        )
        chips: list[dict[str, str]] = []

        for route_id in route_ids:
            node = catalog.get(route_id) if isinstance(catalog.get(route_id), dict) else {}
            label = str(node.get("label") or "").strip()
            template = str(node.get("queryTemplate") or "").strip()

            if not label or not template:
                continue

            chips.append(
                {
                    "label": label,
                    "query": template.replace("{code}", code),
                }
            )

        return chips
