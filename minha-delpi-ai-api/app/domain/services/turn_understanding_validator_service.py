"""Valida e normaliza o contrato canônico de Turn Understanding (E2.S3)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain.entities.turn_understanding import (
    FORBIDDEN_ENTITY_KEYS,
    SUPPORTED_GOAL_KINDS,
    TURN_UNDERSTANDING_CONTRACT_VERSION,
    TurnUnderstanding,
    TurnUnderstandingGoal,
    _clean_entities,
)


@dataclass
class TurnUnderstandingValidationResult:
    ok: bool
    contract: TurnUnderstanding | None = None
    errors: list[str] = field(default_factory=list)
    used_fallback: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": list(self.errors),
            "usedFallback": self.used_fallback,
            "contract": self.contract.as_dict() if self.contract else None,
        }


class TurnUnderstandingValidatorService:
    @classmethod
    def validate(
        cls,
        raw: TurnUnderstanding | dict[str, Any] | None,
        *,
        fallback_message: str | None = None,
    ) -> TurnUnderstandingValidationResult:
        if isinstance(raw, TurnUnderstanding):
            contract = raw
        else:
            contract = TurnUnderstanding.from_dict(raw if isinstance(raw, dict) else None)

        if contract is None:
            message = str(fallback_message or "").strip() or "(vazio)"
            return TurnUnderstandingValidationResult(
                ok=False,
                contract=TurnUnderstanding.fallback_single_goal(message),
                errors=["malformed_or_missing_contract"],
                used_fallback=True,
            )

        errors: list[str] = []
        goals: list[TurnUnderstandingGoal] = []
        for index, goal in enumerate(contract.goals, start=1):
            intent = str(goal.intent or "").strip()
            goal_id = str(goal.goal_id or "").strip() or f"g{index}"
            if not intent:
                errors.append(f"goal[{index}].intent_missing")
                continue
            kind = goal.kind if goal.kind in SUPPORTED_GOAL_KINDS else "unknown"
            entities = _clean_entities(goal.entities)
            for forbidden in FORBIDDEN_ENTITY_KEYS:
                if forbidden in (goal.entities or {}):
                    errors.append(f"goal[{index}].forbidden_entity:{forbidden}")
            goals.append(
                TurnUnderstandingGoal(
                    goal_id=goal_id,
                    intent=intent,
                    entities=entities,
                    depends_on=tuple(
                        dep for dep in goal.depends_on if str(dep or "").strip()
                    ),
                    kind=kind,
                    status=str(goal.status or "pending").strip() or "pending",
                )
            )

        if not goals:
            message = str(
                fallback_message or contract.user_goal or ""
            ).strip() or "(vazio)"
            return TurnUnderstandingValidationResult(
                ok=False,
                contract=TurnUnderstanding.fallback_single_goal(message),
                errors=errors + ["goals_empty"],
                used_fallback=True,
            )

        confidence = float(contract.confidence)
        if confidence < 0 or confidence > 1:
            errors.append("confidence_out_of_range")
            confidence = max(0.0, min(1.0, confidence))

        normalized = TurnUnderstanding(
            user_goal=str(contract.user_goal or "").strip() or goals[0].intent,
            goals=tuple(goals),
            confidence=confidence,
            continuation_of=contract.continuation_of,
            ambiguities=contract.ambiguities,
            references=contract.references,
            presentation_intent=(
                dict(contract.presentation_intent)
                if isinstance(contract.presentation_intent, dict)
                else None
            ),
            needs_tool=contract.needs_tool,
            source=str(contract.source or "heuristic").strip() or "heuristic",
            contract_version=max(
                1, int(contract.contract_version or TURN_UNDERSTANDING_CONTRACT_VERSION)
            ),
        )
        return TurnUnderstandingValidationResult(
            ok=not errors,
            contract=normalized,
            errors=errors,
            used_fallback=False,
        )

    @classmethod
    def ensure(
        cls,
        raw: TurnUnderstanding | dict[str, Any] | None,
        *,
        fallback_message: str | None = None,
    ) -> TurnUnderstanding:
        result = cls.validate(raw, fallback_message=fallback_message)
        assert result.contract is not None
        return result.contract
