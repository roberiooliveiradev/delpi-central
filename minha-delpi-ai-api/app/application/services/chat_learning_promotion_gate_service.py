"""Gate de promoção — bloqueia se casos de regressão falharem (playbook Fase 6)."""

from __future__ import annotations

from app.domain.services.chat_evaluation_case_runner_service import (
    ChatEvaluationCaseRunnerService,
)
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.infrastructure.config.settings import Settings


class ChatLearningPromotionGateService:
    """Valida promoção simulando regras aprendidas antes de persistir.

    Bloqueia quando um caso que **passava** com o vocabulário atual deixa de passar
    após incluir a regra proposta (regressão real).
    """

    _NORMALIZATION_CATEGORIES = ("normalization", "routing")
    _ALL_CATEGORIES = ("normalization", "routing", "small_talk", "security", "memory")

    def __init__(self, *, evaluation_repository=None, vocabulary_repository=None):
        self._evaluation_repository = evaluation_repository
        self._vocabulary_repository = vocabulary_repository

    def _eval_repo(self):
        if self._evaluation_repository is None:
            from app.infrastructure.persistence.postgres_evaluation_case_repository import (
                PostgresEvaluationCaseRepository,
            )

            self._evaluation_repository = PostgresEvaluationCaseRepository()

        return self._evaluation_repository

    def _vocab_repo(self):
        if self._vocabulary_repository is None:
            from app.infrastructure.persistence.postgres_vocabulary_term_repository import (
                PostgresVocabularyTermRepository,
            )

            self._vocabulary_repository = PostgresVocabularyTermRepository()

        return self._vocabulary_repository

    @staticmethod
    def _enabled() -> bool:
        return bool(
            Settings.CHAT_LEARNING_ENABLED
            and Settings.CHAT_LEARNING_EVALUATION_ENABLED
            and Settings.CHAT_LEARNING_EVALUATION_BLOCK_PROMOTION
        )

    def validate_promotion(
        self,
        candidate: dict,
        *,
        term_override: str | None = None,
        normalized_override: str | None = None,
    ) -> dict:
        """Retorna {allowed, failures?, message?}. Não persiste nada."""
        if not self._enabled() or not isinstance(candidate, dict):
            return {"allowed": True}

        candidate_type = str(candidate.get("candidateType") or "")
        categories = (
            self._NORMALIZATION_CATEGORIES
            if candidate_type in {"normalization_rule", "typo", "vocabulary"}
            else self._ALL_CATEGORIES
        )

        cases = self._eval_repo().list_active(categories=categories)

        if not cases:
            return {"allowed": True}

        try:
            baseline_passing = self._run_cases(
                cases,
                self._rules_from_vocabulary(),
            )
            with_proposal_passing = self._run_cases(
                cases,
                self._rules_with_candidate(
                    candidate,
                    term_override=term_override,
                    normalized_override=normalized_override,
                ),
            )

            failures: list[dict] = []

            for case in cases:
                case_id = case.get("id")

                if case_id not in baseline_passing:
                    continue

                if case_id in with_proposal_passing:
                    continue

                failures.append(
                    {
                        "caseId": case_id,
                        "input": case.get("input"),
                        "reason": "regressão: caso passava antes da promoção simulada",
                    }
                )

            if failures:
                return {
                    "allowed": False,
                    "failures": failures,
                    "message": (
                        f"promoção bloqueada: {len(failures)} caso(s) de regressão falharam"
                    ),
                }

            return {"allowed": True}
        finally:
            from app.application.services.chat_learned_normalization_service import (
                ChatLearnedNormalizationService,
            )

            try:
                ChatLearnedNormalizationService(
                    vocabulary_repository=self._vocab_repo(),
                ).refresh()
            except Exception:
                ChatMessageNormalizationService.clear_learned_rules()

    @staticmethod
    def _run_cases(cases: list[dict], rules: list[tuple[str, str]]) -> set:
        ChatMessageNormalizationService.set_learned_rules(rules)
        passing: set = set()

        for case in cases:
            result = ChatEvaluationCaseRunnerService.run(case)

            if result.passed:
                passing.add(case.get("id"))

        return passing

    def _rules_from_vocabulary(self) -> list[tuple[str, str]]:
        return self._collect_rules_from_terms(
            self._vocab_repo().list_active_normalization_rules(
                scopes=("global",),
                max_rules=Settings.CHAT_LEARNING_VOCABULARY_MAX_RULES,
            )
        )

    def _rules_with_candidate(
        self,
        candidate: dict,
        *,
        term_override: str | None = None,
        normalized_override: str | None = None,
    ) -> list[tuple[str, str]]:
        rules = list(self._rules_from_vocabulary())

        term_text = (
            str(term_override or "").strip()
            or candidate.get("term")
            or candidate.get("proposedRule")
            or candidate.get("inputText")
            or ""
        )
        normalized = (
            str(normalized_override or "").strip()
            or candidate.get("proposedRule")
            or term_text
        )

        matchable = ChatMessageNormalizationService.strip_accents(str(term_text))
        correction = ChatMessageNormalizationService.strip_accents(str(normalized))

        if matchable and correction and matchable != correction:
            rules = [rule for rule in rules if rule[0] != matchable]
            rules.append((matchable, correction))

        return rules

    @staticmethod
    def _collect_rules_from_terms(terms: list[dict]) -> list[tuple[str, str]]:
        rules: list[tuple[str, str]] = []

        for term in terms:
            matchable = ChatMessageNormalizationService.strip_accents(term["term"])
            correction = ChatMessageNormalizationService.strip_accents(term["normalizedTerm"])

            if matchable and correction and matchable != correction:
                rules.append((matchable, correction))

        return rules
