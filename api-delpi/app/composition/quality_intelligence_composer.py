from app.application.use_cases.quality_action_plans.quality_intelligence_use_cases import (
    SyncCaseSimilarityIndexUseCase,
)
from app.infrastructure.persistence.plugins.repositories.quality_action_plans.postgres_quality_intelligence_repository import (
    PostgresQualityIntelligenceRepository,
)


def build_quality_intelligence_repository() -> PostgresQualityIntelligenceRepository:
    return PostgresQualityIntelligenceRepository()


def build_sync_case_similarity_index_use_case() -> SyncCaseSimilarityIndexUseCase:
    return SyncCaseSimilarityIndexUseCase(build_quality_intelligence_repository())
