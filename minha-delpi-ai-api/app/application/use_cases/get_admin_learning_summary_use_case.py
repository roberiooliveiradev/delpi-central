from datetime import datetime, timedelta, timezone

from app.domain.services.chat_learning_metrics_service import (
    ChatLearningMetricsService,
)


class GetAdminLearningSummaryUseCase:
    def __init__(
        self,
        candidate_repository=None,
        vocabulary_repository=None,
        memory_repository=None,
        evaluation_repository=None,
        fine_tuning_repository=None,
    ):
        if candidate_repository is None:
            from app.infrastructure.persistence.postgres_learning_candidate_repository import (
                PostgresLearningCandidateRepository,
            )

            candidate_repository = PostgresLearningCandidateRepository()

        if vocabulary_repository is None:
            from app.infrastructure.persistence.postgres_vocabulary_term_repository import (
                PostgresVocabularyTermRepository,
            )

            vocabulary_repository = PostgresVocabularyTermRepository()

        if memory_repository is None:
            from app.infrastructure.persistence.postgres_memory_item_repository import (
                PostgresMemoryItemRepository,
            )

            memory_repository = PostgresMemoryItemRepository()

        if evaluation_repository is None:
            from app.infrastructure.persistence.postgres_evaluation_case_repository import (
                PostgresEvaluationCaseRepository,
            )

            evaluation_repository = PostgresEvaluationCaseRepository()

        if fine_tuning_repository is None:
            from app.infrastructure.persistence.postgres_fine_tuning_repository import (
                PostgresFineTuningRepository,
            )

            fine_tuning_repository = PostgresFineTuningRepository()

        self.candidate_repository = candidate_repository
        self.vocabulary_repository = vocabulary_repository
        self.memory_repository = memory_repository
        self.evaluation_repository = evaluation_repository
        self.fine_tuning_repository = fine_tuning_repository

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
        return summary
