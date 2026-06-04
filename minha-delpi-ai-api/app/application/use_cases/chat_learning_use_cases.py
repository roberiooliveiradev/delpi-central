from app.application.services.chat_knowledge_candidate_service import (
    ChatKnowledgeCandidateService,
)
from app.application.services.chat_learned_normalization_service import (
    ChatLearnedNormalizationService,
)
from app.infrastructure.persistence.postgres_vocabulary_term_repository import (
    PostgresVocabularyTermRepository,
)


class ListLearningCandidatesUseCase:
    def __init__(self, candidate_service: ChatKnowledgeCandidateService | None = None):
        self.candidate_service = candidate_service or ChatKnowledgeCandidateService()

    def execute(
        self,
        *,
        status: str | None = None,
        candidate_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        return self.candidate_service.list_candidates(
            status=status,
            candidate_type=candidate_type,
            limit=limit,
            offset=offset,
        )


class ReviewLearningCandidateUseCase:
    """Aprovar, rejeitar ou promover um candidato (human-in-the-loop, §25)."""

    _ACTIONS = {"approve", "reject", "promote"}

    def __init__(self, candidate_service: ChatKnowledgeCandidateService | None = None):
        self.candidate_service = candidate_service or ChatKnowledgeCandidateService()

    def execute(
        self,
        *,
        candidate_id: int,
        action: str,
        reviewer_id: str | None = None,
        term_override: str | None = None,
        normalized_override: str | None = None,
        meaning_override: str | None = None,
    ) -> dict:
        normalized = str(action or "").strip().lower()

        if normalized not in self._ACTIONS:
            raise ValueError("invalid review action")

        if normalized == "approve":
            return {"candidate": self.candidate_service.approve_candidate(
                candidate_id, reviewer_id=reviewer_id,
            )}

        if normalized == "reject":
            return {"candidate": self.candidate_service.reject_candidate(
                candidate_id, reviewer_id=reviewer_id,
            )}

        result = self.candidate_service.promote_candidate(
            candidate_id,
            reviewer_id=reviewer_id,
            term_override=term_override,
            normalized_override=normalized_override,
            meaning_override=meaning_override,
        )
        # Reflete imediatamente a nova regra aprendida na normalização base.
        try:
            ChatLearnedNormalizationService().refresh()
        except Exception:
            pass

        return result


class ListVocabularyTermsUseCase:
    def __init__(self, vocabulary_repository: PostgresVocabularyTermRepository | None = None):
        self.vocabulary_repository = vocabulary_repository or PostgresVocabularyTermRepository()

    def execute(
        self,
        *,
        scope: str | None = None,
        approved: bool | None = None,
        type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        items, total = self.vocabulary_repository.list_terms(
            scope=scope,
            approved=approved,
            type=type,
            limit=limit,
            offset=offset,
        )

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


class UpsertVocabularyTermUseCase:
    """Admin cria/edita um termo aprovado diretamente (ex.: regra de typo)."""

    def __init__(self, vocabulary_repository: PostgresVocabularyTermRepository | None = None):
        self.vocabulary_repository = vocabulary_repository or PostgresVocabularyTermRepository()

    def execute(self, *, payload: dict, created_by: str | None = None) -> dict:
        from uuid import UUID

        from app.domain.services.chat_learning_safety_guard import ChatLearningSafetyGuard
        from app.domain.services.chat_message_normalization_service import (
            ChatMessageNormalizationService,
        )

        if not isinstance(payload, dict):
            raise ValueError("invalid payload")

        term = str(payload.get("term") or "").strip()
        normalized_term = str(
            payload.get("normalizedTerm") or payload.get("normalized_term") or ""
        ).strip()

        if not term:
            raise ValueError("term is required")

        if not normalized_term:
            normalized_term = ChatMessageNormalizationService.strip_accents(term)

        term_type = str(payload.get("type") or "typo").strip() or "typo"
        verdict = ChatLearningSafetyGuard.inspect(
            f"{term} {normalized_term} {payload.get('meaning') or ''}",
            candidate_type=term_type,
        )

        if not verdict["allowed"]:
            raise ValueError(f"blocked by safety guard: {verdict['reason']}")

        created_by_uuid = None

        if created_by:
            try:
                created_by_uuid = UUID(str(created_by))
            except (TypeError, ValueError):
                created_by_uuid = None

        project_id = payload.get("projectId") or payload.get("project_id")
        project_uuid = None

        if project_id:
            try:
                project_uuid = UUID(str(project_id))
            except (TypeError, ValueError):
                project_uuid = None

        result = self.vocabulary_repository.upsert_term(
            term=term[:160],
            normalized_term=normalized_term[:160],
            meaning=(str(payload.get("meaning")).strip() if payload.get("meaning") else None),
            type=term_type,
            scope=str(payload.get("scope") or "global").strip() or "global",
            project_id=project_uuid,
            source="admin",
            confidence=payload.get("confidence"),
            approved=bool(payload.get("approved", True)),
            active=bool(payload.get("active", True)),
            created_by=created_by_uuid,
        )

        try:
            ChatLearnedNormalizationService().refresh()
        except Exception:
            pass

        return result
