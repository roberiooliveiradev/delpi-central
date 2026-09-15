"""TM-GPI-007 — gpt_get_my_context personal context (not authorization)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from tm_app.application.gpt_actions.errors import GptActionsError
from tm_app.application.gpt_actions.openapi_builder import (
    GPT_ACTIONS_OPERATION_IDS,
    build_gpt_actions_openapi,
    count_operations,
)
from tm_app.application.gpt_actions.user_context_service import UserContextService
from tm_app.infrastructure.gateways.core_person_profile_gateway import (
    CorePersonProfileGateway,
)
from tm_app.interface.http.routes.gpt_actions_routes import router as gpt_router
from tm_app.middleware.auth_middleware import jwt_middleware

_FORBIDDEN_KEYS = frozenset(
    {
        "roles",
        "groups",
        "permissions",
        "is_superadmin",
        "access_scope",
        "scoped_manage",
        "unrestricted",
        "claims",
        "token",
        "user_id",
    }
)


def _request(*, name="Robério", email="roberio@delpi.com.br", perms=None):
    req = MagicMock()
    req.state.user = SimpleNamespace(
        id="11111111-1111-1111-1111-111111111111",
        name=name,
        email=email,
        permissions=perms or ["transformometro.view"],
        roles=["role-x"],
        groups=["group-y"],
        is_superadmin=False,
    )
    req.headers = {"Authorization": "Bearer user-jwt"}
    return req


def test_openapi_includes_gpt_get_my_context():
    doc = build_gpt_actions_openapi()
    assert "gpt_get_my_context" in GPT_ACTIONS_OPERATION_IDS
    assert count_operations(doc) == 20
    op = doc["paths"]["/transformometro/gpt-actions/v1/me"]["get"]
    assert op["operationId"] == "gpt_get_my_context"
    assert op["x-openai-isConsequential"] is False
    assert "parameters" not in op


def test_authenticated_user_gets_display_name_email_job_title():
    svc = UserContextService()
    request = _request()
    with patch.object(svc._profiles, "get_my_person_profile") as fetch:
        fetch.return_value = {"job_title": "Gerente de Processos"}
        data = svc.get_my_context(request)
    assert data["display_name"] == "Robério"
    assert data["email"] == "roberio@delpi.com.br"
    assert data["job_title"] == "Gerente de Processos"
    assert data["profile_complete"] is True
    fetch.assert_called_once_with("Bearer user-jwt")


def test_missing_person_profile_returns_null_job_title_not_invented():
    svc = UserContextService()
    request = _request()
    with patch.object(svc._profiles, "get_my_person_profile") as fetch:
        fetch.return_value = {
            "user_id": "11111111-1111-1111-1111-111111111111",
            "job_title": None,
            "has_photo": False,
        }
        data = svc.get_my_context(request)
    assert data["job_title"] is None
    assert data["profile_complete"] is True


def test_missing_display_name_sets_profile_complete_false():
    svc = UserContextService()
    request = _request(name="roberio@delpi.com.br", email="roberio@delpi.com.br")
    with patch.object(svc._profiles, "get_my_person_profile") as fetch:
        fetch.return_value = {"job_title": None}
        data = svc.get_my_context(request)
    assert data["display_name"] is None
    assert data["profile_complete"] is False


def test_response_excludes_authz_metadata():
    svc = UserContextService()
    request = _request()
    with patch.object(svc._profiles, "get_my_person_profile") as fetch:
        fetch.return_value = {"job_title": "Analista"}
        data = svc.get_my_context(request)
    assert set(data.keys()) == {
        "display_name",
        "email",
        "job_title",
        "profile_complete",
    }
    assert not _FORBIDDEN_KEYS.intersection(data.keys())
    assert "roles" not in str(data)


def test_unauthenticated_service_raises_401():
    svc = UserContextService()
    request = MagicMock()
    request.state.user = None
    with pytest.raises(GptActionsError) as exc:
        svc.get_my_context(request)
    assert exc.value.status_code == 401


def test_gpt_me_route_unauthenticated_returns_401():
    app = FastAPI()
    app.middleware("http")(jwt_middleware)
    app.include_router(gpt_router)
    client = TestClient(app)
    response = client.get("/transformometro/gpt-actions/v1/me")
    assert response.status_code == 401


def test_core_integration_failure_truthful_503():
    gateway = CorePersonProfileGateway()
    with patch("httpx.Client") as client_cls:
        client_cls.return_value.__enter__.return_value.get.side_effect = (
            httpx.ConnectError("down")
        )
        with pytest.raises(GptActionsError) as exc:
            gateway.get_my_person_profile("Bearer x")
    assert exc.value.status_code == 503
    assert exc.value.data.get("error_kind") == "persistence"


def test_no_service_account_token_used():
    gateway = CorePersonProfileGateway()
    with patch("httpx.Client") as client_cls:
        mock_client = client_cls.return_value.__enter__.return_value
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"job_title": "Dev"}
        mock_client.get.return_value = mock_response
        gateway.get_my_person_profile("Bearer end-user-token")
        _args, kwargs = mock_client.get.call_args
        headers = kwargs.get("headers") or {}
        assert headers.get("Authorization") == "Bearer end-user-token"
        assert "X-Delpi-Service-Token" not in headers


def test_existing_nineteen_operation_ids_unchanged():
    before = {
        "gpt_get_catalog",
        "gpt_analyze",
        "gpt_search_records",
        "gpt_get_record",
        "gpt_create_record",
        "gpt_update_record",
        "gpt_delete_record",
        "gpt_duplicate_record",
        "gpt_activate_revision",
        "gpt_recalculate_dashboard",
        "gpt_meeting_minute_workflow",
        "gpt_validate_improvement_package",
        "gpt_commit_improvement_package",
        "gpt_get_process_context",
        "gpt_list_evidence",
        "gpt_manage_evidence",
        "gpt_get_process_timeline",
        "gpt_adjust_shared_resource_cost",
        "gpt_meeting_minute_manage",
    }
    assert before <= set(GPT_ACTIONS_OPERATION_IDS)
    assert len(GPT_ACTIONS_OPERATION_IDS) == 20
