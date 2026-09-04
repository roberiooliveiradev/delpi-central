"""Turn Understanding — decomposição heurística multi-subtask (E3.S1, shadow).

Produz um contrato estruturado sem controlar a execução (shadow). Cutover
fica a cargo do Task Planner (E5) quando a flag estiver ligada.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_turn_understanding_content_service import (
    ChatTurnUnderstandingContentService,
)

_CONTENT = ChatTurnUnderstandingContentService


@dataclass(frozen=True)
class TurnUnderstandingSubtask:
    id: str
    goal: str
    type: str
    depends_on: tuple[str, ...] = ()
    status: str = "pending"

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "goal": self.goal,
            "type": self.type,
            "dependsOn": list(self.depends_on),
            "status": self.status,
        }


@dataclass(frozen=True)
class TurnUnderstanding:
    user_goal: str
    subtasks: tuple[TurnUnderstandingSubtask, ...]
    confidence: float
    continuation_of: str | None = None
    ambiguities: tuple[dict[str, Any], ...] = ()
    references: tuple[dict[str, Any], ...] = ()
    source: str = "heuristic"

    @property
    def subtask_count(self) -> int:
        return len(self.subtasks)

    def as_dict(self) -> dict[str, Any]:
        return {
            "userGoal": self.user_goal,
            "subtasks": [item.as_dict() for item in self.subtasks],
            "confidence": self.confidence,
            "continuationOf": self.continuation_of,
            "ambiguities": list(self.ambiguities),
            "references": list(self.references),
            "source": self.source,
            "subtaskCount": self.subtask_count,
        }

    def as_admin_debug(self) -> dict[str, Any]:
        return self.as_dict()


class ChatTurnUnderstandingService:
    @classmethod
    def analyze(
        cls,
        message: str,
        *,
        response_mode: str | None = None,
        previous_messages: list[Any] | None = None,
    ) -> TurnUnderstanding:
        raw = str(message or "").strip()
        max_chars = max(200, _CONTENT.limit_int("maxMessageChars", 4000))
        clipped = raw[:max_chars]
        segments = cls._split_segments(clipped)
        max_subtasks = max(1, _CONTENT.limit_int("maxSubtasks", 8))

        if str(response_mode or "").strip().lower() == "fast":
            max_subtasks = 1

        segments = segments[:max_subtasks] or [clipped or raw]
        subtasks: list[TurnUnderstandingSubtask] = []

        for index, segment in enumerate(segments, start=1):
            goal = cls._clean_segment(segment)
            if not goal:
                continue
            subtasks.append(
                TurnUnderstandingSubtask(
                    id=f"st-{index}",
                    goal=goal,
                    type=cls._classify_type(goal),
                    depends_on=tuple(
                        [f"st-{index - 1}"] if index > 1 and cls._looks_dependent(goal) else []
                    ),
                )
            )

        if not subtasks:
            subtasks = [
                TurnUnderstandingSubtask(
                    id="st-1",
                    goal=clipped or raw or "(vazio)",
                    type=_CONTENT.kind("unknown"),
                )
            ]

        confidence = cls._resolve_confidence(len(subtasks))
        return TurnUnderstanding(
            user_goal=clipped or raw,
            subtasks=tuple(subtasks),
            confidence=confidence,
            continuation_of=cls._continuation_hint(previous_messages),
            source="heuristic",
        )

    @classmethod
    def analyze_shadow(
        cls,
        message: str,
        *,
        response_mode: str | None = None,
        previous_messages: list[Any] | None = None,
        enabled: bool | None = None,
    ) -> TurnUnderstanding | None:
        from app.domain.services.chat_conversational_intelligence_flag_service import (
            ChatConversationalIntelligenceFlagService,
        )

        if enabled is None:
            enabled = ChatConversationalIntelligenceFlagService.turn_understanding_shadow_enabled()

        if not enabled:
            return None

        return cls.analyze(
            message,
            response_mode=response_mode,
            previous_messages=previous_messages,
        )

    @classmethod
    def _split_segments(cls, message: str) -> list[str]:
        text = message.strip()
        if not text:
            return []

        min_chars = max(1, _CONTENT.limit_int("minSubtaskChars", 4))
        candidates: list[str] = []

        # 1) linhas enumeradas
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        enum_line = _CONTENT.compile_pattern("enumerationLine")
        enumerated = [enum_line.sub("", line).strip() for line in lines if enum_line.search(line)]
        if len(enumerated) >= 2:
            candidates = enumerated
        else:
            # 2) separadores fortes / conectores
            parts = _CONTENT.compile_pattern("hardSeparator").split(text)
            expanded: list[str] = []
            for part in parts:
                chunk = str(part or "").strip()
                if not chunk:
                    continue
                seq = _CONTENT.compile_pattern("sequenceConnector").split(chunk)
                for piece in seq:
                    piece = str(piece or "").strip()
                    if not piece:
                        continue
                    coord = _CONTENT.compile_pattern("coordinationConnector").split(piece)
                    expanded.extend(str(item).strip() for item in coord if str(item).strip())
            # perguntas
            if len(expanded) <= 1:
                expanded = [
                    str(item).strip()
                    for item in _CONTENT.compile_pattern("questionSplit").split(text)
                    if str(item).strip()
                ]
            candidates = expanded

        cleaned = [cls._clean_segment(item) for item in candidates]
        cleaned = [item for item in cleaned if item and len(item) >= min_chars]

        if len(cleaned) < max(2, _CONTENT.limit_int("compoundMinSubtasks", 2)):
            return [text]

        return cleaned

    @classmethod
    def _clean_segment(cls, value: str) -> str:
        text = str(value or "").strip(" \t\r\n-•*;,.")
        for noise in _CONTENT.noise_tokens():
            if text.lower().startswith(noise):
                text = text[len(noise) :].strip(" \t\r\n-•*;,.")
        max_chars = max(16, _CONTENT.limit_int("maxSubtaskChars", 220))
        return text[:max_chars].strip()

    @classmethod
    def _classify_type(cls, goal: str) -> str:
        normalized = ChatMessageNormalizationService.normalize_for_matching(goal) or goal.lower()
        for verb in _CONTENT.verbs("action"):
            if verb in normalized:
                return _CONTENT.kind("action")
        for verb in _CONTENT.verbs("reasoning"):
            if verb in normalized:
                return _CONTENT.kind("reasoning")
        for verb in _CONTENT.verbs("lookup"):
            if verb in normalized:
                return _CONTENT.kind("lookup")
        return _CONTENT.kind("unknown")

    @classmethod
    def _resolve_confidence(cls, subtask_count: int) -> float:
        if subtask_count <= 1:
            return _CONTENT.confidence("single", 0.55)

        base = _CONTENT.confidence("compoundBase", 0.5)
        step = _CONTENT.confidence("compoundStep", 0.08)
        ceiling = _CONTENT.confidence("compoundMax", 0.9)

        return min(ceiling, base + step * subtask_count)

    @classmethod
    def _looks_dependent(cls, goal: str) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(goal) or goal.lower()

        return any(marker in normalized for marker in _CONTENT.dependency_markers())

    @classmethod
    def _continuation_hint(cls, previous_messages: list[Any] | None) -> str | None:
        max_chars = _CONTENT.continuation_max_hint_chars()

        for item in reversed(previous_messages or []):
            if not isinstance(item, dict):
                continue
            role = str(item.get("role") or item.get("sender") or "").strip().lower()
            if role in {"user", "human"}:
                content = str(item.get("content") or "").strip()
                return content[:max_chars] or None
        return None
