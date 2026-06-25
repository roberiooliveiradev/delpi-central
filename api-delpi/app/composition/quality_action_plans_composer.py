from app.application.use_cases.quality_action_plans.quality_action_plan_analysis_use_cases import (
    CreatePlanActionsUseCase,
    RecordEffectivenessReviewUseCase,
    UpdatePlanActionUseCase,
    UpsertFiveWhysUseCase,
    UpsertIshikawaUseCase,
)
from app.application.use_cases.quality_action_plans.quality_action_plans_use_cases import (
    CreateQualityActionPlanUseCase,
    ReopenQualityActionPlanUseCase,
    UpdateQualityActionPlanStatusUseCase,
    UpdateQualityActionPlanUseCase,
)
from app.composition.quality_intelligence_composer import build_sync_case_similarity_index_use_case
from app.infrastructure.persistence.plugins.repositories.quality_action_plans.postgres_quality_action_plan_read_repository import (
    PostgresQualityActionPlanRepository,
)


def build_quality_action_plan_repository() -> PostgresQualityActionPlanRepository:
    return PostgresQualityActionPlanRepository()


def build_quality_action_plan_read_repository() -> PostgresQualityActionPlanRepository:
    return build_quality_action_plan_repository()


def build_create_quality_action_plan_use_case() -> CreateQualityActionPlanUseCase:
    return CreateQualityActionPlanUseCase(
        build_quality_action_plan_repository(),
        intelligence_sync=build_sync_case_similarity_index_use_case(),
    )


def build_update_quality_action_plan_status_use_case() -> UpdateQualityActionPlanStatusUseCase:
    return UpdateQualityActionPlanStatusUseCase(build_quality_action_plan_repository())


def build_reopen_quality_action_plan_use_case() -> ReopenQualityActionPlanUseCase:
    return ReopenQualityActionPlanUseCase(build_quality_action_plan_repository())


def build_update_quality_action_plan_use_case() -> UpdateQualityActionPlanUseCase:
    return UpdateQualityActionPlanUseCase(build_quality_action_plan_repository())


def build_upsert_ishikawa_use_case() -> UpsertIshikawaUseCase:
    return UpsertIshikawaUseCase(build_quality_action_plan_repository())


def build_upsert_five_whys_use_case() -> UpsertFiveWhysUseCase:
    return UpsertFiveWhysUseCase(
        build_quality_action_plan_repository(),
        intelligence_sync=build_sync_case_similarity_index_use_case(),
    )


def build_create_plan_actions_use_case() -> CreatePlanActionsUseCase:
    return CreatePlanActionsUseCase(build_quality_action_plan_repository())


def build_update_plan_action_use_case() -> UpdatePlanActionUseCase:
    return UpdatePlanActionUseCase(build_quality_action_plan_repository())


def build_record_effectiveness_review_use_case() -> RecordEffectivenessReviewUseCase:
    return RecordEffectivenessReviewUseCase(
        build_quality_action_plan_repository(),
        intelligence_sync=build_sync_case_similarity_index_use_case(),
    )
