"""Plano estruturado de execução de actions OpenAPI."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ActionPlanStep:
    action_id: str
    arguments: dict[str, Any] = field(default_factory=dict)
    reason: str = ""
    confidence: float | None = None

    def as_dict(self) -> dict[str, Any]:
        payload = {
            "actionId": self.action_id,
            "arguments": dict(self.arguments or {}),
            "reason": self.reason,
        }
        if self.confidence is not None:
            payload["confidence"] = self.confidence
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ActionPlanStep:
        arguments = payload.get("arguments")
        if not isinstance(arguments, dict):
            arguments = {}
        confidence_raw = payload.get("confidence")
        confidence: float | None
        try:
            confidence = float(confidence_raw) if confidence_raw is not None else None
        except (TypeError, ValueError):
            confidence = None
        return cls(
            action_id=str(payload.get("actionId") or payload.get("action_id") or "").strip(),
            arguments=dict(arguments),
            reason=str(payload.get("reason") or "").strip(),
            confidence=confidence,
        )


@dataclass(frozen=True)
class ActionPlan:
    steps: tuple[ActionPlanStep, ...] = ()
    clarify: str | None = None
    selection_mode: str = "openapi_first"
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "steps": [step.as_dict() for step in self.steps],
            "clarify": self.clarify,
            "selectionMode": self.selection_mode,
            "metadata": dict(self.metadata or {}),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> ActionPlan:
        if not isinstance(payload, dict):
            return cls()
        raw_steps = payload.get("steps") or []
        steps: list[ActionPlanStep] = []
        if isinstance(raw_steps, list):
            for item in raw_steps:
                if isinstance(item, dict):
                    step = ActionPlanStep.from_dict(item)
                    if step.action_id:
                        steps.append(step)
        clarify = payload.get("clarify")
        return cls(
            steps=tuple(steps),
            clarify=str(clarify).strip() if clarify else None,
            selection_mode=str(
                payload.get("selectionMode") or payload.get("selection_mode") or "openapi_first"
            ),
            metadata=(
                dict(payload.get("metadata"))
                if isinstance(payload.get("metadata"), dict)
                else {}
            ),
        )

    @property
    def is_empty(self) -> bool:
        return not self.steps and not self.clarify
