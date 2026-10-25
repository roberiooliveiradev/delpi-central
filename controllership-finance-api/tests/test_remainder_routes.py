"""Remainder build — authz + domain-error mapping dos novos endpoints.

- ``/me/tasks`` e ``/me/profile``: self-only, `access` efetivo,
  service principal recusado, rbac indisponível → 503;
- ``/admin/closing-catalogs`` e lifecycle REVIEW de checklist:
  `manage` efetivo — `access` isolado nunca administra.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import delpi_auth.middleware.fastapi_auth as fa
from controllership_finance_app.domain.closing_checklist import errors as de
from controllership_finance_app.main import app

ACCESS = "controllership-finance.access"
MANAGE = "controllership-finance.manage"
TOKEN = "viewer-test-token"
TEMPLATE_ID = "11111111-1111-4111-8111-111111111111"


def _claims(**overrides) -> dict:
    claims = {
        "sub": "33333333-3333-4333-8333-333333333333",
        "email": "ana@delpi.com.br",
        "name": "Ana Souza",
        "given_name": "Ana",
    }
    claims.update(overrides)
    return claims


def _rbac(**overrides) -> dict:
    rbac = {
        "id": "33333333-3333-4333-8333-333333333333",
        "email": "ana@delpi.com.br",
        "name": "Ana Souza",
        "roles": [],
        "groups": [],
        "permissions": [ACCESS, MANAGE],
        "is_superadmin": False,
    }
    rbac.update(overrides)
    return rbac


async def _load_rbac_result(rbac: dict):
    return rbac


@pytest.fixture(autouse=True)
def _auth_pipeline(monkeypatch):
    rbac_holder = {"rbac": _rbac()}
    monkeypatch.setattr(
        fa,
        "request_has_valid_internal_service_token",
        lambda request: False,
    )
    monkeypatch.setattr(
        fa, "validate_token", lambda token: _claims()
    )
    monkeypatch.setattr(
        fa,
        "load_user_rbac",
        lambda token, *, force_refresh=False: _load_rbac_result(
            rbac_holder["rbac"]
        ),
    )
    yield rbac_holder


@pytest.fixture
def tasks_repo(monkeypatch):
    fake = MagicMock()
    monkeypatch.setattr(
        "controllership_finance_app.interface.http.routes."
        "me_routes.ClosingTasksRepository",
        lambda: fake,
    )
    return fake


@pytest.fixture
def catalog_repo(monkeypatch):
    fake = MagicMock()
    monkeypatch.setattr(
        "controllership_finance_app.interface.http.routes."
        "admin_catalogs_routes._repository",
        lambda: fake,
    )
    return fake


@pytest.fixture
def package_repo(monkeypatch):
    fake = MagicMock()
    monkeypatch.setattr(
        "controllership_finance_app.interface.http.routes."
        "packages_routes._repository",
        lambda: fake,
    )
    return fake


@pytest.fixture
def checklist_repo(monkeypatch):
    fake = MagicMock()
    monkeypatch.setattr(
        "controllership_finance_app.interface.http.routes."
        "admin_checklist_routes._repository",
        lambda: fake,
    )
    return fake


def _client() -> TestClient:
    return TestClient(app)


def _headers(token: str = TOKEN) -> dict:
    return {"Authorization": f"Bearer {token}"}


# -- /me/tasks ----------------------------------------------------------------


def test_my_tasks_requires_bearer(tasks_repo):
    assert _client().get("/me/tasks").status_code == 401
    tasks_repo.list_my_tasks.assert_not_called()


def test_my_tasks_access_only_ok(_auth_pipeline, tasks_repo):
    _auth_pipeline["rbac"] = _rbac(permissions=[ACCESS])
    tasks_repo.list_my_tasks.return_value = {
        "items": [],
        "total": 0,
        "selfOnly": True,
    }
    response = _client().get("/me/tasks", headers=_headers())
    assert response.status_code == 200
    tasks_repo.list_my_tasks.assert_called_once()
    kwargs = tasks_repo.list_my_tasks.call_args.kwargs
    assert kwargs["subject"] == "33333333-3333-4333-8333-333333333333"


def test_my_tasks_no_access_forbidden(_auth_pipeline, tasks_repo):
    _auth_pipeline["rbac"] = _rbac(permissions=[])
    response = _client().get("/me/tasks", headers=_headers())
    assert response.status_code == 403
    tasks_repo.list_my_tasks.assert_not_called()


# -- /me/profile ---------------------------------------------------------------


def test_my_profile_requires_bearer():
    assert _client().get("/me/profile").status_code == 401


def test_my_profile_returns_own_data(_auth_pipeline):
    _auth_pipeline["rbac"] = _rbac(
        permissions=[ACCESS], groups=["controladoria"]
    )
    response = _client().get("/me/profile", headers=_headers())
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["id"] == "33333333-3333-4333-8333-333333333333"
    assert body["groups"] == ["controladoria"]
    assert ACCESS in body["permissions"]


# -- /admin/closing-catalogs ----------------------------------------------------


def test_catalogs_requires_bearer(catalog_repo):
    assert _client().get("/admin/closing-catalogs").status_code == 401
    catalog_repo.list_entries.assert_not_called()


def test_catalogs_access_only_forbidden(_auth_pipeline, catalog_repo):
    _auth_pipeline["rbac"] = _rbac(permissions=[ACCESS])
    response = _client().get(
        "/admin/closing-catalogs", headers=_headers()
    )
    assert response.status_code == 403
    catalog_repo.list_entries.assert_not_called()


def test_catalogs_list_with_manage(_auth_pipeline, catalog_repo):
    catalog_repo.list_entries.return_value = [
        {"catalog_key": "BANK_ACCOUNT", "active": True},
        {"catalog_key": "BANK_ACCOUNT", "active": False},
    ]
    response = _client().get(
        "/admin/closing-catalogs", headers=_headers()
    )
    assert response.status_code == 200
    catalogs = {
        c["catalog_key"]: c
        for c in response.json()["data"]["catalogs"]
    }
    assert catalogs["BANK_ACCOUNT"]["active"] == 1
    assert catalogs["BANK_ACCOUNT"]["inactive"] == 1


def test_catalog_create_and_domain_error(_auth_pipeline, catalog_repo):
    catalog_repo.create_entry.return_value = {
        "entry_id": "e1",
        "catalog_key": "BANK_ACCOUNT",
        "code": "BB-001",
    }
    response = _client().post(
        "/admin/closing-catalogs/bank_account/entries",
        headers=_headers(),
        json={"code": "BB-001", "label": "Conta BB"},
    )
    assert response.status_code == 200
    assert catalog_repo.create_entry.call_args.args[0] == "BANK_ACCOUNT"

    catalog_repo.create_entry.side_effect = de.InvalidCatalogEntry(
        "duplicado"
    )
    response = _client().post(
        "/admin/closing-catalogs/BANK_ACCOUNT/entries",
        headers=_headers(),
        json={"code": "BB-001", "label": "Conta BB"},
    )
    assert response.status_code == 400

    catalog_repo.deactivate_entry.side_effect = de.StaleRevision(
        "revisão"
    )
    response = _client().post(
        "/admin/closing-catalogs/BANK_ACCOUNT/entries/BB-001/deactivate",
        headers=_headers(),
        json={"revision": 1},
    )
    assert response.status_code == 409


# -- lifecycle REVIEW ------------------------------------------------------------


def test_submit_review_requires_manage(_auth_pipeline, checklist_repo):
    _auth_pipeline["rbac"] = _rbac(permissions=[ACCESS])
    response = _client().post(
        f"/admin/checklist-templates/{TEMPLATE_ID}/versions/1/"
        "submit-review",
        headers=_headers(),
    )
    assert response.status_code == 403
    checklist_repo.submit_version_for_review.assert_not_called()


def test_submit_review_and_return_to_draft(
    _auth_pipeline, checklist_repo
):
    checklist_repo.submit_version_for_review.return_value = {
        "version_id": "v",
        "status": "REVIEW",
    }
    response = _client().post(
        f"/admin/checklist-templates/{TEMPLATE_ID}/versions/1/"
        "submit-review",
        headers=_headers(),
    )
    assert response.status_code == 200

    checklist_repo.return_version_to_draft.return_value = {
        "version_id": "v",
        "status": "DRAFT",
    }
    response = _client().post(
        f"/admin/checklist-templates/{TEMPLATE_ID}/versions/1/"
        "return-to-draft",
        headers=_headers(),
        json={"reason": "revisar itens"},
    )
    assert response.status_code == 200
    assert (
        checklist_repo.return_version_to_draft.call_args.kwargs["reason"]
        == "revisar itens"
    )

    checklist_repo.return_version_to_draft.side_effect = (
        de.VersionNotInReview("não está em revisão")
    )
    response = _client().post(
        f"/admin/checklist-templates/{TEMPLATE_ID}/versions/1/"
        "return-to-draft",
        headers=_headers(),
        json={"reason": "revisar itens"},
    )
    assert response.status_code == 409


# -- R-105-01: erro tipado quando rejeicao terminal congela revisao -----


def test_decision_blocked_when_terminal_rejection_active(
    _auth_pipeline, package_repo
):
    _auth_pipeline["rbac"] = _rbac(permissions=[ACCESS])
    package_repo.record_decision.side_effect = (
        de.TerminalRejectionActive(
            "Competência com rejeição terminal ativa."
        )
    )
    response = _client().post(
        "/closing/competences/2026-05/package-versions/"
        "22222222-2222-4222-8222-222222222222/decisions",
        headers=_headers(),
        json={"area": "FISCAL", "outcome": "ACCEPTED"},
    )
    assert response.status_code == 409
    body = response.json()
    assert body["success"] is False
    assert (
        body["data"]["error"]["code"] == "terminal_rejection_active"
    )
    assert (
        body["meta"]["operationId"] == "record_review_decision"
    )


def test_clarification_blocked_when_terminal_rejection_active(
    _auth_pipeline, package_repo
):
    _auth_pipeline["rbac"] = _rbac(permissions=[ACCESS])
    package_repo.open_clarification.side_effect = (
        de.TerminalRejectionActive(
            "Competência com rejeição terminal ativa."
        )
    )
    response = _client().post(
        "/closing/competences/2026-05/package-versions/"
        "22222222-2222-4222-8222-222222222222/clarifications",
        headers=_headers(),
        json={"question": "falta extrato?"},
    )
    assert response.status_code == 409
    assert (
        response.json()["data"]["error"]["code"]
        == "terminal_rejection_active"
    )


# -- R-105-02: envelope /me tipado, sem excecao secundaria -------------


def test_my_tasks_domain_error_typed(_auth_pipeline, tasks_repo):
    _auth_pipeline["rbac"] = _rbac(permissions=[ACCESS])
    tasks_repo.list_my_tasks.side_effect = de.CompetenceNotOpened(
        "Competência não aberta."
    )
    response = _client().get("/me/tasks", headers=_headers())
    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["data"]["error"]["code"] == "competence_not_opened"
    assert body["meta"]["operationId"] == "list_my_tasks"


def test_my_tasks_persistence_unavailable(_auth_pipeline, tasks_repo):
    _auth_pipeline["rbac"] = _rbac(permissions=[ACCESS])
    tasks_repo.list_my_tasks.side_effect = de.PersistenceUnavailable(
        "Persistência indisponível."
    )
    response = _client().get("/me/tasks", headers=_headers())
    assert response.status_code == 503
    body = response.json()
    assert body["data"]["error"]["code"] == "persistence_unavailable"


def test_my_tasks_rbac_unavailable_503(
    _auth_pipeline, tasks_repo, monkeypatch
):
    async def _failing_rbac(token, *, force_refresh=False):
        raise RuntimeError("core down")

    monkeypatch.setattr(fa, "load_user_rbac", _failing_rbac)
    response = _client().get("/me/tasks", headers=_headers())
    assert response.status_code == 503
    tasks_repo.list_my_tasks.assert_not_called()
