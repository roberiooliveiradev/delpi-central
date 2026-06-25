"""Recorrência PAC — agrupamento por recurrence_key (Onda 2.3)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from app.domain.services.quality_action_plans.pac_quality_branch_service import (
    parse_recurrence_key,
)


def test_parse_recurrence_key_splits_segments() -> None:
    parsed = parse_recurrence_key("filial:01|produto:14297268|falha:trinca superficial")
    assert parsed == {
        "branch_code": "01",
        "product_code": "14297268",
        "failure_mode": "trinca superficial",
    }


def test_parse_recurrence_key_empty() -> None:
    assert parse_recurrence_key(None) == {
        "branch_code": None,
        "product_code": None,
        "failure_mode": None,
    }


def _body(response) -> dict:
    return json.loads(response.body.decode())


@patch(
    "app.interface.http.routes.quality.action_plans_read_router.build_quality_action_plan_read_repository"
)
def test_recurrence_route_returns_operation_id(mock_build) -> None:
    from app.interface.http.routes.quality.action_plans_read_router import (
        list_action_plans_recurrence,
    )

    mock_repo = MagicMock()
    mock_repo.list_recurrence_groups.return_value = {
        "items": [
            {
                "recurrence_key": "filial:01|produto:ABC|falha:oxidacao",
                "branch_code": "01",
                "product_code": "ABC",
                "failure_mode": "oxidacao",
                "total_plans": 3,
                "open_plans": 2,
                "critical_open": 1,
                "last_plan_code": "PAC-2026-0003",
                "last_plan_id": "plan-3",
                "last_opened_at": "2026-06-01T10:00:00+00:00",
            }
        ],
        "pagination": {"page": 1, "page_size": 50, "total": 1, "total_pages": 1},
    }
    mock_build.return_value = mock_repo

    response = list_action_plans_recurrence()
    body = _body(response)

    assert body.get("success") is True
    assert body.get("meta", {}).get("operationId") == "list_quality_action_plans_recurrence"
    assert body.get("data", {}).get("items")[0]["total_plans"] == 3
    mock_repo.list_recurrence_groups.assert_called_once()
