"""TM-GPI-007 / 007A — gpt_get_my_context personal context (not authorization)."""

from __future__ import annotations

import ast
from pathlib import Path
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
from tm_app.application.gpt_actions.user_context_service import (
    AuthenticatedUserContext,
    UserContextService,
)
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

_APP_MODULE = (
    Path(__file__).resolve().parents[1]
    / "tm_app"
    / "application"
    / "gpt_actions"
    / "user_context_service.py"
)


class _FakePersonProfileReader:
    def __init__(self, payload: dict | None = None, *, error: Exception | None = None):
        self.payload = payload or {"job_title": None}
        self.error = error
        self.calls: list[str] = []

    def get_my_person_profile(self, authorization: str) -> dict:
        self.calls.append(authorization)
        if self.error is not None:
            raise self.error
        return self.payload


def _context(
    *,
    display_name: str | None = "Robério",
    email: str | None = "roberio@delpi.com.br",
    authorization: str = "Bearer user-jwt",
) -> AuthenticatedUserContext:
    return AuthenticatedUserContext(
        display_name=display_name,
        email=email,
        authorization=authorization,
    )


def test_application_user_context_has_no_infrastructure_or_framework_imports():
    tree = ast.parse(_APP_MODULE.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    joined = "\n".join(imported)
    assert "tm_app.infrastructure" not in joined
    assert not any(name.startswith("tm_app.infrastructure") for name in imported)
    assert "fastapi" not in imported
    assert "starlette" not in imported
    assert not any(name.startswith("fastapi") or name.startswith("starlette") for name in imported)


def test_openapi_includes_gpt_get_my_context():
    doc = build_gpt_actions_openapi()
    assert "gpt_get_my_context" in GPT_ACTIONS_OPERATION_IDS
    assert count_operations(doc) == len(GPT_ACTIONS_OPERATION_IDS) == 18
    op = doc["paths"]["/transformometro/gpt-actions/v1/me"]["get"]
    assert op["operationId"] == "gpt_get_my_context"
    assert op["x-openai-isConsequential"] is False
    assert "parameters" not in op


def test_authenticated_user_gets_display_name_email_job_title():
    reader = _FakePersonProfileReader({"job_title": "Gerente de Processos"})
    svc = UserContextService(person_profile_reader=reader)
    data = svc.get_my_context(_context())
    assert data["display_name"] == "Robério"
    assert data["email"] == "roberio@delpi.com.br"
    assert data["job_title"] == "Gerente de Processos"
    assert data["profile_complete"] is True
    assert reader.calls == ["Bearer user-jwt"]


def test_missing_person_profile_returns_null_job_title_not_invented():
    reader = _FakePersonProfileReader(
        {
            "user_id": "11111111-1111-1111-1111-111111111111",
            "job_title": None,
            "has_photo": False,
        }
    )
    svc = UserContextService(person_profile_reader=reader)
    data = svc.get_my_context(_context())
    assert data["job_title"] is None
    assert data["profile_complete"] is True


def test_missing_display_name_sets_profile_complete_false():
    reader = _FakePersonProfileReader({"job_title": None})
    svc = UserContextService(person_profile_reader=reader)
    data = svc.get_my_context(_context(display_name=None))
    assert data["display_name"] is None
    assert data["profile_complete"] is False


def test_response_excludes_authz_metadata():
    reader = _FakePersonProfileReader({"job_title": "Analista"})
    svc = UserContextService(person_profile_reader=reader)
    data = svc.get_my_context(_context())
    assert set(data.keys()) == {
        "display_name",
        "email",
        "job_title",
        "profile_complete",
    }
    assert not _FORBIDDEN_KEYS.intersection(data.keys())
    assert "roles" not in str(data)


def test_unauthenticated_service_raises_401():
    reader = _FakePersonProfileReader()
    svc = UserContextService(person_profile_reader=reader)
    with pytest.raises(GptActionsError) as exc:
        svc.get_my_context(_context(authorization=""))
    assert exc.value.status_code == 401
    assert reader.calls == []


def test_gpt_me_route_unauthenticated_returns_401():
    app = FastAPI()
    app.middleware("http")(jwt_middleware)
    app.include_router(gpt_router)
    client = TestClient(app)
    response = client.get("/transformometro/gpt-actions/v1/me")
    assert response.status_code == 401


def test_gpt_me_route_injects_authenticated_context(tm_client):
    from tests.support import test_app as support

    prev_name = getattr(support.TEST_USER, "name", None)
    prev_email = getattr(support.TEST_USER, "email", None)
    support.TEST_USER.name = "Robério Oliveira"
    support.TEST_USER.email = "roberio@delpi.com.br"
    try:
        with patch(
            "tm_app.interface.http.routes.gpt_actions_routes._user_context.get_my_context"
        ) as get_ctx:
            get_ctx.return_value = {
                "display_name": "Robério Oliveira",
                "email": "roberio@delpi.com.br",
                "job_title": None,
                "profile_complete": True,
            }
            response = tm_client.get(
                "/transformometro/gpt-actions/v1/me",
                headers={"Authorization": "Bearer user-jwt"},
            )
        assert response.status_code == 200
        body = get_ctx.call_args[0][0]
        assert isinstance(body, AuthenticatedUserContext)
        assert body.display_name == "Robério Oliveira"
        assert body.email == "roberio@delpi.com.br"
        assert body.authorization.startswith("Bearer ")
        payload = response.json()["data"]
        assert payload["job_title"] is None
        assert not _FORBIDDEN_KEYS.intersection(payload.keys())
    finally:
        support.TEST_USER.name = prev_name
        support.TEST_USER.email = prev_email


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


def test_existing_operation_ids_preserved_and_methodology_added():
    current_core = {
        "gpt_get_catalog",
        "gpt_analyze",
        "gpt_search_records",
        "gpt_get_record",
        "gpt_prepare_record_change",
        "gpt_commit_proposal",
        "gpt_activate_revision",
        "gpt_recalculate_dashboard",
        "gpt_meeting_minute_workflow",
        "gpt_validate_improvement_package",
        "gpt_get_process_context",
        "gpt_list_evidence",
        "gpt_manage_evidence",
        "gpt_get_process_timeline",
        "gpt_adjust_shared_resource_cost",
        "gpt_meeting_minute_manage",
        "gpt_get_my_context",
        "gpt_get_methodology_guide",
    }
    assert current_core == set(GPT_ACTIONS_OPERATION_IDS)
    assert len(GPT_ACTIONS_OPERATION_IDS) == 18
