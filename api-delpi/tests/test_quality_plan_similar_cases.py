from __future__ import annotations

from unittest.mock import MagicMock

from app.application.use_cases.quality_action_plans.quality_intelligence_use_cases import (
    GetPlanSimilarCasesUseCase,
    SearchSimilarCasesUseCase,
    SimilarCasesRequest,
)
from app.domain.services.quality_action_plans.case_similarity_scoring_service import (
    CaseSimilarityScoringService,
    IndexedCaseCandidate,
    SimilarCaseQuery,
)


def test_scoring_ranks_matching_product_higher():
    scoring = CaseSimilarityScoringService()
    query = SimilarCaseQuery(
        problem_description="trinca superficial no chicote",
        product_code="14297268",
        branch_code="01",
    )
    high = IndexedCaseCandidate(
        plan_id="uuid-1",
        plan_code="PAC-2025-0001",
        search_text="trinca superficial chicote aparência",
        product_code="14297268",
        failure_mode="trinca",
        root_cause_category="processo",
        symptom_tags=["trinca"],
        problem_summary="Trinca no chicote",
        root_cause="Parâmetro incorreto",
        effectiveness_status="effective",
        closed_at="2025-12-01",
        effective_actions=["Ajustar parâmetro"],
        branch_code="01",
    )
    low = IndexedCaseCandidate(
        plan_id="uuid-2",
        plan_code="PAC-2025-0002",
        search_text="cor errada etiqueta",
        product_code="99999999",
        failure_mode="cor",
        root_cause_category="fornecedor",
        symptom_tags=[],
        problem_summary="Cor divergente",
        root_cause="Lote fornecedor",
        effectiveness_status="pending",
        closed_at=None,
        effective_actions=[],
        branch_code="02",
    )

    ranked = scoring.rank_cases(query, [low, high])
    assert ranked[0]["plan_id"] == "PAC-2025-0001"
    assert scoring.score(query, high) > scoring.score(query, low)


def test_search_similar_cases_excludes_current_plan():
    repo = MagicMock()
    repo.fetch_similar_case_candidates.return_value = [
        {
            "plan_id": "other-uuid",
            "plan_code": "PAC-2025-0099",
            "search_text": "trinca chicote",
            "product_code": "14297268",
            "failure_mode": "trinca",
            "root_cause_category": "processo",
            "symptom_tags": [],
            "problem_summary": "Trinca",
            "root_cause": "Parâmetro",
            "effectiveness_status": "effective",
            "closed_at": None,
            "effective_actions": [],
            "branch_code": "01",
        }
    ]
    use_case = SearchSimilarCasesUseCase(repo)

    result = use_case.execute(
        SimilarCasesRequest(
            problem_description="trinca no chicote",
            product_code="14297268",
            exclude_plan_id="current-uuid",
        )
    )

    repo.fetch_similar_case_candidates.assert_called_once()
    assert repo.fetch_similar_case_candidates.call_args.kwargs["exclude_plan_id"] == "current-uuid"
    assert len(result["similar_cases"]) == 1


def test_get_plan_similar_cases_builds_request_from_detail():
    plan_repo = MagicMock()
    plan_repo.get_plan_detail.return_value = {
        "plan": {
            "id": "plan-1",
            "title": "NC chicote",
            "reported_problem": "Trinca superficial",
            "product_code": "14297268",
            "symptom_tags": ["trinca"],
            "failure_mode": "trinca",
            "branch_code": "01",
        },
        "five_whys": {"root_cause": "Parâmetro de corte"},
    }
    search = MagicMock()
    search.execute.return_value = {"similar_cases": [], "recurrence_signals": {}, "suggested_focus_areas": []}

    result = GetPlanSimilarCasesUseCase(plan_repo, search).execute("plan-1")

    assert result is not None
    search.execute.assert_called_once()
    request = search.execute.call_args[0][0]
    assert request.problem_description == "Trinca superficial"
    assert request.product_code == "14297268"
    assert request.exclude_plan_id == "plan-1"
