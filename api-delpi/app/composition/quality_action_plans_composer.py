from app.infrastructure.persistence.plugins.repositories.quality_action_plans.postgres_quality_action_plan_read_repository import (
    PostgresQualityActionPlanReadRepository,
)


def build_quality_action_plan_read_repository() -> PostgresQualityActionPlanReadRepository:
    return PostgresQualityActionPlanReadRepository()
