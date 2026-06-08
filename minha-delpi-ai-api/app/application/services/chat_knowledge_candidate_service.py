from uuid import UUID

from app.domain.services.chat_learning_safety_guard import ChatLearningSafetyGuard
from app.domain.ports.learning_candidate_repository_port import LearningCandidateRepositoryPort
from app.domain.ports.vocabulary_term_repository_port import VocabularyTermRepositoryPort
from app.domain.services.chat_vocabulary_learning_service import (
    ChatVocabularyLearningService,
)
from app.infrastructure.config.settings import Settings


def _default_candidate_repository() -> LearningCandidateRepositoryPort:
    from app.composition.repository_composer import make_learning_candidate_repository

    return make_learning_candidate_repository()


def _default_vocabulary_repository() -> VocabularyTermRepositoryPort:
    from app.composition.repository_composer import make_vocabulary_term_repository

    return make_vocabulary_term_repository()

_CONFIDENCE_CAP = 0.95
_EVIDENCE_CONFIDENCE_STEP = 0.05


class ChatKnowledgeCandidateService:
    """Orquestra captura, dedup/evidência, governança e promoção de candidatos.

    Playbook §14 (candidatos), §15 (promoção), §26 (safety), §27 (confiança).
    """

    def __init__(
        self,
        candidate_repository: LearningCandidateRepositoryPort | None = None,
        vocabulary_repository: VocabularyTermRepositoryPort | None = None,
    ):
        self.candidate_repository = candidate_repository or _default_candidate_repository()
        self.vocabulary_repository = vocabulary_repository or _default_vocabulary_repository()

    def register_candidate(
        self,
        candidate: dict,
        *,
        created_by: str | None = None,
    ) -> dict | None:
        """Registra um candidato (dedup + evidência + safety). Retorna o estado salvo."""
        if not isinstance(candidate, dict):
            return None

        candidate_type = str(candidate.get("candidateType") or "").strip()
        term = self._clip(candidate.get("term"), 160)
        input_text = (
            self._clip(candidate.get("inputText"), 4000)
            or self._clip(candidate.get("term"), 4000)
            or self._clip(candidate.get("proposedMeaning"), 4000)
        )

        if not candidate_type or not input_text:
            return None

        guard_text = " ".join(
            part
            for part in (
                str(candidate.get("term") or ""),
                str(candidate.get("inputText") or ""),
                str(candidate.get("proposedMeaning") or ""),
            )
            if part
        )
        verdict = ChatLearningSafetyGuard.inspect(guard_text, candidate_type=candidate_type)

        if not verdict["allowed"]:
            return {"blocked": True, "reason": verdict["reason"], "riskLevel": verdict["riskLevel"]}

        scope = str(candidate.get("scope") or "global").strip() or "global"
        project_id = self._to_uuid(candidate.get("projectId"))
        incoming_confidence = self._confidence(candidate.get("confidence"))

        existing = self.candidate_repository.find_active_duplicate(
            candidate_type=candidate_type,
            term=term or input_text[:160],
            scope=scope,
            project_id=project_id,
        )

        if existing:
            new_confidence = min(
                _CONFIDENCE_CAP,
                max(existing.get("confidence") or 0.0, incoming_confidence or 0.0)
                + _EVIDENCE_CONFIDENCE_STEP,
            )
            example = None
            evidence = candidate.get("evidence")

            if isinstance(evidence, dict):
                examples = evidence.get("examples") or []
                example = examples[0] if examples else None

            return self.candidate_repository.bump_evidence(
                existing["id"],
                confidence=new_confidence,
                example=example or input_text,
            )

        status, risk_level = self._initial_status(
            confidence=incoming_confidence,
            risk_level=verdict["riskLevel"],
        )

        return self.candidate_repository.create(
            candidate_type=candidate_type,
            input_text=input_text,
            term=term or input_text[:160],
            proposed_rule=self._clip(candidate.get("proposedRule"), 240),
            proposed_meaning=self._clip(candidate.get("proposedMeaning"), 4000),
            evidence=candidate.get("evidence") if isinstance(candidate.get("evidence"), dict) else None,
            confidence=incoming_confidence,
            risk_level=risk_level,
            scope=scope,
            project_id=project_id,
            status=status,
            source=str(candidate.get("source") or "auto"),
            created_by=self._to_uuid(created_by),
        )

    def approve_candidate(self, candidate_id: int, *, reviewer_id: str | None = None) -> dict:
        updated = self.candidate_repository.update_status(
            candidate_id,
            status="approved",
            reviewer_id=self._to_uuid(reviewer_id),
        )

        if not updated:
            raise ValueError("candidate not found")

        return updated

    def reject_candidate(self, candidate_id: int, *, reviewer_id: str | None = None) -> dict:
        updated = self.candidate_repository.update_status(
            candidate_id,
            status="rejected",
            reviewer_id=self._to_uuid(reviewer_id),
        )

        if not updated:
            raise ValueError("candidate not found")

        return updated

    def promote_candidate(
        self,
        candidate_id: int,
        *,
        reviewer_id: str | None = None,
        term_override: str | None = None,
        normalized_override: str | None = None,
        meaning_override: str | None = None,
    ) -> dict:
        """Promove candidato a termo de vocabulário aprovado (playbook §15).

        O admin pode corrigir o termo/correção/significado no momento da promoção
        (ex.: definir a forma correta de um typo aprendido a partir do feedback).
        """
        candidate = self.candidate_repository.get(candidate_id)

        if not candidate:
            raise ValueError("candidate not found")

        if candidate["status"] in {"rejected", "expired"}:
            raise ValueError("cannot promote a rejected/expired candidate")

        from app.application.services.chat_learning_promotion_gate_service import (
            ChatLearningPromotionGateService,
        )

        gate = ChatLearningPromotionGateService().validate_promotion(
            candidate,
            term_override=term_override,
            normalized_override=normalized_override,
        )

        if not gate.get("allowed", True):
            raise ValueError(gate.get("message") or "promotion blocked by evaluation regression")

        term_text = (
            self._clip(term_override, 160)
            or candidate.get("term")
            or candidate.get("proposedRule")
            or candidate["inputText"]
        )
        normalized_term = (
            self._clip(normalized_override, 160)
            or candidate.get("proposedRule")
            or term_text
        )
        meaning = self._clip(meaning_override, 4000) or candidate.get("proposedMeaning")
        term_type = (
            "term_definition"
            if candidate["candidateType"] == "term_definition"
            else ChatVocabularyLearningService.classify_term(term_text)
        )

        term_row = self.vocabulary_repository.upsert_term(
            term=str(term_text)[:160],
            normalized_term=str(normalized_term)[:160],
            meaning=meaning,
            type=term_type,
            scope=candidate["scope"],
            project_id=self._to_uuid(candidate.get("projectId")),
            source="promotion",
            confidence=candidate.get("confidence"),
            approved=True,
            active=True,
            created_by=self._to_uuid(reviewer_id),
        )

        updated = self.candidate_repository.update_status(
            candidate_id,
            status="promoted",
            reviewer_id=self._to_uuid(reviewer_id),
            promoted_term_id=term_row["id"],
        )

        from app.domain.services.chat_learning_event_service import ChatLearningEventService

        ChatLearningEventService.emit(
            "chat.learning_candidate.promoted",
            candidateId=candidate_id,
            termId=term_row.get("id"),
            candidateType=candidate.get("candidateType"),
        )

        return {"candidate": updated, "term": term_row}

    def list_candidates(self, **kwargs) -> dict:
        items, total = self.candidate_repository.list_candidates(**kwargs)
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

    @staticmethod
    def _initial_status(*, confidence: float | None, risk_level: str) -> tuple[str, str]:
        auto = (
            Settings.CHAT_LEARNING_AUTO_APPROVE_ENABLED
            and risk_level == "low"
            and (confidence or 0.0) >= Settings.CHAT_LEARNING_AUTO_APPROVE_MIN_CONFIDENCE
        )
        return ("auto_approved" if auto else "pending", risk_level)

    @staticmethod
    def _confidence(value) -> float | None:
        try:
            if value is None:
                return None
            return max(0.0, min(float(value), _CONFIDENCE_CAP))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _clip(value, length: int) -> str | None:
        text = str(value).strip() if value is not None else ""
        return text[:length] if text else None

    @staticmethod
    def _to_uuid(value) -> UUID | None:
        if not value:
            return None

        if isinstance(value, UUID):
            return value

        try:
            return UUID(str(value))
        except (TypeError, ValueError):
            return None
