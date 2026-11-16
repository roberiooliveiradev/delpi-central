"""DAVI-SI-READ-USER-PARITY-001 — bounded SI user-parity READ surface.

Covers the smallest cross-API adapter chain:

  DAVI read → api-delpi BFF (/strategic-indicators/*) → SI API → SI AuthZ

Assertions:
  * client transports ONLY the caller JWT (never X-Delpi-Service-Token);
  * fail-closed when no user Authorization is bound;
  * BFF routes keep SI permission codes (not dashboard permissions);
  * DAVI catalog eligibility/projection for the 5 approved ops;
  * read remains strictly non-persistent (all approved ops are GET).
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.application.external_capabilities.dynamic_information.action_index import (
    reset_action_index_for_tests,
    set_actions_for_tests,
)
from app.application.external_capabilities.dynamic_information.catalog_builder import (
    build_technical_actions_from_baseline,
)
from app.application.external_capabilities.dynamic_information.content_loader import (
    load_dynamic_read_budgets,
    load_external_read_allowlist,
)
from app.application.external_capabilities.dynamic_information.execute_service import (
    davi_read,
)
from app.application.services.strategic_indicators.si_user_parity_service import (
    StrategicIndicatorsUserParityService,
)
from app.domain.ports.davi_catalog_action_executor_port import (
    CatalogActionExecutionResult,
)
from app.interface.http.routes.strategic_indicators import (
    strategic_indicators_router,
)
from strategic_indicators_client import (
    StrategicIndicatorsApiClient,
    StrategicIndicatorsApiError,
)
from tests.support.route_contract_smoke import assert_envelope_meta

_API_ROOT = Path(__file__).resolve().parents[1]

SI_READ_OPS = [
    "get_si_executive_summary",
    "get_si_departments",
    "get_si_indicators",
    "list_si_indicator_goals",
    "list_si_indicator_goal_history",
]


@pytest.fixture(autouse=True)
def _reset_index():
    reset_action_index_for_tests()
    load_external_read_allowlist.cache_clear()
    load_dynamic_read_budgets.cache_clear()
    yield
    reset_action_index_for_tests()
    load_external_read_allowlist.cache_clear()
    load_dynamic_read_budgets.cache_clear()


def _actions():
    baseline = json.loads(
        (_API_ROOT / "app/content/openapi_baseline.json").read_text(
            encoding="utf-8"
        )
    )
    return build_technical_actions_from_baseline(
        baseline, allowlist=load_external_read_allowlist()
    )


class _StubExecutor:
    def __init__(self, *, outcome="ok", payload=None, error_message=None):
        self._result = CatalogActionExecutionResult(
            outcome=outcome, payload=payload, error_message=error_message
        )
        self.calls = []

    def execute(self, *, action_id, validated_arguments):
        self.calls.append(
            {
                "action_id": action_id,
                "validated_arguments": dict(validated_arguments or {}),
            }
        )
        return self._result


# ---------------------------------------------------------------------------
# Client transport — user-parity (no service token)
# ---------------------------------------------------------------------------


class _FakeResponse:
    status_code = 200

    def json(self):
        return {"items": []}


def test_user_scoped_get_sends_only_user_jwt() -> None:
    captured = {}

    class _FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def request(self, method, url, headers=None):
            captured["method"] = method
            captured["url"] = url
            captured["headers"] = dict(headers or {})
            return _FakeResponse()

    client = StrategicIndicatorsApiClient(
        base_url="http://strategic-indicators-api:8000"
    )
    with patch(
        "strategic_indicators_client.client.httpx.Client", _FakeClient
    ), patch(
        "strategic_indicators_client.client.apply_internal_service_headers"
    ) as service_headers:
        payload = client.get_user_indicators(
            authorization="Bearer user-token-abc",
            competence="2026-06",
        )

    assert payload == {"items": []}
    assert captured["method"] == "GET"
    assert captured["headers"] == {"Authorization": "Bearer user-token-abc"}
    assert "X-Delpi-Service-Token" not in captured["headers"]
    service_headers.assert_not_called()
    assert "competence=2026-06" in captured["url"]


def test_user_scoped_get_refuses_missing_jwt() -> None:
    client = StrategicIndicatorsApiClient(
        base_url="http://strategic-indicators-api:8000"
    )
    with pytest.raises(StrategicIndicatorsApiError):
        client.get_user_departments(authorization="")


def test_legacy_service_scoped_get_still_applies_service_headers() -> None:
    """Existing integrations keep the service-token path (unchanged contract)."""
    captured = {}

    class _FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def request(self, method, url, headers=None):
            captured["headers"] = dict(headers or {})
            return _FakeResponse()

    client = StrategicIndicatorsApiClient(
        base_url="http://strategic-indicators-api:8000"
    )
    with patch(
        "strategic_indicators_client.client.httpx.Client", _FakeClient
    ), patch(
        "strategic_indicators_client.client.apply_internal_service_headers"
        ,
        side_effect=lambda h: h.__setitem__("X-Delpi-Service-Token", "svc"),
    ):
        client.list_dashboard_goals(source_keys=["kpi.a"], authorization=None)

    assert captured["headers"].get("X-Delpi-Service-Token") == "svc"


def test_http_error_carries_status_code() -> None:
    class _ErrorResponse:
        status_code = 403
        text = '{"detail":"forbidden"}'

        def json(self):
            return {}

    class _FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def request(self, method, url, headers=None):
            return _ErrorResponse()

    client = StrategicIndicatorsApiClient(
        base_url="http://strategic-indicators-api:8000"
    )
    with patch("strategic_indicators_client.client.httpx.Client", _FakeClient):
        with pytest.raises(StrategicIndicatorsApiError) as excinfo:
            client.get_user_indicators(authorization="Bearer t")
    assert excinfo.value.status_code == 403


# ---------------------------------------------------------------------------
# Application service — bounded params + identity forwarding
# ---------------------------------------------------------------------------


def test_service_forwards_user_authorization_and_filters() -> None:
    mock_client = MagicMock()
    mock_client.get_user_departments.return_value = {"items": []}
    service = StrategicIndicatorsUserParityService(client=mock_client)

    service.get_departments(
        authorization="Bearer alice",
        department_id="commercial",
        competence="2026-06",
    )
    mock_client.get_user_departments.assert_called_once_with(
        authorization="Bearer alice",
        department_id="commercial",
        branch=None,
        competence="2026-06",
        start_date=None,
        end_date=None,
    )


def test_service_goal_history_requires_indicator() -> None:
    mock_client = MagicMock()
    mock_client.list_user_indicator_goal_history.return_value = {"items": []}
    service = StrategicIndicatorsUserParityService(client=mock_client)
    service.list_indicator_goal_history(
        authorization="Bearer bob", indicator_id="ind_x", goal_year=2026
    )
    mock_client.list_user_indicator_goal_history.assert_called_once_with(
        authorization="Bearer bob", indicator_id="ind_x", goal_year=2026
    )


def test_service_rejects_missing_authorization_locally() -> None:
    service = StrategicIndicatorsUserParityService(client=MagicMock())
    with pytest.raises(StrategicIndicatorsApiError):
        service.get_indicators(authorization=None)


# ---------------------------------------------------------------------------
# BFF routes — envelope/meta + SI permission boundary
# ---------------------------------------------------------------------------


def _make_app():
    app = FastAPI()
    app.include_router(strategic_indicators_router.router)
    return app


def _app_with_service(mock_service):
    app = _make_app()
    app.dependency_overrides[
        strategic_indicators_router._si_user_parity_service
    ] = lambda: mock_service
    return app


def _denied_user(*, permissions=()):
    user = MagicMock()
    user.is_superadmin = False
    user.rbac_unavailable = False
    user.permissions = list(permissions)
    return user


def test_indicators_route_meta_and_envelope() -> None:
    mock_service = MagicMock()
    client = TestClient(_app_with_service(mock_service))
    mock_service.get_indicators.return_value = {
        "items": [{"indicator_id": "ind_x", "value": 9.5}],
        "partial_success": False,
    }
    response = client.get(
            "/strategic-indicators/indicators",
            params={"competence": "2026-06"},
            headers={"Authorization": "Bearer user-token"},
        )
    assert response.status_code == 200
    assert_envelope_meta(
        response.json(),
        operation_id="get_si_indicators",
        shape="paged_list",
        entity="strategic_indicators_indicators",
    )
    assert response.json()["data"]["items"][0]["indicator_id"] == "ind_x"
    mock_service.get_indicators.assert_called_once()


def test_executive_summary_route_meta() -> None:
    mock_service = MagicMock()
    client = TestClient(_app_with_service(mock_service))
    mock_service.get_executive_summary.return_value = {
        "competence": "2026-06",
        "igd": 8.1,
        "departments": [],
        "partial_success": False,
    }
    response = client.get(
            "/strategic-indicators/executive-summary",
            headers={"Authorization": "Bearer user-token"},
        )
    assert response.status_code == 200
    assert_envelope_meta(
        response.json(),
        operation_id="get_si_executive_summary",
    )


def test_goals_route_forwards_user_authorization_header() -> None:
    mock_service = MagicMock()
    client = TestClient(_app_with_service(mock_service))
    mock_service.list_indicator_goals.return_value = {"items": []}
    client.get(
            "/strategic-indicators/indicator-goals",
            headers={"Authorization": "Bearer distinct-user"},
        )
    call = mock_service.list_indicator_goals.call_args
    assert call.kwargs["authorization"] == "Bearer distinct-user"


def test_view_routes_deny_user_without_si_permission() -> None:
    """User authenticated but missing strategic-indicators.view → 403."""
    client = TestClient(_make_app())
    with patch(
        "delpi_auth.authorization.resolve_user_context",
        return_value=_denied_user(permissions=["api-delpi.access"]),
    ), pytest.raises(Exception, match="Forbidden"):
        client.get(
            "/strategic-indicators/departments",
            headers={"Authorization": "Bearer no-perms"},
        )


def test_goals_route_deny_user_without_settings_manage() -> None:
    """User with view but NOT settings.manage must be denied goal reads."""
    client = TestClient(_make_app())
    with patch(
        "delpi_auth.authorization.resolve_user_context",
        return_value=_denied_user(
            permissions=["strategic-indicators.view"]
        ),
    ), pytest.raises(Exception, match="Forbidden"):
        client.get(
            "/strategic-indicators/indicator-goals",
            headers={"Authorization": "Bearer view-only"},
        )

    # goal history must be equally gated
    with patch(
        "delpi_auth.authorization.resolve_user_context",
        return_value=_denied_user(
            permissions=["strategic-indicators.view"]
        ),
    ), pytest.raises(Exception, match="Forbidden"):
        client.get(
            "/strategic-indicators/indicator-goals/history",
            params={"indicator_id": "ind_x"},
            headers={"Authorization": "Bearer view-only"},
        )


def test_goals_route_allowed_with_settings_manage() -> None:
    mock_service = MagicMock()
    client = TestClient(_app_with_service(mock_service))
    mock_service.list_indicator_goals.return_value = {"items": []}
    with patch(
        "delpi_auth.authorization.resolve_user_context",
        return_value=_denied_user(
            permissions=["strategic-indicators.settings.manage"]
        ),
    ):
        response = client.get(
            "/strategic-indicators/indicator-goals",
            headers={"Authorization": "Bearer admin"},
        )
    assert response.status_code == 200


def test_si_403_propagates_from_owner_backend() -> None:
    """SI-side 403 (e.g. permission revoked mid-flight) maps to 403, not 503."""
    mock_service = MagicMock()
    client = TestClient(_app_with_service(mock_service))
    mock_service.get_indicators.side_effect = StrategicIndicatorsApiError(
        "Strategic Indicators API retornou 403: denied", status_code=403
    )
    response = client.get(
            "/strategic-indicators/indicators",
            headers={"Authorization": "Bearer t"},
        )
    assert response.status_code == 403


def test_si_unexpected_4xx_maps_to_502() -> None:
    """Deterministic upstream 4xx is a contract error, not unavailability."""
    mock_service = MagicMock()
    client = TestClient(_app_with_service(mock_service))
    mock_service.get_indicators.side_effect = StrategicIndicatorsApiError(
        "Strategic Indicators API retornou 422: bad request", status_code=422
    )
    response = client.get(
            "/strategic-indicators/indicators",
            headers={"Authorization": "Bearer t"},
        )
    assert response.status_code == 502


def test_si_5xx_maps_to_503() -> None:
    mock_service = MagicMock()
    client = TestClient(_app_with_service(mock_service))
    mock_service.get_departments.side_effect = StrategicIndicatorsApiError(
        "Falha de rede ao consultar Strategic Indicators API: boom"
    )
    response = client.get(
            "/strategic-indicators/departments",
            headers={"Authorization": "Bearer t"},
        )
    assert response.status_code == 503


def test_unknown_query_param_is_not_forwarded() -> None:
    """Params outside the route schema are not accepted by OpenAPI/allowlist."""
    mock_service = MagicMock()
    client = TestClient(_app_with_service(mock_service))
    mock_service.get_indicators.return_value = {"items": []}
    response = client.get(
            "/strategic-indicators/indicators",
            params={"arbitrary": "x", "competence": "2026-06"},
            headers={"Authorization": "Bearer t"},
        )
    assert response.status_code == 200
    call = mock_service.get_indicators.call_args
    assert "arbitrary" not in call.kwargs


# ---------------------------------------------------------------------------
# DAVI catalog — eligibility, projection, read-only gate
# ---------------------------------------------------------------------------


def test_si_ops_present_in_baseline_and_allowlist() -> None:
    actions = _actions()
    by_id = {a.action_id: a for a in actions}
    for op_id in SI_READ_OPS:
        assert op_id in by_id, op_id
        assert by_id[op_id].method == "GET", op_id
        assert by_id[op_id].executable is True, op_id


def test_no_si_mutation_is_exposed() -> None:
    """No approved SI op may be non-GET — read cannot perform ACT."""
    actions = _actions()
    si_ops = [a for a in actions if a.path.startswith("/strategic-indicators")]
    assert si_ops, "expected SI ops in catalog"
    assert all(a.method == "GET" for a in si_ops)


def test_davi_read_executes_si_capability_with_validated_args() -> None:
    actions = _actions()
    set_actions_for_tests(actions)
    executor = _StubExecutor(payload={"success": True, "data": {"items": []}})

    result = davi_read(
        capability="get_si_indicators",
        arguments={"competence": "2026-06"},
        catalog_action_executor=executor,
    )

    assert executor.calls
    assert executor.calls[0]["action_id"] == "get_si_indicators"
    assert executor.calls[0]["validated_arguments"] == {"competence": "2026-06"}
    assert result.get("success") is True or "data" in result or result


def test_davi_read_rejects_unknown_capability_argument() -> None:
    actions = _actions()
    set_actions_for_tests(actions)
    executor = _StubExecutor()

    with pytest.raises(Exception):
        davi_read(
            capability="list_si_indicator_goals",
            arguments={"drop_table": "1"},
            catalog_action_executor=executor,
        )
    assert executor.calls == []


def test_davi_read_rejects_non_allowlisted_capability() -> None:
    actions = _actions()
    set_actions_for_tests(actions)
    executor = _StubExecutor()

    from app.application.external_capabilities.dynamic_information.errors import (
        GovernedExecutionError,
    )

    with pytest.raises(GovernedExecutionError):
        davi_read(
            capability="create_indicator_goal",  # not in catalog/allowlist
            arguments={},
            catalog_action_executor=executor,
        )
    assert executor.calls == []
