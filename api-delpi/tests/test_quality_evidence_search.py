"""Busca textual em evidências PAC — Onda 2.9."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch


def _body(response) -> dict:
    return json.loads(response.body.decode())


@patch(
    "app.interface.http.routes.quality.action_plans_read_router.build_quality_action_plan_read_repository"
)
def test_search_evidences_route_returns_operation_id(mock_build) -> None:
    from app.interface.http.routes.quality.action_plans_read_router import (
        search_action_plan_evidences,
    )

    mock_repo = MagicMock()
    mock_repo.search_evidences.return_value = {
        "query": "foto",
        "items": [
            {
                "id": "ev-1",
                "plan_id": "plan-1",
                "file_name": "foto-nc.png",
                "plan_code": "PAC-2026-0001",
            }
        ],
        "pagination": {"page": 1, "page_size": 50, "total": 1, "total_pages": 1},
    }
    mock_build.return_value = mock_repo

    response = search_action_plan_evidences(q="foto")
    body = _body(response)

    assert body.get("success") is True
    assert body.get("meta", {}).get("operationId") == "search_quality_action_plan_evidences"
    assert body.get("data", {}).get("items")[0]["file_name"] == "foto-nc.png"
    mock_repo.search_evidences.assert_called_once()


@patch(
    "app.interface.http.routes.quality.action_plans_read_router.build_quality_action_plan_read_repository"
)
def test_list_evidences_accepts_query_filter(mock_build) -> None:
    from app.interface.http.routes.quality.action_plans_read_router import list_plan_evidences

    mock_repo = MagicMock()
    mock_repo.get_plan_by_id.return_value = {"id": "plan-1"}
    mock_repo.list_evidences.return_value = [{"id": "ev-1", "file_name": "anexo.pdf"}]
    mock_build.return_value = mock_repo

    response = list_plan_evidences("plan-1", q="anexo")
    body = _body(response)

    assert body.get("success") is True
    mock_repo.list_evidences.assert_called_once_with("plan-1", q="anexo")
