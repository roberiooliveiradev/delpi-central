from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.application.use_cases.quality_action_plans.quality_action_plan_analysis_use_cases import (
    UpdatePlanActionUseCase,
)


def test_update_plan_action_blocks_completion_without_required_evidence():
    repo = MagicMock()
    repo.get_action.return_value = {
        "id": "act-1",
        "evidence_required": True,
        "status": "pending",
    }
    repo.count_evidences_for_action.return_value = 0

    use_case = UpdatePlanActionUseCase(repo)

    with pytest.raises(ValueError, match="evidência vinculada"):
        use_case.execute(
            "plan-1",
            "act-1",
            {"status": "completed"},
            updated_by="user-1",
        )

    repo.update_action.assert_not_called()


def test_update_plan_action_allows_completion_with_required_evidence_attached():
    repo = MagicMock()
    repo.get_action.return_value = {
        "id": "act-1",
        "evidence_required": True,
        "status": "pending",
    }
    repo.count_evidences_for_action.return_value = 1
    repo.update_action.return_value = {"id": "act-1", "status": "completed"}

    use_case = UpdatePlanActionUseCase(repo)
    result = use_case.execute(
        "plan-1",
        "act-1",
        {"status": "completed"},
        updated_by="user-1",
    )

    assert result["status"] == "completed"
    repo.update_action.assert_called_once()


def test_update_plan_action_allows_completion_when_evidence_not_required():
    repo = MagicMock()
    repo.get_action.return_value = {
        "id": "act-1",
        "evidence_required": False,
        "status": "pending",
    }
    repo.update_action.return_value = {"id": "act-1", "status": "completed"}

    use_case = UpdatePlanActionUseCase(repo)
    use_case.execute(
        "plan-1",
        "act-1",
        {"status": "completed"},
        updated_by="user-1",
    )

    repo.count_evidences_for_action.assert_not_called()
