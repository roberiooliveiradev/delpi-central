"""Flag do bounded planner loop — não reutiliza o alias morto de CHAT_OPENAPI_PLANNER_MODE."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.services.openapi_tool_routing_content_service import (
    OpenApiToolRoutingContentService,
)
from app.domain.services.openapi_planner_mode_service import OpenApiPlannerModeService


@dataclass(frozen=True)
class ChatBoundedPlannerModeDecision:
    mode: str
    use_bounded_loop: bool
    is_shadow: bool
    canary_matched: bool


class ChatBoundedPlannerModeService:
    _ALLOWED = frozenset({"off", "shadow", "canary", "on"})

    @classmethod
    def resolve_mode(cls) -> str:
        from app.infrastructure.config.settings import Settings

        raw = str(getattr(Settings, "CHAT_BOUNDED_PLANNER_MODE", "") or "").strip().lower()
        if not raw:
            raw = str(
                OpenApiToolRoutingContentService.get("boundedLoop", "default", default="on")
                or "on"
            ).strip().lower()
        if raw not in cls._ALLOWED:
            return "on"
        return raw

    @classmethod
    def decide(
        cls,
        *,
        provider_keys: set[str] | list[str] | None = None,
        agent_id: str | None = None,
    ) -> ChatBoundedPlannerModeDecision:
        mode = cls.resolve_mode()
        if mode == "off":
            return ChatBoundedPlannerModeDecision(
                mode=mode,
                use_bounded_loop=False,
                is_shadow=False,
                canary_matched=False,
            )
        if mode == "on" or mode == "shadow":
            return ChatBoundedPlannerModeDecision(
                mode=mode,
                use_bounded_loop=True,
                is_shadow=mode == "shadow",
                canary_matched=False,
            )

        openapi = OpenApiPlannerModeService.decide(
            provider_keys=provider_keys,
            agent_id=agent_id,
        )
        matched = bool(openapi.canary_matched)
        return ChatBoundedPlannerModeDecision(
            mode=mode,
            use_bounded_loop=matched,
            is_shadow=False,
            canary_matched=matched,
        )
