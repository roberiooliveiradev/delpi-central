from unittest.mock import MagicMock

from app.application.use_cases.quality_action_plans.quality_intelligence_use_cases import (
    AssessRecurrenceOnOpeningRequest,
    AssessRecurrenceOnOpeningUseCase,
)
from app.domain.services.quality_action_plans.pac_recurrence_proactive_alert_service import (
    PacRecurrenceProactiveAlertService,
)


def test_recurrence_score_high_when_many_open_plans():
    score = PacRecurrenceProactiveAlertService.compute_score(
        plans_in_window=4,
        open_plans=3,
        total_plans=6,
    )
    level = PacRecurrenceProactiveAlertService.resolve_alert_level(
        recurrence_score=score,
        plans_in_window=4,
    )
    assert score >= 0.75
    assert level == "high"


def test_assess_recurrence_on_opening_use_case():
    repository = MagicMock()
    repository.fetch_recurrence_opening_stats.return_value = {
        "plans_in_window": 3,
        "open_plans": 2,
        "total_plans": 5,
    }
    search = MagicMock()
    search.execute.return_value = {
        "similar_cases": [{"plan_id": "PAC-1"}],
        "recurrence_signals": {"same_product": 3, "same_symptom": 1, "same_root_cause_category": 0},
        "similar_cases_decision_log": {"entries": []},
    }

    result = AssessRecurrenceOnOpeningUseCase(repository, search).execute(
        AssessRecurrenceOnOpeningRequest(
            problem_description="oxidação em parafusos",
            product_code="90110001",
            failure_mode="oxidação",
            branch_code="01",
        )
    )

    assert result["should_warn_before_opening"] is True
    assert result["recurrence_key"] == "filial:01|produto:90110001|falha:oxidação"
