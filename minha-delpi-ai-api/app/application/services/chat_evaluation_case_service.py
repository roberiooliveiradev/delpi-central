"""Casos de regressão — CRUD, execução e captura a partir de feedback (Fase 6)."""

from __future__ import annotations

from uuid import UUID

from app.domain.services.chat_evaluation_case_runner_service import (
    ChatEvaluationCaseRunnerService,
)
from app.domain.services.chat_learning_safety_guard import ChatLearningSafetyGuard
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.ports.evaluation_case_repository_port import EvaluationCaseRepositoryPort
from app.domain.services.chat_simple_turn_gate_service import ChatSimpleTurnGateService
from app.infrastructure.config.settings import Settings


def _default_evaluation_repository() -> EvaluationCaseRepositoryPort:
    from app.composition.repository_composer import make_evaluation_case_repository

    return make_evaluation_case_repository()


class ChatEvaluationCaseService:
    def __init__(self, repository: EvaluationCaseRepositoryPort | None = None):
        self._repository = repository

    def _repo(self) -> EvaluationCaseRepositoryPort:
        if self._repository is None:
            self._repository = _default_evaluation_repository()

        return self._repository

    @staticmethod
    def _capture_enabled() -> bool:
        return bool(
            Settings.CHAT_LEARNING_ENABLED
            and Settings.CHAT_LEARNING_EVALUATION_ENABLED
            and Settings.CHAT_LEARNING_EVALUATION_CAPTURE_FROM_FEEDBACK
        )

    @staticmethod
    def _run_enabled() -> bool:
        return bool(
            Settings.CHAT_LEARNING_ENABLED and Settings.CHAT_LEARNING_EVALUATION_ENABLED
        )

    def create_case(self, *, payload: dict, created_by: str | None = None) -> dict:
        if not isinstance(payload, dict):
            raise ValueError("invalid payload")

        category = str(payload.get("category") or "routing").strip() or "routing"
        input_text = str(payload.get("input") or "").strip()

        if not input_text:
            raise ValueError("input is required")

        verdict = ChatLearningSafetyGuard.is_safe_to_learn(input_text)

        if not verdict:
            raise ValueError("blocked by safety guard")

        created_by_uuid = None

        if created_by:
            try:
                created_by_uuid = UUID(str(created_by))
            except (TypeError, ValueError):
                created_by_uuid = None

        return self._repo().create(
            category=category,
            input_text=input_text,
            expected_intent=payload.get("expectedIntent") or payload.get("expected_intent"),
            expected_answer=payload.get("expectedAnswer") or payload.get("expected_answer"),
            expected_normalized=(
                payload.get("expectedNormalized") or payload.get("expected_normalized")
            ),
            must_not_use_tools=bool(
                payload.get("mustNotUseTools") or payload.get("must_not_use_tools")
            ),
            must_not_use_rag=bool(payload.get("mustNotUseRag") or payload.get("must_not_use_rag")),
            source_feedback_id=payload.get("sourceFeedbackId") or payload.get("source_feedback_id"),
            linked_candidate_id=(
                payload.get("linkedCandidateId") or payload.get("linked_candidate_id")
            ),
            created_by=created_by_uuid,
        )

    def list_cases(self, **kwargs) -> dict:
        items, total = self._repo().list_cases(**kwargs)
        limit = int(kwargs.get("limit", 50))
        offset = int(kwargs.get("offset", 0))

        return {
            "items": items,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": total,
                "hasNext": offset + limit < total,
                "hasPrevious": offset > 0,
            },
        }

    def run_case(self, case_id: int) -> dict:
        if not self._run_enabled():
            return {"enabled": False, "caseId": case_id}

        case = self._repo().get(case_id)

        if not case:
            raise ValueError("case not found")

        return self._run_and_persist(case)

    def run_all_active(self, *, category: str | None = None) -> dict:
        if not self._run_enabled():
            return {"enabled": False, "processed": 0}

        categories = (category,) if category else None
        cases = self._repo().list_active(categories=categories)
        passed = failed = 0
        results: list[dict] = []

        for case in cases:
            outcome = self._run_and_persist(case)
            results.append(outcome)

            if outcome.get("passed"):
                passed += 1
            else:
                failed += 1

        return {
            "enabled": True,
            "processed": len(cases),
            "passed": passed,
            "failed": failed,
            "results": results,
        }

    def _run_and_persist(self, case: dict) -> dict:
        result = ChatEvaluationCaseRunnerService.run(case)
        updated = self._repo().update_run_result(
            int(case["id"]),
            passed=result.passed,
            failure_reason=result.to_dict().get("failureReason"),
        )

        return {
            "caseId": case["id"],
            "passed": result.passed,
            "failures": list(result.failures),
            "case": updated,
        }

    def capture_from_negative_feedback(
        self,
        *,
        user_question: str,
        reason: str | None = None,
        feedback_id: int | None = None,
        created_by: str | None = None,
    ) -> dict | None:
        """Gera caso de regressão a partir de feedback negativo (best-effort)."""
        if not self._capture_enabled():
            return None

        message = str(user_question or "").strip()

        if not message or not ChatLearningSafetyGuard.is_safe_to_learn(message):
            return None

        decision = ChatSimpleTurnGateService.evaluate(message=message)
        category = "routing"

        if decision.matched and decision.intent == "assistant_identity":
            category = "routing"
        elif reason in {"wrong_intent", "misunderstood", "wrong_answer"}:
            category = "routing"

        existing = self._repo().find_duplicate_input(input_text=message, category=category)

        if existing:
            return {"skipped": True, "case": existing}

        expected_intent = None
        expected_normalized = None
        must_not_tools = False
        must_not_rag = False

        if decision.matched:
            if decision.sub_intent:
                expected_intent = f"{decision.intent}.{decision.sub_intent}"
            else:
                expected_intent = str(decision.intent)

            must_not_tools = not decision.requires_tool
            must_not_rag = not decision.requires_rag

        if reason in {"wrong_intent", "misunderstood"} and "como" in message.lower():
            expected_normalized = ChatMessageNormalizationService.normalize_for_matching(
                message
            )

        try:
            case = self._repo().create(
                category=category,
                input_text=message,
                expected_intent=expected_intent,
                expected_normalized=expected_normalized,
                must_not_use_tools=must_not_tools,
                must_not_use_rag=must_not_rag,
                source_feedback_id=feedback_id,
                created_by=self._to_uuid(created_by),
            )
            return {"created": True, "case": case}
        except Exception:
            return None

    @staticmethod
    def _to_uuid(value) -> UUID | None:
        if not value:
            return None

        try:
            return UUID(str(value))
        except (TypeError, ValueError):
            return None
