"""Métricas e metadata de roteamento de intenção — Playbook 02."""

from __future__ import annotations

from collections import Counter
from typing import Any


class ChatIntentRouterMetricsService:
    _SIMPLE_INTENTS = frozenset({"small_talk", "utility", "identity", "self_help"})

    @classmethod
    def is_simple_turn_snapshot(cls, snapshot: dict[str, Any] | None) -> bool:
        """Define turno simples a partir do snapshot/intentRouting (fonte única, §30)."""
        if not isinstance(snapshot, dict):
            return False

        intent = str(snapshot.get("intent") or "")
        sub_intent = str(snapshot.get("subIntent") or "")

        return intent in cls._SIMPLE_INTENTS or (
            intent == "clarification" and sub_intent == "unclear"
        )

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
            "requiresLlm": route.get("requiresLlm"),
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

    @classmethod
    def enrich_audit_metadata(
        cls,
        audit_metadata: dict,
        *,
        route: dict[str, Any] | None,
    ) -> dict:
        snapshot = cls.snapshot_from_route(route)

        if snapshot.get("intent"):
            audit_metadata["intentRouting"] = snapshot

        return audit_metadata

    @classmethod
    def aggregate_snapshots(
        cls,
        entries: list[dict[str, Any]],
        *,
        hours: int,
        since_iso: str,
    ) -> dict[str, Any]:
        by_intent: Counter[str] = Counter()
        by_decision: Counter[str] = Counter()
        ambiguous = 0
        mixed = 0
        web = 0
        text_skipped_tools = 0
        simple_turns = 0
        fallbacks = 0
        direct_answers = 0
        recent: list[dict[str, Any]] = []

        for entry in entries:
            snapshot = entry.get("snapshot") if isinstance(entry.get("snapshot"), dict) else entry

            if not isinstance(snapshot, dict):
                continue

            intent = str(snapshot.get("intent") or "unknown")
            by_intent[intent] += 1
            decision = str(snapshot.get("decision") or "").strip()
            sub_intent = str(snapshot.get("subIntent") or "").strip()

            if decision:
                by_decision[decision] += 1

            if snapshot.get("ambiguous"):
                ambiguous += 1

            if intent == "mixed_task":
                mixed += 1

            if snapshot.get("requiresWeb"):
                web += 1

            if decision == "skip_tools":
                text_skipped_tools += 1

            # Playbook §30 — eficiência de turnos simples
            if cls.is_simple_turn_snapshot(snapshot):
                simple_turns += 1

            if decision == "llm_fallback" or (intent == "clarification" and sub_intent == "unclear"):
                fallbacks += 1

            if snapshot.get("requiresLlm") is False:
                direct_answers += 1

        for entry in entries[:12]:
            snapshot = entry.get("snapshot")

            if not isinstance(snapshot, dict):
                continue

            recent.append(
                {
                    "loggedAt": entry.get("loggedAt"),
                    "action": entry.get("action"),
                    "intent": snapshot.get("intent"),
                    "subIntent": snapshot.get("subIntent"),
                    "decision": snapshot.get("decision"),
                    "ambiguous": snapshot.get("ambiguous"),
                }
            )

        return {
            "windowHours": hours,
            "since": since_iso,
            "routesCount": len(entries),
            "ambiguousCount": ambiguous,
            "mixedTaskCount": mixed,
            "webSearchCount": web,
            "textSkipToolsCount": text_skipped_tools,
            "simpleTurnCount": simple_turns,
            "fallbackCount": fallbacks,
            "directAnswerCount": direct_answers,
            "byIntent": dict(by_intent),
            "byDecision": dict(by_decision),
            "recent": recent,
        }
