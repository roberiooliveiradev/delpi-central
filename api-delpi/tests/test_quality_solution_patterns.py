"""Padrões de solução PAC — Onda 2.5 / 2.7 (api-delpi local)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from app.application.use_cases.quality_action_plans.quality_intelligence_use_cases import (
    ListSolutionPatternsUseCase,
    PromoteSolutionPatternFromPlanUseCase,
)


def _body(response) -> dict:
    return json.loads(response.body.decode())


def test_list_solution_patterns_use_case_delegates_to_repository() -> None:
    repo = MagicMock()
    repo.list_solution_patterns.return_value = {
        "items": [{"id": "pat-1", "title": "Tratamento oxidação"}],
        "pagination": {"page": 1, "page_size": 50, "total": 1, "total_pages": 1},
    }
    use_case = ListSolutionPatternsUseCase(repo)

    result = use_case.execute(failure_mode="oxidacao", page=1, page_size=50)

    assert result["items"][0]["title"] == "Tratamento oxidação"
    repo.list_solution_patterns.assert_called_once()


def test_promote_solution_pattern_rejects_ineffective_plan() -> None:
    repo = MagicMock()
    repo.upsert_solution_pattern_from_plan.side_effect = ValueError(
        "Promova apenas planos com eficácia effective ou partially_effective."
    )
    use_case = PromoteSolutionPatternFromPlanUseCase(repo)

    try:
        use_case.execute("plan-1")
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "eficácia" in str(exc)


@patch(
    "app.interface.http.routes.quality.solution_patterns_router.build_list_solution_patterns_use_case"
)
def test_list_solution_patterns_route_returns_operation_id(mock_build) -> None:
    from app.interface.http.routes.quality.solution_patterns_router import list_solution_patterns

    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = {
        "items": [],
        "pagination": {"page": 1, "page_size": 50, "total": 0, "total_pages": 1},
    }
    mock_build.return_value = mock_use_case

    response = list_solution_patterns()
    body = _body(response)

    assert body.get("success") is True
    assert body.get("meta", {}).get("operationId") == "list_quality_solution_patterns"


@patch(
    "app.interface.http.routes.quality.action_plans_read_router.build_promote_solution_pattern_from_plan_use_case"
)
def test_promote_solution_pattern_route_returns_operation_id(mock_build) -> None:
    from app.interface.http.routes.quality.action_plans_read_router import promote_solution_pattern

    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = {
        "id": "pat-1",
        "title": "Padrão PAC-2026-0001",
        "recommended_actions": ["Revisar processo"],
    }
    mock_build.return_value = mock_use_case

    response = promote_solution_pattern("plan-1")
    body = _body(response)

    assert body.get("success") is True
    assert body.get("meta", {}).get("operationId") == "promote_quality_action_plan_solution_pattern"
    assert body.get("data", {}).get("id") == "pat-1"
