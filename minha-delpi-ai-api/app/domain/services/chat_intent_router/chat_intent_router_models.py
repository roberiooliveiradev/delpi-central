"""Modelos compartilhados — roteamento de intenção."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class IntentRouteResult:
    intent: str
    sub_intent: str | None = None
    is_follow_up: bool = False
    confidence: float = 0.0
    requires_tool: bool = False
    requires_rag: bool = False
    requires_web: bool = False
    requires_canvas: bool = False
    requires_llm: bool = True
    priority_applied: int = 0
    flags: tuple[str, ...] = ()
    resolved_params: dict[str, str] | None = None
    ambiguous: bool = False
    candidates: tuple[str, ...] = ()
    decision: str | None = None
    reason: str | None = None
    mixed_steps: tuple[str, ...] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "intent": self.intent,
            "isFollowUp": self.is_follow_up,
            "confidence": round(self.confidence, 2),
            "requiresTool": self.requires_tool,
            "requiresRag": self.requires_rag,
            "requiresWeb": self.requires_web,
            "requiresCanvas": self.requires_canvas,
            "requiresLlm": self.requires_llm,
            "priorityApplied": self.priority_applied,
            "ambiguous": self.ambiguous,
        }

        if self.sub_intent:
            payload["subIntent"] = self.sub_intent

        if self.flags:
            payload["flags"] = list(self.flags)

        if self.resolved_params:
            params = dict(self.resolved_params)
            payload["resolvedParams"] = params
            payload["resolvedFromMemory"] = params

        if self.candidates:
            payload["candidates"] = list(self.candidates)

        if self.mixed_steps:
            payload["mixedSteps"] = list(self.mixed_steps)

        if self.decision:
            payload["decision"] = self.decision

        if self.reason:
            payload["reason"] = self.reason

        payload["router"] = {
            "intent": self.intent,
            "subIntent": self.sub_intent,
            "confidence": payload["confidence"],
            "decision": self.decision,
            "reason": self.reason,
        }

        payload["intentRouting"] = {
            key: payload[key]
            for key in (
                "intent",
                "subIntent",
                "isFollowUp",
                "confidence",
                "requiresTool",
                "requiresRag",
                "requiresWeb",
                "requiresCanvas",
                "requiresLlm",
                "resolvedParams",
                "ambiguous",
                "candidates",
                "mixedSteps",
            )
            if key in payload
        }

        return payload
