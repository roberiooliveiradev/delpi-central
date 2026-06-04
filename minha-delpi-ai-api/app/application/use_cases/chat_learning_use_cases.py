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

        # Atualiza o cache de definições do glossário (termo promovido com meaning).
        try:
            from app.application.services.chat_glossary_retrieval_service import (
                ChatGlossaryRetrievalService,
            )

            ChatGlossaryRetrievalService().refresh()
        except Exception:
            pass

        # RAG adaptativo (Fase 5): indexa o termo promovido como conhecimento recuperável.
        try:
            from app.application.services.chat_glossary_knowledge_index_service import (
                ChatGlossaryKnowledgeIndexService,
            )

            ChatGlossaryKnowledgeIndexService().sync_term(result.get("term") or {})
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


class ReindexUserMemoryKnowledgeUseCase:
    """Backfill do índice RAG de memórias persistentes ativas."""

    def __init__(self, memory_repository=None):
        if memory_repository is None:
            from app.infrastructure.persistence.postgres_memory_item_repository import (
                PostgresMemoryItemRepository,
            )

            memory_repository = PostgresMemoryItemRepository()

        self.memory_repository = memory_repository

    def execute(self, *, limit: int = 2000) -> dict:
        from app.application.services.chat_memory_knowledge_index_service import (
            ChatMemoryKnowledgeIndexService,
        )

        items = self.memory_repository.list_active_for_reindex(
            limit=max(1, min(int(limit), 5000)),
        )
        result = ChatMemoryKnowledgeIndexService().reindex_all(items)
        result["total"] = len(items)
        return result


class ReindexGlossaryKnowledgeUseCase:
    """Backfill do índice RAG do glossário (playbook Fase 5).

    Reindexa todos os termos de definição aprovados como conhecimento recuperável,
    útil ao habilitar a flag em uma base com termos já promovidos.
    """

    def __init__(self, vocabulary_repository: PostgresVocabularyTermRepository | None = None):
        self.vocabulary_repository = vocabulary_repository or PostgresVocabularyTermRepository()

    def execute(self, *, limit: int = 2000) -> dict:
        from app.application.services.chat_glossary_knowledge_index_service import (
            ChatGlossaryKnowledgeIndexService,
        )

        items, total = self.vocabulary_repository.list_terms(
            type="term_definition",
            approved=True,
            limit=max(1, min(int(limit), 5000)),
            offset=0,
        )

        result = ChatGlossaryKnowledgeIndexService().reindex_all(items)
        result["total"] = int(total)
        return result


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

        try:
            from app.application.services.chat_glossary_retrieval_service import (
                ChatGlossaryRetrievalService,
            )

            ChatGlossaryRetrievalService().refresh()
        except Exception:
            pass

        try:
            from app.application.services.chat_glossary_knowledge_index_service import (
                ChatGlossaryKnowledgeIndexService,
            )

            ChatGlossaryKnowledgeIndexService().sync_term(result or {})
        except Exception:
            pass

        return result


class ListEvaluationCasesUseCase:
    def __init__(self, evaluation_service=None):
        from app.application.services.chat_evaluation_case_service import (
            ChatEvaluationCaseService,
        )

        self.evaluation_service = evaluation_service or ChatEvaluationCaseService()

    def execute(
        self,
        *,
        category: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        return self.evaluation_service.list_cases(
            category=category,
            status=status,
            limit=limit,
            offset=offset,
        )


class CreateEvaluationCaseUseCase:
    def __init__(self, evaluation_service=None):
        from app.application.services.chat_evaluation_case_service import (
            ChatEvaluationCaseService,
        )

        self.evaluation_service = evaluation_service or ChatEvaluationCaseService()

    def execute(self, *, payload: dict, created_by: str | None = None) -> dict:
        return self.evaluation_service.create_case(payload=payload, created_by=created_by)


class RunEvaluationCaseUseCase:
    def __init__(self, evaluation_service=None):
        from app.application.services.chat_evaluation_case_service import (
            ChatEvaluationCaseService,
        )

        self.evaluation_service = evaluation_service or ChatEvaluationCaseService()

    def execute(self, *, case_id: int | None = None, category: str | None = None) -> dict:
        if case_id is not None:
            return self.evaluation_service.run_case(case_id)

        return self.evaluation_service.run_all_active(category=category)


class ReviewEvaluationCaseUseCase:
    """Ativa/desativa um caso de regressão."""

    _ACTIONS = {"enable", "disable"}

    def __init__(self, repository=None):
        if repository is None:
            from app.infrastructure.persistence.postgres_evaluation_case_repository import (
                PostgresEvaluationCaseRepository,
            )

            repository = PostgresEvaluationCaseRepository()

        self.repository = repository

    def execute(self, *, case_id: int, action: str) -> dict:
        normalized = str(action or "").strip().lower()

        if normalized not in self._ACTIONS:
            raise ValueError("invalid review action")

        status = "active" if normalized == "enable" else "disabled"
        updated = self.repository.set_status(case_id, status=status)

        if not updated:
            raise ValueError("case not found")

        return {"case": updated}


class ListFineTuningSamplesUseCase:
    def __init__(self, service=None):
        from app.application.services.chat_fine_tuning_service import ChatFineTuningService

        self.service = service or ChatFineTuningService()

    def execute(self, **kwargs) -> dict:
        return self.service.list_samples(**kwargs)


class CreateFineTuningSampleUseCase:
    def __init__(self, service=None):
        from app.application.services.chat_fine_tuning_service import ChatFineTuningService

        self.service = service or ChatFineTuningService()

    def execute(self, *, payload: dict, created_by: str | None = None) -> dict:
        return self.service.create_sample_manual(payload=payload, created_by=created_by)


class ReviewFineTuningSampleUseCase:
    def __init__(self, service=None):
        from app.application.services.chat_fine_tuning_service import ChatFineTuningService

        self.service = service or ChatFineTuningService()

    def execute(
        self,
        *,
        sample_id: int,
        action: str,
        reviewer_id: str | None = None,
        dataset_id: int | None = None,
    ) -> dict:
        return self.service.review_sample(
            sample_id,
            action=action,
            reviewer_id=reviewer_id,
            dataset_id=dataset_id,
        )


class ListFineTuningDatasetsUseCase:
    def __init__(self, service=None):
        from app.application.services.chat_fine_tuning_service import ChatFineTuningService

        self.service = service or ChatFineTuningService()

    def execute(self, **kwargs) -> dict:
        return self.service.list_datasets(**kwargs)


class CreateFineTuningDatasetUseCase:
    def __init__(self, service=None):
        from app.application.services.chat_fine_tuning_service import ChatFineTuningService

        self.service = service or ChatFineTuningService()

    def execute(self, *, payload: dict, created_by: str | None = None) -> dict:
        return self.service.create_dataset(payload=payload, created_by=created_by)


class ApproveFineTuningDatasetUseCase:
    def __init__(self, service=None):
        from app.application.services.chat_fine_tuning_service import ChatFineTuningService

        self.service = service or ChatFineTuningService()

    def execute(self, *, dataset_id: int, approved_by: str | None = None) -> dict:
        return self.service.approve_dataset(dataset_id, approved_by=approved_by)


class ExportFineTuningDatasetUseCase:
    def __init__(self, service=None):
        from app.application.services.chat_fine_tuning_service import ChatFineTuningService

        self.service = service or ChatFineTuningService()

    def execute(self, *, dataset_id: int) -> dict:
        return self.service.export_dataset(dataset_id)


class FineTuningRunUseCase:
    def __init__(self, service=None):
        from app.application.services.chat_fine_tuning_service import ChatFineTuningService

        self.service = service or ChatFineTuningService()

    def start(self, *, dataset_id: int, created_by: str | None = None) -> dict:
        return {"run": self.service.start_run(dataset_id=dataset_id, created_by=created_by)}

    def export(self, *, run_id: int) -> dict:
        return self.service.execute_run_export(run_id)

    def train(self, *, run_id: int) -> dict:
        return self.service.execute_run_training(run_id)

    def deploy(self, *, run_id: int) -> dict:
        return self.service.deploy_run(run_id)

    def rollback(self, *, run_id: int) -> dict:
        return self.service.rollback_run(run_id)
