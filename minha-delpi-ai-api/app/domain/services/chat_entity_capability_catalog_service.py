"""Catálogo declarativo de capacidades operacionais por domínio (E5.S7).

Authority de enrichment = ``semanticGoals`` + caps de budget.
Maps ``scopeToRouteId`` / ``enrichInsightScopes`` / ``artifactToEnrichKey`` removidos.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "entity_capability_catalog"


@dataclass(frozen=True)
class EntityEnrichGoal:
    goal_id: str
    scope_label: str
    intent: str
    query_hints: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "goalId": self.goal_id,
            "scopeLabel": self.scope_label,
            "intent": self.intent,
            "queryHints": list(self.query_hints),
        }


class ChatEntityCapabilityCatalogService:
    @classmethod
    def limit_int(cls, key: str, default: int) -> int:
        node = ChatAssistantContentService.get_node(_BUNDLE, "limits") or {}

        if not isinstance(node, dict):
            return default

        try:
            return int(node.get(key, default))
        except (TypeError, ValueError):
            return default

    @classmethod
    def max_extra_routes_per_turn(cls) -> int:
        return cls.limit_int("maxExtraRoutesPerTurn", 4)

    @classmethod
    def max_fan_out_keys(cls) -> int:
        return cls.limit_int("maxFanOutKeys", 8)

    @classmethod
    def enrich_artifact_group(
        cls,
        entity: str | None,
        profile_key: str | None = None,
    ) -> str:
        """Resolve semantic goal group without routeId authority."""
        node = ChatAssistantContentService.get_node(
            _BUNDLE,
            "semanticGoals",
            "enrichByArtifact",
        )
        if not isinstance(node, dict) or not node:
            return "default"

        candidates: list[str] = []
        profile = str(profile_key or "").strip()
        entity_key = str(entity or "").strip()
        if profile:
            candidates.append(profile)
        if entity_key:
            candidates.append(entity_key)
            if entity_key.startswith("product_"):
                candidates.append(entity_key[len("product_") :])
        candidates.append("default")

        for candidate in candidates:
            if candidate in node and isinstance(node.get(candidate), list):
                return candidate
        return "default"

    @classmethod
    def enrich_goals_for_artifact(
        cls,
        entity: str | None,
        profile_key: str | None = None,
        *,
        product_code: str | None = None,
    ) -> list[EntityEnrichGoal]:
        group = cls.enrich_artifact_group(entity, profile_key)
        node = ChatAssistantContentService.get_node(
            _BUNDLE,
            "semanticGoals",
            "enrichByArtifact",
            group,
        )
        if not isinstance(node, list):
            node = ChatAssistantContentService.get_node(
                _BUNDLE,
                "semanticGoals",
                "enrichByArtifact",
                "default",
            )
        if not isinstance(node, list):
            return []

        code = str(product_code or "produto").strip() or "produto"
        goals: list[EntityEnrichGoal] = []
        for item in node:
            if not isinstance(item, dict):
                continue
            goal_id = str(item.get("goalId") or "").strip()
            scope_label = str(item.get("scopeLabel") or "").strip()
            template = str(item.get("intentTemplate") or "").strip()
            if not goal_id or not template:
                continue
            hints = tuple(
                str(hint).strip().lower()
                for hint in (item.get("queryHints") or [])
                if str(hint).strip()
            )
            goals.append(
                EntityEnrichGoal(
                    goal_id=goal_id,
                    scope_label=scope_label or goal_id,
                    intent=template.format(product_code=code),
                    query_hints=hints,
                )
            )
        return goals

    @classmethod
    def enrich_insight_limits_for_mode(cls, response_mode: str) -> dict[str, int]:
        from app.domain.services.chat_response_mode_service import ChatResponseModeService

        mode = ChatResponseModeService.normalize(response_mode)
        node = ChatAssistantContentService.get_node(_BUNDLE, "enrichInsightLimitsByMode") or {}

        if not isinstance(node, dict):
            return {}

        limits = node.get(mode)

        if not isinstance(limits, dict):
            limits = node.get("normal")

        if not isinstance(limits, dict):
            return {}

        resolved: dict[str, int] = {}

        for key in ("maxExtraRoutes", "maxFanOut"):
            try:
                resolved[key] = int(limits.get(key) or 0)
            except (TypeError, ValueError):
                resolved[key] = 0

        return resolved
