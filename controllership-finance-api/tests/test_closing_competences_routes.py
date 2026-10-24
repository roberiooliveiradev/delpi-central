"""P2-READ competences API — authorization + contract tests.

``access`` efetivo autoriza abertura/leitura; ``manage`` isolado não
implica ``access``; sem versão PUBLISHED vigente a abertura falha com
``no_published_template`` (409) — nunca fallback silencioso.
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


def _claims(**overrides) -> dict:
    claims = {
        "sub": "user-1",
        "email": "ana@delpi.com.br",
        "name": "Ana Souza",
    }
    claims.update(overrides)
    return claims


def _rbac(**overrides) -> dict:
    rbac = {
        "id": "user-1",
        "email": "ana@delpi.com.br",
        "name": "Ana Souza",
        "roles": [],
        "groups": [],
        "permissions": [ACCESS],
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
        fa, "request_has_valid_internal_service_token", lambda request: False
    )
    monkeypatch.setattr(fa, "validate_token", lambda token: _claims())
    monkeypatch.setattr(
        fa,
        "load_user_rbac",
        lambda token, *, force_refresh=False: _load_rbac_result(
            rbac_holder["rbac"]
        ),
    )
    yield rbac_holder


@pytest.fixture
def repo(monkeypatch):
    fake = MagicMock()
    monkeypatch.setattr(
        "controllership_finance_app.interface.http.routes."
        "competences_routes._repository",
        lambda: fake,
    )
    return fake


def _client() -> TestClient:
    return TestClient(app)


def _headers(token: str = TOKEN) -> dict:
    return {"Authorization": f"Bearer {token}"}


# --- authorization ----------------------------------------------------------


def test_requires_bearer(repo):
    assert _client().get("/closing/competences").status_code == 401


def test_manage_only_is_forbidden(_auth_pipeline, repo):
    _auth_pipeline["rbac"] = _rbac(permissions=[MANAGE])
    response = _client().get("/closing/competences", headers=_headers())
    assert response.status_code == 403
    repo.list_competences.assert_not_called()


def test_service_principal_denied(monkeypatch, repo):
    monkeypatch.setattr(
        fa, "request_has_valid_internal_service_token", lambda request: True
    )
    response = _client().post(
        "/closing/competences",
        headers=_headers(),
        json={"period": "2026-10"},
    )
    assert response.status_code == 403
    repo.open_competence.assert_not_called()


def test_rbac_unavailable_fails_closed(_auth_pipeline, repo):
    _auth_pipeline["rbac"] = _rbac(rbac_unavailable=True)
    response = _client().get("/closing/competences", headers=_headers())
    assert response.status_code == 503
    repo.list_competences.assert_not_called()


# --- open competence --------------------------------------------------------


def test_open_competence_created(_auth_pipeline, repo):
    repo.open_competence.return_value = (
        {"competence_id": "c", "period": "2026-10", "status": "OPEN"},
        True,
    )
    response = _client().post(
        "/closing/competences",
        headers=_headers(),
        json={"period": "2026-10"},
    )
    assert response.status_code == 201
    assert response.json()["data"]["period"] == "2026-10"


def test_open_competence_replay_idempotent(_auth_pipeline, repo):
    repo.open_competence.return_value = (
        {"competence_id": "c", "period": "2026-10", "status": "OPEN"},
        False,
    )
    response = _client().post(
        "/closing/competences",
        headers=_headers(),
        json={"period": "2026-10"},
    )
    assert response.status_code == 200
    assert "já existente" in response.json()["message"]


def test_open_without_published_template(_auth_pipeline, repo):
    repo.open_competence.side_effect = de.NoPublishedTemplate(
        "sem template publicado"
    )
    response = _client().post(
        "/closing/competences",
        headers=_headers(),
        json={"period": "2026-10"},
    )
    assert response.status_code == 409
    assert (
        response.json()["data"]["error"]["code"] == "no_published_template"
    )


def test_open_invalid_period_422(_auth_pipeline, repo):
    response = _client().post(
        "/closing/competences",
        headers=_headers(),
        json={"period": "10/2026"},
    )
    assert response.status_code == 422
    repo.open_competence.assert_not_called()


# --- reads ------------------------------------------------------------------


def test_list_competences(_auth_pipeline, repo):
    repo.list_competences.return_value = [
        {"period": "2026-10", "item_count": 53}
    ]
    response = _client().get("/closing/competences", headers=_headers())
    assert response.status_code == 200
    assert response.json()["data"]["competences"][0]["item_count"] == 53


def test_get_competence_not_opened(_auth_pipeline, repo):
    repo.get_competence.side_effect = de.CompetenceNotOpened("não aberta")
    response = _client().get(
        "/closing/competences/2026-10", headers=_headers()
    )
    assert response.status_code == 404
    assert (
        response.json()["data"]["error"]["code"] == "competence_not_opened"
    )


def test_get_competence_invalid_period(_auth_pipeline, repo):
    response = _client().get(
        "/closing/competences/2026-13", headers=_headers()
    )
    assert response.status_code == 422


def test_list_items(_auth_pipeline, repo):
    repo.list_competence_items.return_value = [
        {"item_key": "CK-E-01", "state": "EXPECTED"}
    ]
    response = _client().get(
        "/closing/competences/2026-10/items", headers=_headers()
    )
    assert response.status_code == 200
    assert response.json()["data"]["items"][0]["state"] == "EXPECTED"


def test_list_items_filters(_auth_pipeline, repo):
    repo.list_competence_items.return_value = []
    response = _client().get(
        "/closing/competences/2026-10/items?sheet=FISICO&state=EXPECTED",
        headers=_headers(),
    )
    assert response.status_code == 200
    kwargs = repo.list_competence_items.call_args.kwargs
    assert kwargs["sheet"] == "FISICO"
    assert kwargs["state"] == "EXPECTED"


def test_get_item(_auth_pipeline, repo):
    repo.get_competence_item.return_value = {"item_key": "CK-E-27"}
    response = _client().get(
        "/closing/competences/2026-10/items/CK-E-27", headers=_headers()
    )
    assert response.status_code == 200
    assert response.json()["data"]["item_key"] == "CK-E-27"


def test_get_item_not_found(_auth_pipeline, repo):
    repo.get_competence_item.side_effect = de.ItemNotFound("x")
    response = _client().get(
        "/closing/competences/2026-10/items/CK-E-99", headers=_headers()
    )
    assert response.status_code == 404
    assert response.json()["data"]["error"]["code"] == "item_not_found"
