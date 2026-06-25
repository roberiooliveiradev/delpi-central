"""Smoke HTTP — rotas PAC Onda 1 (meta operationId e contrato básico)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


def _body(response) -> dict:
    return json.loads(response.body.decode())


@patch(
    "app.interface.http.routes.quality.action_plans_read_router.build_quality_action_plan_read_repository"
)
def test_dashboard_route_returns_operation_id(mock_build) -> None:
    from app.interface.http.routes.quality.action_plans_read_router import (
        get_action_plans_dashboard,
    )

    mock_repo = MagicMock()
    mock_repo.get_dashboard_summary.return_value = {
        "open_plans": 2,
        "critical_open": 1,
        "waiting_validation": 0,
        "completed_this_month": 0,
        "overdue_actions": 0,
        "overdue_plans": 0,
        "open_internal": 0,
        "open_external": 2,
        "by_branch": [],
        "by_scope": [],
    }
    mock_build.return_value = mock_repo

    response = get_action_plans_dashboard()
    body = _body(response)

    assert body.get("success") is True
    assert body.get("meta", {}).get("operationId") == "get_quality_action_plans_dashboard"
    assert body.get("data", {}).get("open_plans") == 2


@patch(
    "app.interface.http.routes.quality.action_plans_read_router.build_create_quality_action_plan_use_case"
)
@patch("app.interface.http.routes.quality.action_plans_read_router.get_current_user")
def test_create_plan_route_returns_operation_id(mock_user, mock_build) -> None:
    from app.interface.http.routes.quality.action_plans_read_router import (
        CreateActionPlanBody,
        create_action_plan,
    )

    mock_user.return_value = MagicMock(id="user-smoke")
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = {
        "id": "plan-smoke-id",
        "code": "PAC-2026-SMOKE",
        "status": "triage",
    }
    mock_build.return_value = mock_use_case

    response = create_action_plan(
        CreateActionPlanBody(
            title="Plano smoke rota",
            branch_code="01",
            nonconformity_scope="external",
            severity="critical",
        )
    )
    body = _body(response)

    assert body.get("success") is True
    assert body.get("meta", {}).get("operationId") == "create_quality_action_plan"
    assert body.get("data", {}).get("code") == "PAC-2026-SMOKE"


@patch(
    "app.interface.http.routes.quality.action_plans_read_router.build_quality_action_plan_read_repository"
)
def test_list_evidences_route_returns_operation_id(mock_build) -> None:
    from app.interface.http.routes.quality.action_plans_read_router import list_plan_evidences

    mock_repo = MagicMock()
    mock_repo.get_plan_by_id.return_value = {"id": "plan-1"}
    mock_repo.list_evidences.return_value = [
        {"id": "ev-1", "evidence_type": "image", "action_id": "act-1"},
    ]
    mock_build.return_value = mock_repo

    response = list_plan_evidences("plan-1")
    body = _body(response)

    assert body.get("success") is True
    assert body.get("meta", {}).get("operationId") == "list_quality_action_plan_evidences"
    assert len(body.get("data", [])) == 1


@pytest.fixture
def pac_client() -> TestClient:
    from fastapi import FastAPI

    from app.interface.http.routes.quality.action_plans_read_router import router

    app = FastAPI()
    app.include_router(router, prefix="/quality")
    return TestClient(app)


def test_create_plan_requires_branch_code(pac_client: TestClient) -> None:
    response = pac_client.post(
        "/quality/action-plans",
        json={"title": "Sem filial", "nonconformity_scope": "external"},
    )
    assert response.status_code == 422


def test_evidence_upload_rejects_invalid_section(pac_client: TestClient) -> None:
    response = pac_client.post(
        "/quality/action-plans/plan-1/evidences",
        data={"evidence_type": "image", "section": "invalid_section"},
        files={"file": ("x.png", b"not-a-png", "image/png")},
    )
    assert response.status_code == 422
