from app.application.use_cases.quality_action_plans.quality_intelligence_use_cases import (
    AssessRecurrenceOnOpeningUseCase,
    GetPlanSimilarCasesUseCase,
    ListSolutionPatternsUseCase,
    PromoteSolutionPatternFromPlanUseCase,
    SearchSimilarCasesUseCase,
    SyncCaseSimilarityIndexUseCase,
)
from app.infrastructure.embeddings.null_case_similarity_embedding_gateway import (
    NullCaseSimilarityEmbeddingGateway,
)
from app.infrastructure.embeddings.ollama_case_similarity_embedding_gateway import (
    OllamaCaseSimilarityEmbeddingGateway,
)
from app.infrastructure.persistence.plugins.repositories.quality_action_plans.postgres_quality_intelligence_repository import (
    PostgresQualityIntelligenceRepository,
)


def build_quality_intelligence_repository() -> PostgresQualityIntelligenceRepository:
    return PostgresQualityIntelligenceRepository()


def build_case_similarity_embedding_gateway():
    gateway = OllamaCaseSimilarityEmbeddingGateway()
    if gateway.is_enabled():
        return gateway
    return NullCaseSimilarityEmbeddingGateway()


def build_sync_case_similarity_index_use_case() -> SyncCaseSimilarityIndexUseCase:
    return SyncCaseSimilarityIndexUseCase(
        build_quality_intelligence_repository(),
        embedding_gateway=build_case_similarity_embedding_gateway(),
    )


def build_search_similar_cases_use_case() -> SearchSimilarCasesUseCase:
    return SearchSimilarCasesUseCase(
        build_quality_intelligence_repository(),
        embedding_gateway=build_case_similarity_embedding_gateway(),
    )


def build_get_plan_similar_cases_use_case() -> GetPlanSimilarCasesUseCase:
    from app.composition.quality_action_plans_composer import (
        build_quality_action_plan_read_repository,
    )

    return GetPlanSimilarCasesUseCase(
        build_quality_action_plan_read_repository(),
        build_search_similar_cases_use_case(),
    )


def build_list_solution_patterns_use_case() -> ListSolutionPatternsUseCase:
    return ListSolutionPatternsUseCase(build_quality_intelligence_repository())


def build_promote_solution_pattern_from_plan_use_case() -> PromoteSolutionPatternFromPlanUseCase:
    return PromoteSolutionPatternFromPlanUseCase(build_quality_intelligence_repository())


def build_assess_recurrence_on_opening_use_case() -> AssessRecurrenceOnOpeningUseCase:
    return AssessRecurrenceOnOpeningUseCase(
        build_quality_intelligence_repository(),
        build_search_similar_cases_use_case(),
    )
