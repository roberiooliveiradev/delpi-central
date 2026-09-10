"""Turn Understanding — contrato canônico de entendimento do turno (E2.S3).

Semântica estruturada (goals/entities/presentation), sem path tokens nem
enum de intent por endpoint. Parser determinístico de entidades é hint.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

TURN_UNDERSTANDING_CONTRACT_VERSION = 1

SUPPORTED_GOAL_KINDS = frozenset({"lookup", "action", "reasoning", "unknown"})
FORBIDDEN_ENTITY_KEYS = frozenset(
    {
        "pathToken",
        "path_token",
        "pathMarkers",
        "path_markers",
        "operationIdMarkers",
        "routeSegment",
        "route_segment",
        "parameterStrategy",
        "parameter_strategy",
    }
)

TURN_UNDERSTANDING_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "TurnUnderstanding",
    "type": "object",
    "required": ["userGoal", "goals", "confidence"],
    "additionalProperties": True,
    "properties": {
        "contractVersion": {"type": "integer", "minimum": 1},
        "userGoal": {"type": "string", "minLength": 1},
        "goals": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["goalId", "intent"],
                "properties": {
                    "goalId": {"type": "string", "minLength": 1},
                    "intent": {"type": "string", "minLength": 1},
                    "entities": {"type": "object"},
                    "dependsOn": {"type": "array", "items": {"type": "string"}},
                    "kind": {"type": "string"},
                    "status": {"type": "string"},
                },
            },
        },
        "references": {"type": "array"},
        "presentationIntent": {"type": ["object", "null"]},
        "needsTool": {"type": ["boolean", "null"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "continuationOf": {"type": ["string", "null"]},
        "ambiguities": {"type": "array"},
        "source": {"type": "string"},
    },
}


def _clean_entities(raw: Any) -> dict[str, str]:
    if not isinstance(raw, dict):
        return {}
    cleaned: dict[str, str] = {}
    for key, value in raw.items():
        name = str(key or "").strip()
        if not name or name in FORBIDDEN_ENTITY_KEYS:
            continue
        if value is None:
            continue
        text = str(value).strip()
        if not text:
            continue
        cleaned[name] = text
    return cleaned


@dataclass(frozen=True)
class TurnUnderstandingGoal:
    """Um goal semântico — `intent` é prosa, não enum de endpoint."""

    goal_id: str
    intent: str
    entities: dict[str, str] = field(default_factory=dict)
    depends_on: tuple[str, ...] = ()
    kind: str = "unknown"
    status: str = "pending"

    @property
    def id(self) -> str:
        return self.goal_id

    @property
    def goal(self) -> str:
        """Alias legado (subtask.goal)."""
        return self.intent

    @property
    def type(self) -> str:
        """Alias legado (subtask.type)."""
        return self.kind

    def as_dict(self) -> dict[str, Any]:
        return {
            "goalId": self.goal_id,
            "intent": self.intent,
            "entities": dict(self.entities),
            "dependsOn": list(self.depends_on),
            "kind": self.kind,
            "status": self.status,
        }

    def as_subtask_dict(self) -> dict[str, Any]:
        """Shape legado consumido por TaskPlanner / testes E2.S2."""
        return {
            "id": self.goal_id,
            "goal": self.intent,
            "type": self.kind,
            "dependsOn": list(self.depends_on),
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> TurnUnderstandingGoal | None:
        if not isinstance(payload, dict):
            return None
        goal_id = str(
            payload.get("goalId") or payload.get("goal_id") or payload.get("id") or ""
        ).strip()
        intent = str(
            payload.get("intent") or payload.get("goal") or payload.get("userGoal") or ""
        ).strip()
        if not goal_id or not intent:
            return None
        kind = str(payload.get("kind") or payload.get("type") or "unknown").strip().lower()
        if kind not in SUPPORTED_GOAL_KINDS:
            kind = "unknown"
        depends_raw = payload.get("dependsOn") or payload.get("depends_on") or ()
        depends = tuple(str(item).strip() for item in depends_raw if str(item or "").strip())
        return cls(
            goal_id=goal_id,
            intent=intent,
            entities=_clean_entities(payload.get("entities")),
            depends_on=depends,
            kind=kind,
            status=str(payload.get("status") or "pending").strip() or "pending",
        )


# Alias estável para imports legados.
TurnUnderstandingSubtask = TurnUnderstandingGoal


@dataclass(frozen=True)
class TurnUnderstanding:
    user_goal: str
    goals: tuple[TurnUnderstandingGoal, ...]
    confidence: float
    continuation_of: str | None = None
    ambiguities: tuple[dict[str, Any], ...] = ()
    references: tuple[dict[str, Any], ...] = ()
    presentation_intent: dict[str, Any] | None = None
    needs_tool: bool | None = None
    source: str = "heuristic"
    contract_version: int = TURN_UNDERSTANDING_CONTRACT_VERSION

    @property
    def subtasks(self) -> tuple[TurnUnderstandingGoal, ...]:
        return self.goals

    @property
    def subtask_count(self) -> int:
        return len(self.goals)

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "contractVersion": self.contract_version,
            "userGoal": self.user_goal,
            "goals": [item.as_dict() for item in self.goals],
            "subtasks": [item.as_subtask_dict() for item in self.goals],
            "confidence": self.confidence,
            "continuationOf": self.continuation_of,
            "ambiguities": list(self.ambiguities),
            "references": list(self.references),
            "source": self.source,
            "subtaskCount": self.subtask_count,
            "needsTool": self.needs_tool,
        }
        if self.presentation_intent:
            payload["presentationIntent"] = dict(self.presentation_intent)
        return payload

    def as_admin_debug(self) -> dict[str, Any]:
        return self.as_dict()

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> TurnUnderstanding | None:
        if not isinstance(payload, dict):
            return None
        user_goal = str(payload.get("userGoal") or payload.get("user_goal") or "").strip()
        raw_goals = payload.get("goals")
        if not isinstance(raw_goals, list) or not raw_goals:
            raw_goals = payload.get("subtasks")
        if not isinstance(raw_goals, list) or not raw_goals:
            return None
        goals: list[TurnUnderstandingGoal] = []
        for item in raw_goals:
            goal = TurnUnderstandingGoal.from_dict(item if isinstance(item, dict) else None)
            if goal is not None:
                goals.append(goal)
        if not user_goal or not goals:
            return None
        try:
            confidence = float(payload.get("confidence"))
        except (TypeError, ValueError):
            return None
        confidence = max(0.0, min(1.0, confidence))
        presentation = payload.get("presentationIntent") or payload.get("presentation_intent")
        if presentation is not None and not isinstance(presentation, dict):
            presentation = None
        needs_tool = payload.get("needsTool")
        if needs_tool is None:
            needs_tool = payload.get("needs_tool")
        if needs_tool is not None:
            needs_tool = bool(needs_tool)
        refs = payload.get("references") or ()
        ambs = payload.get("ambiguities") or ()
        version = payload.get("contractVersion") or payload.get("contract_version") or 1
        try:
            version_int = int(version)
        except (TypeError, ValueError):
            version_int = TURN_UNDERSTANDING_CONTRACT_VERSION
        return cls(
            user_goal=user_goal,
            goals=tuple(goals),
            confidence=confidence,
            continuation_of=(
                str(payload.get("continuationOf") or payload.get("continuation_of") or "").strip()
                or None
            ),
            ambiguities=tuple(item for item in ambs if isinstance(item, dict)),
            references=tuple(item for item in refs if isinstance(item, dict)),
            presentation_intent=dict(presentation) if isinstance(presentation, dict) else None,
            needs_tool=needs_tool,
            source=str(payload.get("source") or "heuristic").strip() or "heuristic",
            contract_version=version_int,
        )

    @classmethod
    def fallback_single_goal(
        cls,
        message: str,
        *,
        source: str = "fallback",
        confidence: float = 0.4,
    ) -> TurnUnderstanding:
        text = str(message or "").strip() or "(vazio)"
        return cls(
            user_goal=text,
            goals=(
                TurnUnderstandingGoal(
                    goal_id="g1",
                    intent=text[:220],
                    entities={},
                    kind="unknown",
                ),
            ),
            confidence=max(0.0, min(1.0, float(confidence))),
            source=source,
            needs_tool=None,
        )
