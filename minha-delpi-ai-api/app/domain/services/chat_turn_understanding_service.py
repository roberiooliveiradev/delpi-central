"""Turn Understanding — decomposição multi-subtask (shadow) + contrato canônico E2.S3.

Produz contrato estruturado sem controlar a execução (shadow). Cutover de
authority fica em E2.S4+ / Task Planner quando a flag estiver ligada.
"""

from __future__ import annotations

from typing import Any

from app.domain.entities.turn_understanding import (
    TurnUnderstanding,
    TurnUnderstandingGoal,
    TurnUnderstandingSubtask,
)
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_turn_understanding_content_service import (
    ChatTurnUnderstandingContentService,
)
from app.domain.services.turn_understanding_validator_service import (
    TurnUnderstandingValidatorService,
)

_CONTENT = ChatTurnUnderstandingContentService

__all__ = [
    "ChatTurnUnderstandingService",
    "TurnUnderstanding",
    "TurnUnderstandingGoal",
    "TurnUnderstandingSubtask",
]


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
        goals: list[TurnUnderstandingGoal] = []

        for index, segment in enumerate(segments, start=1):
            intent = cls._clean_segment(segment)
            if not intent:
                continue
            goals.append(
                TurnUnderstandingGoal(
                    goal_id=f"g{index}",
                    intent=intent,
                    entities=cls._extract_entities(intent),
                    depends_on=tuple(
                        [f"g{index - 1}"] if index > 1 and cls._looks_dependent(intent) else []
                    ),
                    kind=cls._classify_type(intent),
                )
            )

        if not goals:
            goals = [
                TurnUnderstandingGoal(
                    goal_id="g1",
                    intent=clipped or raw or "(vazio)",
                    entities=cls._extract_entities(clipped or raw),
                    kind=_CONTENT.kind("unknown"),
                )
            ]

        # Compat IDs st-* ainda aceitos via from_dict; emissão canônica = gN.
        # Task planner / E2.S2 leem .subtasks / .goal / .type / depends_on.
        # Mantém st-* nos IDs para não quebrar depends_on esperados nos testes TU.
        st_goals = [
            TurnUnderstandingGoal(
                goal_id=f"st-{index}",
                intent=goal.intent,
                entities=goal.entities,
                depends_on=(f"st-{index - 1}",) if goal.depends_on and index > 1 else (),
                kind=goal.kind,
                status=goal.status,
            )
            for index, goal in enumerate(goals, start=1)
        ]

        confidence = cls._resolve_confidence(len(st_goals))
        draft = TurnUnderstanding(
            user_goal=clipped or raw,
            goals=tuple(st_goals),
            confidence=confidence,
            continuation_of=cls._continuation_hint(previous_messages),
            presentation_intent=cls._presentation_intent(clipped or raw),
            needs_tool=cls._infer_needs_tool(st_goals),
            source="heuristic",
        )
        return TurnUnderstandingValidatorService.ensure(
            draft,
            fallback_message=clipped or raw,
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
    def _extract_entities(cls, goal: str) -> dict[str, str]:
        from app.domain.services.chat_product_query_intent_service import (
            ChatProductQueryIntentService,
        )

        entities: dict[str, str] = {}
        code = ChatProductQueryIntentService.extract_product_code(goal or "")
        if code:
            entities["productCode"] = code
        return entities

    @classmethod
    def _presentation_intent(cls, message: str) -> dict[str, str] | None:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message) or ""
        if "tabela" in normalized or "table" in normalized:
            return {"view": "table"}
        if "grafico" in normalized or "gráfico" in normalized or "chart" in normalized:
            return {"view": "chart"}
        if "kpi" in normalized or "indicador" in normalized:
            return {"view": "kpi"}
        return None

    @classmethod
    def _infer_needs_tool(cls, goals: list[TurnUnderstandingGoal]) -> bool | None:
        kinds = {goal.kind for goal in goals}
        if kinds & {"lookup", "action", "reasoning"}:
            return True
        if kinds == {"unknown"} and len(goals) == 1 and len(goals[0].intent) < 40:
            return False
        return None

    @classmethod
    def _split_segments(cls, message: str) -> list[str]:
        text = message.strip()
        if not text:
            return []

        min_chars = max(1, _CONTENT.limit_int("minSubtaskChars", 4))
        candidates: list[str] = []

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        enum_line = _CONTENT.compile_pattern("enumerationLine")
        enumerated = [enum_line.sub("", line).strip() for line in lines if enum_line.search(line)]
        if len(enumerated) >= 2:
            candidates = enumerated
        else:
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
