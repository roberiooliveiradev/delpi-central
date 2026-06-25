"""Executor de casos de regressão — Playbook aprendizagem contínua (Fase 6).

Avalia roteamento/normalização/respostas diretas sem LLM, alinhado ao gate de turno
simples e aos serviços de resposta direta já existentes na inteligência base.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_simple_turn_gate_service import ChatSimpleTurnGateService


@dataclass(frozen=True)
class EvaluationCaseResult:
    passed: bool
    failures: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "failures": list(self.failures),
            "failureReason": "; ".join(self.failures) if self.failures else None,
        }


class ChatEvaluationCaseRunnerService:
    """Avalia um caso de regressão de forma determinística (sem LLM)."""

    @classmethod
    def run(cls, case: dict) -> EvaluationCaseResult:
        message = str(case.get("input") or "").strip()
        failures: list[str] = []

        if not message:
            return EvaluationCaseResult(passed=False, failures=("input vazio",))

        decision = ChatSimpleTurnGateService.evaluate(message=message)

        expected_intent = str(case.get("expectedIntent") or "").strip()
        if expected_intent and not cls._intent_matches(expected_intent, decision):
            actual = cls._format_intent(decision)
            failures.append(
                f"intenção esperada '{expected_intent}', obtida '{actual}'"
            )

        expected_normalized = str(case.get("expectedNormalized") or "").strip()
        if expected_normalized:
            actual_norm = ChatMessageNormalizationService.normalize_for_matching(message)
            expected_norm = ChatMessageNormalizationService.normalize_for_matching(
                expected_normalized
            )

            if actual_norm != expected_norm:
                failures.append(
                    f"normalização esperada '{expected_norm}', obtida '{actual_norm}'"
                )

        if case.get("mustNotUseTools") and decision.requires_tool:
            failures.append("não deveria exigir ferramenta")

        if case.get("mustNotUseRag") and decision.requires_rag:
            failures.append("não deveria exigir RAG")

        expected_answer = str(case.get("expectedAnswer") or "").strip()
        if expected_answer:
            direct = cls._direct_answer_snippet(message)
            needle = ChatMessageNormalizationService.strip_accents(expected_answer)

            if not direct or needle not in ChatMessageNormalizationService.strip_accents(
                direct
            ):
                failures.append(
                    f"resposta direta não contém trecho esperado '{expected_answer[:80]}'"
                )

        return EvaluationCaseResult(
            passed=len(failures) == 0,
            failures=tuple(failures),
        )

    @classmethod
    def _format_intent(cls, decision) -> str:
        if not decision.matched or not decision.intent:
            return "none"

        if decision.sub_intent:
            return f"{decision.intent}.{decision.sub_intent}"

        return str(decision.intent)

    @classmethod
    def _intent_matches(cls, expected: str, decision) -> bool:
        if not decision.matched:
            return False

        expected = expected.strip().lower()
        actual = cls._format_intent(decision).lower()

        if expected == actual:
            return True

        # Aceita prefixo (ex.: expected assistant_identity → assistant_identity.name).
        if "." in actual and actual.startswith(f"{expected}."):
            return True

        if "." in expected:
            base = expected.split(".", 1)[0]
            return actual == expected or actual.startswith(f"{base}.")

        return actual.split(".", 1)[0] == expected

    @classmethod
    def _direct_answer_snippet(cls, message: str) -> str:
        workspace: dict = {}

        from app.domain.services.chat_assistant_identity_service import (
            ChatAssistantIdentityService,
        )
        from app.domain.services.chat_capabilities_catalog_answer_service import (
            ChatCapabilitiesCatalogAnswerService,
        )
        from app.domain.services.chat_capabilities_detection_service import (
            ChatCapabilitiesDetectionService,
        )
        from app.domain.services.chat_small_talk_service import ChatSmallTalkService
        from app.domain.services.chat_utility_direct_answer_service import (
            ChatUtilityDirectAnswerService,
        )
        from app.domain.services.chat_unclear_request_service import (
            ChatUnclearRequestService,
        )

        if ChatAssistantIdentityService.classify(message):
            answer = ChatAssistantIdentityService.build_direct_answer(
                message=message,
                workspace_context=workspace,
            )
            return str(answer or "")

        if ChatSmallTalkService.classify(message):
            answer = ChatSmallTalkService.build_direct_answer(
                message=message,
                workspace_context=workspace,
            )
            return str(answer or "")

        if ChatUtilityDirectAnswerService.classify(message):
            answer = ChatUtilityDirectAnswerService.build_direct_answer(message)
            return str(answer or "")

        if ChatCapabilitiesDetectionService.is_capabilities_question(message):
            answer = ChatCapabilitiesCatalogAnswerService.build_direct_answer(
                workspace_context=workspace,
            )
            return str(answer or "")

        if ChatUnclearRequestService.classify(message):
            answer = ChatUnclearRequestService.build_direct_answer(message)
            return str(answer or "")

        return ""
