"""AuthZ hardening: user ausente, data transfer e paridade do recálculo."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from starlette.requests import Request

from tm_app.application.gpt_actions.dispatch_service import (
    GptActionsDispatchService,
    GptActionsError,
)
from tm_app.application.governed_writes.errors import FORBIDDEN, GovernedWriteError
from tm_app.application.governed_writes.orchestrator import GovernedWriteOrchestrator
from tm_app.application.security.authorization_policy import (
    AuthorizationDenied,
    TransformometroAuthorizationPolicy,
)
from tm_app.interface.http.routes.dashboard_routes import recalcular_dashboard
from tm_app.interface.http.routes.json_backup_routes import export_json, import_preview


def _user(**kwargs):
    return SimpleNamespace(
        id="u1",
        email="u@test",
        name="U",
        permissions=kwargs.get("permissions", []),
        is_superadmin=kwargs.get("is_superadmin", False),
    )


def _request(user) -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "https",
        "path": "/transformometro/dashboard/recalcular",
        "raw_path": b"/transformometro/dashboard/recalcular",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 0),
        "server": ("test", 443),
    }
    request = Request(scope)
    request.state.user = user
    return request


def test_data_transfer_denies_missing_user_and_allows_normal_use():
    policy = TransformometroAuthorizationPolicy()
    with pytest.raises(AuthorizationDenied) as missing:
        policy.require_data_transfer(None)
    assert missing.value.status_code == 401

    with pytest.raises(AuthorizationDenied):
        policy.require_data_transfer(_user(permissions=[]))

    policy.require_data_transfer(_user(permissions=["transformometro.view"]))
    policy.require_data_transfer(_user(permissions=["transformometro.access"]))
    policy.require_data_transfer(_user(permissions=["transformometro.data.transfer"]))
    policy.require_data_transfer(_user(is_superadmin=True))
    with pytest.raises(AuthorizationDenied):
        policy.require_data_transfer(_user(permissions=["transformometro.manage"]))


def test_export_route_uses_data_transfer_gate():
    denied = export_json(_request(_user(permissions=[])))
    assert denied.status_code == 403

    with patch(
        "tm_app.interface.http.routes.json_backup_routes.JsonBackupService.export_bundle",
        return_value={"counts": {}},
    ):
        allowed = export_json(_request(_user(permissions=["transformometro.access"])))
    assert allowed.status_code == 200


def test_import_preview_does_not_run_without_permission():
    body = SimpleNamespace(data={}, mode="merge", import_format="auto")
    with patch(
        "tm_app.interface.http.routes.json_backup_routes.JsonBackupService.preview"
    ) as preview:
        denied = import_preview(body, _request(_user(permissions=[])))
    assert denied.status_code == 403
    preview.assert_not_called()


def test_dashboard_recalculate_policy_parity():
    policy = TransformometroAuthorizationPolicy()
    view_only = _user(permissions=["transformometro.view"])
    nobody = _user(permissions=[])
    recalc = _user(permissions=["transformometro.dashboard.recalculate"])
    sibling = _user(permissions=["transformometro.access"])
    normal_use = _user(permissions=["transformometro.processes.manage"])

    with pytest.raises(AuthorizationDenied):
        policy.require_dashboard_recalculate(None)
    with pytest.raises(AuthorizationDenied):
        policy.require_dashboard_recalculate(nobody)
    policy.require_dashboard_recalculate(view_only)
    policy.require_dashboard_recalculate(recalc)
    policy.require_dashboard_recalculate(sibling)
    policy.require_dashboard_recalculate(normal_use)

    http_denied = recalcular_dashboard(_request(nobody))
    assert http_denied.status_code == 403

    dispatch = GptActionsDispatchService()
    with pytest.raises(GptActionsError) as gpt:
        dispatch._require_dashboard_recalculate_access(_request(nobody))
    assert gpt.value.status_code == 403
    assert "transformometro.access" in str(gpt.value)

    with pytest.raises(GovernedWriteError) as mcp:
        GovernedWriteOrchestrator().prepare(
            _request(nobody),
            capability="recalculate_dashboard",
            args={},
        )
    assert mcp.value.code == FORBIDDEN

    with patch(
        "tm_app.interface.http.routes.dashboard_routes.DashboardRecalcService.recalculate",
        return_value={"mode": "test"},
    ), patch(
        "tm_app.interface.http.routes.dashboard_routes.notify_catalog_updated"
    ), patch(
        "tm_app.interface.http.routes.dashboard_routes.actor_from_request",
        return_value=("u1", "u@test", "U"),
    ), patch(
        "tm_app.interface.http.routes.dashboard_routes.client_id_from_request",
        return_value="test",
    ):
        allowed = recalcular_dashboard(_request(recalc))
    assert allowed.status_code == 200
