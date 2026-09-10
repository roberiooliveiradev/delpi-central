"""Planejamento de composição departamental por goals + Action Catalog (E5.S5).

Taxonomia de departamento (`department_idd`) permanece canônica.
`primaryRouteId` / `composeRouteIds` estão deprecated (observer até E5.S7).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_operational_api_domain_service import (
    ChatOperationalApiDomainService,
)
from app.domain.services.openapi_when_not_to_use_guidance_service import (
    OpenApiWhenNotToUseGuidanceService,
)
from app.domain.services.operational_api_parameter_builder_service import (
    OperationalApiParameterBuilderService,
)

_BUNDLE = "department_meta_composition"


@dataclass(frozen=True)
class DepartmentMetaGoal:
    goal_id: str
    intent: str
    query_hints: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "goalId": self.goal_id,
            "intent": self.intent,
            "queryHints": list(self.query_hints),
        }


class ChatDepartmentMetaCompositionPlanningService:
    @classmethod
    def looks_like_department_meta_composition(cls, message: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        triggers = ChatAssistantContentService.list(_BUNDLE, "triggerTerms")

        return any(str(term).strip() and str(term) in normalized for term in triggers)

    @classmethod
    def resolve_department_id(cls, message: str | None) -> str | None:
        spec = ChatOperationalApiDomainService.parameter_strategy_spec("department_idd")
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized or not isinstance(spec, dict):
            return None

        resolved = OperationalApiParameterBuilderService._resolve_source_value(
            "department_id_regex",
            {"source": "department_id_regex", "matchAliases": ["department_id"]},
            spec,
            {"normalized": normalized},
        )
        value = str(resolved or "").strip().lower()

        return value or None

    @classmethod
    def composition_mode(cls, message: str | None) -> str:
        """``primary`` (meta curta) vs ``compose`` (painel / indicadores / visão integrada)."""
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        default_mode = str(
            ChatAssistantContentService.get(_BUNDLE, "defaultMode", default="primary")
            or "primary"
        ).strip().lower()

        if default_mode not in {"primary", "compose"}:
            default_mode = "primary"

        if not normalized:
            return default_mode

        full_terms = ChatAssistantContentService.list(
            _BUNDLE,
            "composeModeTerms",
            "full",
        )

        if any(str(term).strip() and str(term) in normalized for term in full_terms):
            return "compose"

        return default_mode

    @classmethod
    def cutover_enabled(cls) -> bool:
        raw = ChatAssistantContentService.get_node(_BUNDLE, "cutoverEnabled")
        if raw is None:
            return True
        return bool(raw)

    @classmethod
    def route_maps_deprecated(cls) -> bool:
        return bool(
            ChatAssistantContentService.get_node(_BUNDLE, "routeMapsDeprecated")
        )

    @classmethod
    def goals_for_department(
        cls,
        department_id: str,
        *,
        mode: str = "compose",
    ) -> list[DepartmentMetaGoal]:
        dept = str(department_id or "").strip().lower()
        mode_key = "compose" if str(mode or "").strip().lower() == "compose" else "primary"
        node = ChatAssistantContentService.get_node(_BUNDLE, "semanticGoals", mode_key)
        if not isinstance(node, list):
            return []

        goals: list[DepartmentMetaGoal] = []
        for item in node:
            if not isinstance(item, dict):
                continue
            goal_id = str(item.get("goalId") or "").strip()
            template = str(item.get("intentTemplate") or "").strip()
            if not goal_id or not template:
                continue
            hints = [
                str(hint).strip().lower()
                for hint in (item.get("queryHints") or [])
                if str(hint).strip()
            ]
            dept_hints = item.get("departmentQueryHints")
            if isinstance(dept_hints, dict):
                for hint in dept_hints.get(dept) or []:
                    text = str(hint).strip().lower()
                    if text and text not in hints:
                        hints.append(text)
            goals.append(
                DepartmentMetaGoal(
                    goal_id=goal_id,
                    intent=template.format(department_id=dept or "departamento"),
                    query_hints=tuple(hints),
                )
            )
        return goals

    @classmethod
    def route_ids_for_department(
        cls,
        department_id: str,
        *,
        mode: str = "compose",
    ) -> list[str]:
        """Legacy observer — maps deprecated (E5.S5). Prefer ``goals_for_department``."""
        node = ChatAssistantContentService.get_node(
            _BUNDLE,
            "byDepartment",
            str(department_id or "").strip().lower(),
        )

        if not isinstance(node, dict):
            return []

        primary = str(node.get("primaryRouteId") or "").strip()
        compose = node.get("composeRouteIds") or []
        route_ids: list[str] = []

        if primary:
            route_ids.append(primary)

        if mode == "compose" and isinstance(compose, list):
            for item in compose:
                route_id = str(item or "").strip()

                if route_id and route_id not in route_ids:
                    route_ids.append(route_id)

        return route_ids

    @classmethod
    def plan(
        cls,
        selection_service: Any = None,
        *,
        message: str,
        allowed_action_ids: list[str] | None,
        previous_messages: list | None = None,
        max_calls: int = 5,
        select_registry_route_id: Callable[..., dict | None] | None = None,
        actions_by_id: dict[str, dict[str, Any]] | None = None,
    ) -> list[dict]:
        _ = previous_messages
        _ = select_registry_route_id
        _ = selection_service
        return cls.plan_goal_driven(
            message=message,
            allowed_action_ids=allowed_action_ids,
            actions_by_id=actions_by_id,
            max_calls=max_calls,
        )

    @classmethod
    def plan_goal_driven(
        cls,
        *,
        message: str,
        allowed_action_ids: list[str] | None,
        actions_by_id: dict[str, dict[str, Any]] | None,
        max_calls: int = 5,
    ) -> list[dict]:
        if not cls.cutover_enabled():
            return []
        if not cls.looks_like_department_meta_composition(message):
            return []

        department_id = cls.resolve_department_id(message)
        if not department_id:
            return []

        mode = cls.composition_mode(message)
        goals = cls.goals_for_department(department_id, mode=mode)
        if not goals:
            return []

        allowed = [
            str(item).strip()
            for item in (allowed_action_ids or [])
            if str(item).strip()
        ]
        if not allowed:
            return []

        catalog = {
            str(action_id).strip(): dict(action)
            for action_id, action in (actions_by_id or {}).items()
            if str(action_id).strip() and isinstance(action, dict)
        }
        if not catalog:
            return []

        limit = max(1, min(int(max_calls), 12))
        planned: list[dict] = []
        seen_action_ids: set[str] = set()
        reason = str(
            ChatAssistantContentService.get(
                _BUNDLE,
                "selectionReasons",
                "goalDriven",
                default=(
                    "Action escolhida por goal semântico + Action Catalog "
                    "(sem routeId fixo)."
                ),
            )
        )

        for goal in goals:
            if len(planned) >= limit:
                break
            selected = cls._select_action_for_goal(
                goal,
                message=message,
                allowed_action_ids=allowed,
                catalog=catalog,
                exclude_action_ids=seen_action_ids,
            )
            if selected is None:
                continue
            action_id = str(selected.get("actionId") or "").strip()
            if not action_id or action_id in seen_action_ids:
                continue
            seen_action_ids.add(action_id)
            planned.append(
                cls._to_tool_call(
                    selected,
                    department_id=department_id,
                    goal=goal,
                    reason=reason,
                )
            )

        if mode == "compose" and len(planned) < 1:
            return []
        return planned

    @classmethod
    def _select_action_for_goal(
        cls,
        goal: DepartmentMetaGoal,
        *,
        message: str,
        allowed_action_ids: list[str],
        catalog: dict[str, dict[str, Any]],
        exclude_action_ids: set[str],
    ) -> dict[str, Any] | None:
        candidates = [
            catalog[action_id]
            for action_id in allowed_action_ids
            if action_id in catalog and action_id not in exclude_action_ids
        ]
        if not candidates:
            return None

        query = " ".join(
            part
            for part in (goal.intent, message, " ".join(goal.query_hints))
            if part
        )
        filtered = OpenApiWhenNotToUseGuidanceService.filter_candidates(
            query,
            candidates,
            raw_action_of=lambda item: item,
        )
        preferred = OpenApiWhenNotToUseGuidanceService.prefer_candidates(
            query,
            filtered or candidates,
            raw_action_of=lambda item: item,
        )
        ranked = cls._rank_by_hints(preferred or filtered or candidates, goal)
        return ranked[0] if ranked else None

    @classmethod
    def _rank_by_hints(
        cls,
        candidates: list[dict[str, Any]],
        goal: DepartmentMetaGoal,
    ) -> list[dict[str, Any]]:
        hints = tuple(hint for hint in goal.query_hints if hint)

        def score(action: dict[str, Any]) -> tuple[int, str]:
            haystack = " ".join(
                [
                    str(action.get("whenToUse") or ""),
                    str(action.get("summary") or ""),
                    str(action.get("description") or ""),
                    str(action.get("actionId") or ""),
                    str(action.get("operationId") or ""),
                ]
            ).lower()
            hits = sum(1 for hint in hints if hint and hint in haystack)
            action_id = str(action.get("actionId") or "")
            return (-hits, action_id)

        return sorted(candidates, key=score)

    @classmethod
    def _to_tool_call(
        cls,
        action: dict[str, Any],
        *,
        department_id: str,
        goal: DepartmentMetaGoal,
        reason: str,
    ) -> dict[str, Any]:
        action_id = str(action.get("actionId") or action.get("action_id") or "").strip()
        return {
            "name": "execute_external_action",
            "arguments": {
                "actionId": action_id,
                "parameters": {"department_id": department_id},
            },
            "reason": reason,
            "metadata": {
                "selectionMode": "openapi_first",
                "compositionRole": "department_meta",
                "departmentMetaGoalDriven": True,
                "goalId": goal.goal_id,
                "goalIntent": goal.intent,
                "departmentId": department_id,
                "actionId": action_id,
                "providerKey": action.get("providerKey"),
                "operationId": action.get("operationId") or action.get("operation_id"),
                "path": action.get("path"),
                "method": action.get("method"),
                "routeMapsDeprecated": cls.route_maps_deprecated(),
            },
        }
