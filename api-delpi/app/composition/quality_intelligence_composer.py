from app.application.use_cases.quality_action_plans.quality_intelligence_use_cases import (
    GetPlanSimilarCasesUseCase,
    SearchSimilarCasesUseCase,
    SyncCaseSimilarityIndexUseCase,
)
from app.infrastructure.persistence.plugins.repositories.quality_action_plans.postgres_quality_intelligence_repository import (
    PostgresQualityIntelligenceRepository,
)


def build_quality_intelligence_repository() -> PostgresQualityIntelligenceRepository:
    return PostgresQualityIntelligenceRepository()


def build_sync_case_similarity_index_use_case() -> SyncCaseSimilarityIndexUseCase:
    return SyncCaseSimilarityIndexUseCase(build_quality_intelligence_repository())


def build_search_similar_cases_use_case() -> SearchSimilarCasesUseCase:
    return SearchSimilarCasesUseCase(build_quality_intelligence_repository())


def build_get_plan_similar_cases_use_case() -> GetPlanSimilarCasesUseCase:
    from app.composition.quality_action_plans_composer import (
        build_quality_action_plan_read_repository,
    )

    return GetPlanSimilarCasesUseCase(
        build_quality_action_plan_read_repository(),
        build_search_similar_cases_use_case(),
    )
