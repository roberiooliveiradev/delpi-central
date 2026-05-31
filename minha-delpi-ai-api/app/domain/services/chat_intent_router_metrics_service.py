"""Métricas e metadata de roteamento de intenção — Playbook 02."""

from __future__ import annotations

from typing import Any


class ChatIntentRouterMetricsService:
    @classmethod
    def snapshot_from_route(cls, route: dict[str, Any] | None) -> dict[str, Any]:
        route = route if isinstance(route, dict) else {}
        router = route.get("router") if isinstance(route.get("router"), dict) else {}

        return {
            "intent": route.get("intent"),
            "subIntent": route.get("subIntent"),
            "confidence": route.get("confidence"),
            "isFollowUp": bool(route.get("isFollowUp")),
            "requiresTool": bool(route.get("requiresTool")),
            "requiresWeb": bool(route.get("requiresWeb")),
            "requiresRag": bool(route.get("requiresRag")),
            "requiresCanvas": bool(route.get("requiresCanvas")),
            "ambiguous": bool(route.get("ambiguous")),
            "decision": router.get("decision") or route.get("decision"),
            "reason": router.get("reason") or route.get("reason"),
        }

    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict[str, Any],
        route: dict[str, Any] | None,
        *,
        normalized_message: str | None = None,
    ) -> None:
        if not isinstance(metadata, dict) or not isinstance(route, dict):
            return

        routing = route.get("intentRouting")

        if isinstance(routing, dict):
            metadata["intentRouting"] = dict(routing)
        else:
            metadata["intentRouting"] = {
                key: route[key]
                for key in (
                    "intent",
                    "subIntent",
                    "confidence",
                    "isFollowUp",
                    "requiresTool",
                    "requiresWeb",
                    "requiresRag",
                    "requiresLlm",
                    "requiresCanvas",
                    "resolvedParams",
                    "ambiguous",
                    "candidates",
                    "mixedSteps",
                )
                if key in route
            }

        metadata["intentRouterMetrics"] = cls.snapshot_from_route(route)

        if normalized_message:
            admin_debug = metadata.get("adminDebug")

            if isinstance(admin_debug, dict):
                admin_debug.setdefault("router", {})
                admin_debug["router"]["normalizedMessage"] = normalized_message[:500]
