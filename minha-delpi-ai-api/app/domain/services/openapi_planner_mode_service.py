"""Resolução de CHAT_OPENAPI_PLANNER_MODE (off|shadow|canary|on)."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.services.openapi_tool_routing_content_service import (
    OpenApiToolRoutingContentService,
)


@dataclass(frozen=True)
class OpenApiPlannerModeDecision:
    mode: str
    use_openapi_selection: bool
    run_shadow_compare: bool
    canary_matched: bool

    @property
    def is_off(self) -> bool:
        return self.mode == "off"


class OpenApiPlannerModeService:
    _ALLOWED = frozenset({"off", "shadow", "canary", "on"})

    @classmethod
    def resolve_mode(cls) -> str:
        from app.infrastructure.config.settings import Settings

        raw = str(getattr(Settings, "CHAT_OPENAPI_PLANNER_MODE", "") or "").strip().lower()
        if not raw:
            default = OpenApiToolRoutingContentService.get("modes", "default", default="on")
            raw = str(default or "on").strip().lower()
        if raw not in cls._ALLOWED:
            return "on"
        return raw

    @classmethod
    def provider_allowlist(cls) -> set[str]:
        from app.infrastructure.config.settings import Settings

        raw = str(getattr(Settings, "CHAT_OPENAPI_PLANNER_PROVIDER_KEYS", "") or "")
        return {part.strip() for part in raw.split(",") if part.strip()}

    @classmethod
    def agent_allowlist(cls) -> set[str]:
        from app.infrastructure.config.settings import Settings

        raw = str(getattr(Settings, "CHAT_OPENAPI_PLANNER_AGENT_IDS", "") or "")
        return {part.strip() for part in raw.split(",") if part.strip()}

    @classmethod
    def decide(
        cls,
        *,
        provider_keys: set[str] | list[str] | None = None,
        agent_id: str | None = None,
    ) -> OpenApiPlannerModeDecision:
        mode = cls.resolve_mode()
        providers = {str(item).strip() for item in (provider_keys or []) if str(item).strip()}
        agent = str(agent_id or "").strip()

        if mode == "off":
            return OpenApiPlannerModeDecision(
                mode=mode,
                use_openapi_selection=False,
                run_shadow_compare=False,
                canary_matched=False,
            )

        if mode == "shadow":
            return OpenApiPlannerModeDecision(
                mode=mode,
                use_openapi_selection=False,
                run_shadow_compare=True,
                canary_matched=False,
            )

        if mode == "on":
            return OpenApiPlannerModeDecision(
                mode=mode,
                use_openapi_selection=True,
                run_shadow_compare=False,
                canary_matched=False,
            )

        # canary
        allowed_providers = cls.provider_allowlist()
        allowed_agents = cls.agent_allowlist()
        matched = False
        if allowed_providers and providers.intersection(allowed_providers):
            matched = True
        if allowed_agents and agent and agent in allowed_agents:
            matched = True
        if not allowed_providers and not allowed_agents:
            matched = False

        return OpenApiPlannerModeDecision(
            mode=mode,
            use_openapi_selection=matched,
            run_shadow_compare=False,
            canary_matched=matched,
        )
