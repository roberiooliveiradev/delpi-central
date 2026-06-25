from __future__ import annotations

from unittest.mock import MagicMock

from app.application.use_cases.quality_action_plans.quality_action_plan_analysis_use_cases import (
    EffectivenessReviewRequest,
    RecordEffectivenessReviewUseCase,
    UpsertFiveWhysRequest,
    UpsertFiveWhysUseCase,
)
from app.application.use_cases.quality_action_plans.quality_action_plans_use_cases import (
    CreateQualityActionPlanRequest,
    CreateQualityActionPlanUseCase,
)
from app.application.use_cases.quality_action_plans.quality_intelligence_use_cases import (
    SyncCaseSimilarityIndexUseCase,
)


def test_create_plan_syncs_similarity_index():
    repo = MagicMock()
    repo.create_plan.return_value = {"id": "plan-1", "code": "PAC-2026-0001"}
    sync = MagicMock(spec=SyncCaseSimilarityIndexUseCase)

    use_case = CreateQualityActionPlanUseCase(repo, intelligence_sync=sync)
    use_case.execute(
        CreateQualityActionPlanRequest(
            title="NC teste",
            created_by_user_id="user-1",
            branch_code="01",
            nonconformity_scope="external",
        )
    )

    sync.execute.assert_called_once_with("plan-1")


def test_five_whys_syncs_similarity_index():
    repo = MagicMock()
    repo.upsert_five_whys.return_value = {"plan_id": "plan-1", "root_cause": "Causa"}
    sync = MagicMock(spec=SyncCaseSimilarityIndexUseCase)

    use_case = UpsertFiveWhysUseCase(repo, intelligence_sync=sync)
    use_case.execute(
        "plan-1",
        UpsertFiveWhysRequest(root_cause="Causa raiz", why_1="Por quê"),
        updated_by="user-1",
    )

    sync.execute.assert_called_once_with("plan-1")


def test_effectiveness_review_syncs_similarity_index():
    repo = MagicMock()
    repo.record_effectiveness_review.return_value = {"id": "plan-1", "effectiveness_status": "effective"}
    sync = MagicMock(spec=SyncCaseSimilarityIndexUseCase)

    use_case = RecordEffectivenessReviewUseCase(repo, intelligence_sync=sync)
    use_case.execute(
        "plan-1",
        EffectivenessReviewRequest(effectiveness_status="effective"),
        updated_by="user-1",
    )

    sync.execute.assert_called_once_with("plan-1")


def test_sync_repository_builds_search_text_from_plan_fields():
    from app.infrastructure.persistence.plugins.repositories.quality_action_plans.postgres_quality_intelligence_repository import (
        PostgresQualityIntelligenceRepository,
    )

    repo = PostgresQualityIntelligenceRepository(connection=MagicMock())
    repo.fetch_one = MagicMock(  # type: ignore[method-assign]
        return_value={
            "title": "Trinca no chicote",
            "reported_problem": "Defeito visual",
            "product_code": "14297268",
            "customer_name": "Cliente X",
            "problem_category": "Aparência",
            "failure_mode": "trinca",
            "root_cause_category": None,
            "symptom_tags": ["trinca"],
            "branch_code": "01",
            "product_description": "CHICOTE",
            "root_cause": "Parâmetro incorreto",
        }
    )
    repo.execute = MagicMock()  # type: ignore[method-assign]

    repo.sync_case_similarity_index("plan-uuid")

    repo.execute.assert_called_once()
    params = repo.execute.call_args[0][1]
    assert params[0] == "plan-uuid"
    assert "Trinca no chicote" in params[1]
    assert "Parâmetro incorreto" in params[1]
    assert params[2] == "14297268"
