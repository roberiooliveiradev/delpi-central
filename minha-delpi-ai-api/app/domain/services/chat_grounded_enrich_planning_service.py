"""Fusão de sinais para planejamento grounded enrich-insight."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain.services.chat_entity_capability_catalog_service import (
    ChatEntityCapabilityCatalogService,
    EntityEnrichGoal,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.domain.services.chat_response_mode_service import ChatResponseModeService
from app.domain.services.chat_turn_grounding_service import ChatTurnGroundingService


@dataclass(frozen=True)
class ChatGroundedEnrichPlan:
    planned_scopes: tuple[str, ...]
    product_codes: list[str]
    max_calls: int
    max_fan_out: int
    response_mode: str
    reason: str
    enrich_goals: tuple[EntityEnrichGoal, ...] = field(default_factory=tuple)


class ChatGroundedEnrichPlanningService:
    @classmethod
    def build_plan(
        cls,
        *,
        message: str,
        workspace_context: dict[str, Any] | None,
        excerpt: dict[str, Any],
        response_mode: str | None = None,
    ) -> ChatGroundedEnrichPlan | None:
        if not ChatTurnGroundingService.should_enrich_before_insight(message, excerpt):
            return None

        normalized_mode = ChatResponseModeService.normalize(response_mode)
        limits = ChatEntityCapabilityCatalogService.enrich_insight_limits_for_mode(
            normalized_mode
        )
        product_codes = cls._resolve_product_codes(
            message,
            workspace_context=workspace_context,
            excerpt=excerpt,
            max_fan_out=cls._resolve_fan_out_cap(limits),
        )
        max_calls = cls._resolve_max_calls(normalized_mode, limits)
        enrich_goals = cls._resolve_enrich_goals(
            message,
            workspace_context,
            excerpt,
            product_code=product_codes[0] if product_codes else None,
        )
        scopes = cls._resolve_scopes(
            message,
            workspace_context,
            excerpt,
            enrich_goals=enrich_goals,
        )

        if (not scopes and not enrich_goals) or not product_codes:
            return None

        return ChatGroundedEnrichPlan(
            planned_scopes=scopes,
            product_codes=product_codes,
            max_calls=max_calls,
            max_fan_out=cls._resolve_fan_out_cap(limits),
            response_mode=normalized_mode,
            reason=(
                "grounded_enrich_insight_goal_driven"
                if ChatEntityCapabilityCatalogService.cutover_enabled()
                else "grounded_enrich_insight"
            ),
            enrich_goals=enrich_goals,
        )

    @classmethod
    def should_preserve_rag(cls, workspace_context: dict[str, Any] | None) -> bool:
        workspace = workspace_context if isinstance(workspace_context, dict) else {}
        turn_grounding = workspace.get("turnGrounding")

        if not isinstance(turn_grounding, dict):
            return False

        if str(turn_grounding.get("stage") or "").strip() != "grounded_enrich_insight":
            return False

        skills = workspace.get("turnAnalysisSkillsToLoad")

        if isinstance(skills, list) and any(str(item).strip() for item in skills):
            return True

        turn_analysis = workspace.get("turnAnalysis")

        if isinstance(turn_analysis, dict):
            analysis_skills = turn_analysis.get("skillsToLoad")

            if isinstance(analysis_skills, list) and any(
                str(item).strip() for item in analysis_skills
            ):
                return True

        return False

    @classmethod
    def _resolve_product_codes(
        cls,
        message: str,
        *,
        workspace_context: dict[str, Any] | None,
        excerpt: dict[str, Any],
        max_fan_out: int,
    ) -> list[str]:
        codes = cls._resolve_enrich_product_codes(message, excerpt=excerpt)

        if codes:
            return codes[:max_fan_out]

        workspace = workspace_context if isinstance(workspace_context, dict) else {}
        working_memory = workspace.get("workingMemory")

        if isinstance(working_memory, dict):
            from app.domain.services.chat_user_context_item_service import (
                ChatUserContextItemService,
            )

            context_codes = ChatUserContextItemService.resolve_all_product_codes_from_items(
                working_memory.get("userContextItems"),
            )

            if context_codes:
                return context_codes[:max_fan_out]

            operational_focus = working_memory.get("operationalFocus")

            if isinstance(operational_focus, dict):
                focus_code = ChatProductQueryIntentService.normalize_product_code(
                    str(operational_focus.get("productCode") or ""),
                )

                if focus_code:
                    return [focus_code]

        return []

    @classmethod
    def _resolve_enrich_goals(
        cls,
        message: str,
        workspace_context: dict[str, Any] | None,
        excerpt: dict[str, Any],
        *,
        product_code: str | None,
    ) -> tuple[EntityEnrichGoal, ...]:
        if not ChatEntityCapabilityCatalogService.cutover_enabled():
            return ()

        goals = list(
            ChatEntityCapabilityCatalogService.enrich_goals_for_artifact(
                str(excerpt.get("entity") or "").strip() or None,
                str(excerpt.get("profileKey") or "").strip() or None,
                product_code=product_code,
            )
        )
        requested = cls._scopes_from_message(message)
        if requested:
            filtered = [goal for goal in goals if goal.scope_label in requested]
            if filtered:
                goals = filtered

        workspace = workspace_context if isinstance(workspace_context, dict) else {}
        preferred = cls._preferred_scopes_from_behavior(workspace)
        for scope in preferred:
            if any(goal.scope_label == scope for goal in goals):
                continue
            goals.append(
                EntityEnrichGoal(
                    goal_id=f"enrich_{scope}",
                    scope_label=scope,
                    intent=f"{scope} do produto {product_code or 'produto'}",
                    query_hints=(scope,),
                )
            )

        turn_analysis = (
            workspace.get("turnAnalysis")
            if isinstance(workspace.get("turnAnalysis"), dict)
            else {}
        )
        for scope in cls._scopes_from_turn_analysis(turn_analysis):
            if any(goal.scope_label == scope for goal in goals):
                continue
            goals.append(
                EntityEnrichGoal(
                    goal_id=f"enrich_{scope}",
                    scope_label=scope,
                    intent=f"{scope} do produto {product_code or 'produto'}",
                    query_hints=(scope,),
                )
            )

        return tuple(goals)

    @classmethod
    def _resolve_scopes(
        cls,
        message: str,
        workspace_context: dict[str, Any] | None,
        excerpt: dict[str, Any],
        *,
        enrich_goals: tuple[EntityEnrichGoal, ...] = (),
    ) -> tuple[str, ...]:
        if enrich_goals:
            return tuple(goal.scope_label for goal in enrich_goals if goal.scope_label)

        workspace = workspace_context if isinstance(workspace_context, dict) else {}
        artifact_key = ChatEntityCapabilityCatalogService.artifact_enrich_key(
            str(excerpt.get("entity") or "").strip() or None,
            str(excerpt.get("profileKey") or "").strip() or None,
        )
        base_scopes = ChatEntityCapabilityCatalogService.enrich_insight_scopes(artifact_key)
        requested = cls._scopes_from_message(message)
        turn_analysis = (
            workspace.get("turnAnalysis")
            if isinstance(workspace.get("turnAnalysis"), dict)
            else {}
        )
        analysis_scopes = cls._scopes_from_turn_analysis(turn_analysis)
        preferred = cls._preferred_scopes_from_behavior(workspace)

        if requested:
            scoped = [scope for scope in requested if scope in base_scopes] or list(requested)
        else:
            scoped = list(base_scopes)

        merged: list[str] = []

        for scope in (*scoped, *analysis_scopes, *preferred):
            token = str(scope or "").strip()

            if token and token not in merged:
                merged.append(token)

        return tuple(merged)

    @classmethod
    def _scopes_from_message(cls, message: str) -> tuple[str, ...]:
        from app.domain.services.chat_product_multi_scope_planning_service import (
            ChatProductMultiScopePlanningService,
        )

        return tuple(ChatProductMultiScopePlanningService.extract_requested_scopes(message))

    @classmethod
    def _scopes_from_turn_analysis(cls, turn_analysis: dict[str, Any]) -> tuple[str, ...]:
        action_ids = turn_analysis.get("actionIds")

        if not isinstance(action_ids, list):
            return ()

        scopes: list[str] = []

        for action_id in action_ids:
            token = str(action_id or "").strip().lower()

            if "stock" in token and "stock" not in scopes:
                scopes.append("stock")

            if any(marker in token for marker in ("summary", "profile", "description")):
                if "profile" not in scopes:
                    scopes.append("profile")

            if "structure" in token and "structure" not in scopes:
                scopes.append("structure")

        return tuple(scopes)

    @classmethod
    def _preferred_scopes_from_behavior(cls, workspace: dict[str, Any]) -> tuple[str, ...]:
        behavior = workspace.get("behaviorInstructions")

        if not isinstance(behavior, dict):
            return ()

        preferred = behavior.get("preferredEnrichScopes")

        if not isinstance(preferred, list):
            return ()

        return tuple(str(item).strip() for item in preferred if str(item).strip())

    @classmethod
    def _resolve_max_calls(cls, response_mode: str, limits: dict[str, int] | None = None) -> int:
        resolved = limits or ChatEntityCapabilityCatalogService.enrich_insight_limits_for_mode(
            response_mode
        )
        extra = int(resolved.get("maxExtraRoutes") or 0)

        if extra > 0:
            return extra

        return ChatEntityCapabilityCatalogService.max_extra_routes_per_turn()

    @classmethod
    def _resolve_fan_out_cap(cls, limits: dict[str, int] | None) -> int:
        fan_out = int((limits or {}).get("maxFanOut") or 0)

        if fan_out > 0:
            return fan_out

        return ChatEntityCapabilityCatalogService.max_fan_out_keys()

    @classmethod
    def _resolve_enrich_product_codes(
        cls,
        message: str,
        *,
        excerpt: dict[str, Any],
    ) -> list[str]:
        from app.domain.services.chat_grounded_capability_planning_service import (
            ChatGroundedCapabilityPlanningService,
        )

        return ChatGroundedCapabilityPlanningService._resolve_enrich_product_codes(
            message,
            excerpt=excerpt,
        )
