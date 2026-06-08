from datetime import datetime, timedelta, timezone

from app.domain.ports.evaluation_case_repository_port import EvaluationCaseRepositoryPort
from app.domain.ports.fine_tuning_repository_port import FineTuningRepositoryPort
from app.domain.ports.knowledge_repository_port import KnowledgeRepositoryPort
from app.domain.ports.learning_candidate_repository_port import LearningCandidateRepositoryPort
from app.domain.ports.memory_item_repository_port import MemoryItemRepositoryPort
from app.domain.ports.vocabulary_term_repository_port import VocabularyTermRepositoryPort
from app.domain.services.chat_learning_dashboard_service import (
    ChatLearningDashboardService,
)
from app.domain.services.chat_learning_metrics_service import (
    ChatLearningMetricsService,
)


def _default_candidate_repository() -> LearningCandidateRepositoryPort:
    from app.composition.repository_composer import make_learning_candidate_repository

    return make_learning_candidate_repository()


def _default_vocabulary_repository() -> VocabularyTermRepositoryPort:
    from app.composition.repository_composer import make_vocabulary_term_repository

    return make_vocabulary_term_repository()


def _default_memory_repository() -> MemoryItemRepositoryPort:
    from app.composition.repository_composer import make_memory_item_repository

    return make_memory_item_repository()


def _default_evaluation_repository() -> EvaluationCaseRepositoryPort:
    from app.composition.repository_composer import make_evaluation_case_repository

    return make_evaluation_case_repository()


def _default_fine_tuning_repository() -> FineTuningRepositoryPort:
    from app.composition.repository_composer import make_fine_tuning_repository

    return make_fine_tuning_repository()


def _default_knowledge_repository() -> KnowledgeRepositoryPort:
    from app.composition.repository_composer import make_knowledge_repository

    return make_knowledge_repository()


class GetAdminLearningSummaryUseCase:
    def __init__(
        self,
        candidate_repository: LearningCandidateRepositoryPort | None = None,
        vocabulary_repository: VocabularyTermRepositoryPort | None = None,
        memory_repository: MemoryItemRepositoryPort | None = None,
        evaluation_repository: EvaluationCaseRepositoryPort | None = None,
        fine_tuning_repository: FineTuningRepositoryPort | None = None,
        knowledge_repository: KnowledgeRepositoryPort | None = None,
    ):
        self.candidate_repository = candidate_repository or _default_candidate_repository()
        self.vocabulary_repository = vocabulary_repository or _default_vocabulary_repository()
        self.memory_repository = memory_repository or _default_memory_repository()
        self.evaluation_repository = evaluation_repository or _default_evaluation_repository()
        self.fine_tuning_repository = fine_tuning_repository or _default_fine_tuning_repository()
        self.knowledge_repository = knowledge_repository or _default_knowledge_repository()

    def execute(self, *, hours: int = 168) -> dict:
        window = max(1, int(hours))
        since = datetime.now(timezone.utc) - timedelta(hours=window)

        candidates = self.candidate_repository.summary(since=since)
        vocabulary = self.vocabulary_repository.summary()
        memory = self.memory_repository.summary()
        evaluation = self.evaluation_repository.summary()
        fine_tuning = self.fine_tuning_repository.summary()

        summary = ChatLearningMetricsService.assemble(
            candidates=candidates,
            vocabulary=vocabulary,
            memory=memory,
            evaluation=evaluation,
            fine_tuning=fine_tuning,
        )
        summary["windowHours"] = window

        try:
            rag_counts = self.knowledge_repository.count_active_documents_by_source_type()
            top_typos = self.vocabulary_repository.list_top_typo_rules(limit=8)
            summary = ChatLearningDashboardService.enrich(
                summary=summary,
                rag_index_counts=rag_counts,
                top_typo_rules=top_typos,
            )
        except Exception:
            pass

        return summary
