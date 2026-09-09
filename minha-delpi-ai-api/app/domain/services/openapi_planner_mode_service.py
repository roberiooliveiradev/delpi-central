"""OpenAPI-first é o único seletor — sem off/shadow/canary."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OpenApiPlannerModeDecision:
    mode: str
    use_openapi_selection: bool
    run_shadow_compare: bool
    canary_matched: bool

    @property
    def is_off(self) -> bool:
        return False


class OpenApiPlannerModeService:
    @classmethod
    def resolve_mode(cls) -> str:
        return "on"

    @classmethod
    def decide(
        cls,
        *,
        provider_keys: set[str] | list[str] | None = None,
        agent_id: str | None = None,
    ) -> OpenApiPlannerModeDecision:
        del provider_keys, agent_id
        return OpenApiPlannerModeDecision(
            mode="on",
            use_openapi_selection=True,
            run_shadow_compare=False,
            canary_matched=False,
        )
