"""Smoke — dispatch de notificações PAC (Onda 4.1)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from app.interface.http.routes.quality.action_plans_read_router import (
    dispatch_quality_action_plan_notifications,
)


def _body(response) -> dict:
    return json.loads(response.body.decode())


@patch(
    "app.interface.http.routes.quality.action_plans_read_router.build_dispatch_pac_quality_notifications_use_case"
)
@patch(
    "app.interface.http.routes.quality.action_plans_read_router.request_has_valid_internal_service_token",
    return_value=True,
)
def test_dispatch_notifications_route_returns_operation_id(mock_token, mock_build) -> None:
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = MagicMock(
        enabled=True,
        dry_run=False,
        candidates=2,
        sent=2,
        skipped_duplicate=0,
        skipped_no_recipient=0,
        failed=0,
    )
    mock_build.return_value = mock_use_case

    response = dispatch_quality_action_plan_notifications(
        request=MagicMock(),
        dry_run=False,
    )
    body = _body(response)

    assert body.get("success") is True
    assert (
        body.get("meta", {}).get("operationId")
        == "dispatch_quality_action_plan_notifications"
    )
    assert body.get("data", {}).get("sent") == 2
