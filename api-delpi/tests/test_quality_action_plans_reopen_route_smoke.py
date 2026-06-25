"""Smoke — reabertura PAC Onda 4."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from app.interface.http.routes.quality.action_plans_read_router import (
    ReopenActionPlanBody,
    reopen_action_plan,
)


def _body(response) -> dict:
    return json.loads(response.body.decode())


@patch(
    "app.interface.http.routes.quality.action_plans_read_router.build_reopen_quality_action_plan_use_case"
)
def test_reopen_route_returns_operation_id(mock_build) -> None:
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = {
        "id": "plan-1",
        "status": "in_progress",
        "code": "PAC-2026-0001",
    }
    mock_build.return_value = mock_use_case

    response = reopen_action_plan(
        "plan-1",
        ReopenActionPlanBody(
            reason="Nova evidência exige retomada do plano.",
            target_status="in_progress",
        ),
    )
    body = _body(response)

    assert body.get("success") is True
    assert body.get("meta", {}).get("operationId") == "reopen_quality_action_plan"
    assert body.get("data", {}).get("status") == "in_progress"
    mock_use_case.execute.assert_called_once()
