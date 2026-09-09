"""CreatePlanActionsUseCase — validação de status e cause_track."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.application.use_cases.quality_action_plans.quality_action_plan_analysis_use_cases import (
    CreateActionItemRequest,
    CreatePlanActionsUseCase,
)


def _action(**overrides):
    base = {
        "action_type": "containment",
        "description": "Segregar e revisar itens",
        "status": "in_progress",
        "cause_track": "occurrence",
        "due_date": "2026-07-17",
        "responsible_name": "Aline e Geiziara",
        "responsibles": None,
        "evidence_required": False,
    }
    base.update(overrides)
    return CreateActionItemRequest(**base)


def test_create_actions_accepts_in_progress_with_due_date_and_unlinked_responsible() -> None:
    repo = MagicMock()
    repo.create_actions.return_value = [{"id": "a1"}]
    use_case = CreatePlanActionsUseCase(repo)

    result = use_case.execute(
        "plan-1",
        [_action()],
        created_by="user-1",
        expected_revision_number=2,
    )

    assert result == [{"id": "a1"}]
    payload = repo.create_actions.call_args.args[1]
    assert payload[0]["status"] == "in_progress"
    assert payload[0]["due_date"] == "2026-07-17"
    assert payload[0]["cause_track"] == "occurrence"
    assert repo.create_actions.call_args.kwargs["expected_revision_number"] == 2


def test_create_actions_accepts_completed_status() -> None:
    repo = MagicMock()
    repo.create_actions.return_value = []
    use_case = CreatePlanActionsUseCase(repo)

    use_case.execute("plan-1", [_action(status="completed")], created_by="user-1")

    assert repo.create_actions.call_args.args[1][0]["status"] == "completed"


def test_create_actions_rejects_invalid_status() -> None:
    use_case = CreatePlanActionsUseCase(MagicMock())
    with pytest.raises(ValueError, match="status"):
        use_case.execute("plan-1", [_action(status="weird")], created_by="user-1")


def test_create_actions_normalizes_empty_cause_track() -> None:
    repo = MagicMock()
    repo.create_actions.return_value = []
    use_case = CreatePlanActionsUseCase(repo)

    use_case.execute("plan-1", [_action(cause_track="")], created_by="user-1")

    assert repo.create_actions.call_args.args[1][0]["cause_track"] is None
