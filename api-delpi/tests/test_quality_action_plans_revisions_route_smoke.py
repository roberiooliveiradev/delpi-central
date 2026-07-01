"""Smoke — revisões versionadas PAC."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from app.interface.http.routes.quality.action_plans_read_router import (
    get_plan_revision,
    list_plan_revisions,
    restore_plan_revision,
)


def _body(response) -> dict:
    return json.loads(response.body.decode())


@patch(
    "app.interface.http.routes.quality.action_plans_read_router.build_quality_action_plan_read_repository"
)
@patch(
    "app.interface.http.routes.quality.action_plans_read_router.build_list_plan_revisions_use_case"
)
def test_list_revisions_route_returns_operation_id(mock_build_uc, mock_build_repo) -> None:
    mock_repo = MagicMock()
    mock_repo.get_plan_by_id.return_value = {"id": "plan-1"}
    mock_build_repo.return_value = mock_repo

    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = {
        "items": [{"revision_number": 1, "change_scope": "created"}],
        "pagination": {"page": 1, "page_size": 20, "total": 1, "total_pages": 1},
    }
    mock_build_uc.return_value = mock_use_case

    response = list_plan_revisions("plan-1", page=1, page_size=20)
    body = _body(response)

    assert body.get("success") is True
    assert body.get("meta", {}).get("operationId") == "list_quality_action_plan_revisions"
    assert len(body.get("data", {}).get("items", [])) == 1


@patch(
    "app.interface.http.routes.quality.action_plans_read_router.build_quality_action_plan_read_repository"
)
@patch(
    "app.interface.http.routes.quality.action_plans_read_router.build_get_plan_revision_use_case"
)
def test_get_revision_route_returns_snapshot(mock_build_uc, mock_build_repo) -> None:
    mock_repo = MagicMock()
    mock_repo.get_plan_by_id.return_value = {"id": "plan-1"}
    mock_build_repo.return_value = mock_repo

    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = {
        "revision_number": 2,
        "change_scope": "identification",
        "snapshot": {"schema_version": 1, "plan": {"title": "Antigo"}},
    }
    mock_build_uc.return_value = mock_use_case

    response = get_plan_revision("plan-1", 2)
    body = _body(response)

    assert body.get("success") is True
    assert body.get("meta", {}).get("operationId") == "get_quality_action_plan_revision"
    assert body.get("data", {}).get("revision_number") == 2


@patch(
    "app.interface.http.routes.quality.action_plans_read_router.build_restore_plan_revision_use_case"
)
def test_restore_revision_route_returns_operation_id(mock_build) -> None:
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = {
        "plan": {"id": "plan-1", "title": "Restaurado"},
        "actions": [],
    }
    mock_build.return_value = mock_use_case

    response = restore_plan_revision("plan-1", 1)
    body = _body(response)

    assert body.get("success") is True
    assert body.get("meta", {}).get("operationId") == "restore_quality_action_plan_revision"
    mock_use_case.execute.assert_called_once()
