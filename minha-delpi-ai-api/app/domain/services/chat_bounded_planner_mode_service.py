"""Bounded planner loop é o único caminho de planejamento de actions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChatBoundedPlannerModeDecision:
    mode: str
    use_bounded_loop: bool
    is_shadow: bool
    canary_matched: bool


class ChatBoundedPlannerModeService:
    @classmethod
    def resolve_mode(cls) -> str:
        return "on"

    @classmethod
    def decide(
        cls,
        *,
        provider_keys: set[str] | list[str] | None = None,
        agent_id: str | None = None,
    ) -> ChatBoundedPlannerModeDecision:
        del provider_keys, agent_id
        return ChatBoundedPlannerModeDecision(
            mode="on",
            use_bounded_loop=True,
            is_shadow=False,
            canary_matched=False,
        )
