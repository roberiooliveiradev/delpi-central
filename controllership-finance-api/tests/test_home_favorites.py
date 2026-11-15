"""Favoritos do hub Início — normalize + rotas GET/PUT /me/home-favorites."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import delpi_auth.middleware.fastapi_auth as fa
from controllership_finance_app.infrastructure.persistence.home_favorites_repository import (
    normalize_favorite_items,
)
from controllership_finance_app.main import app

ACCESS = "controllership-finance.access"
MANAGE = "controllership-finance.manage"
ACCESS_DRE = "controllership-finance.access.dre"
TOKEN = "home-favorites-test-token"


def _claims(**overrides) -> dict:
    claims = {
        "sub": "user-fav-1",
        "email": "ana@delpi.com.br",
        "name": "Ana Souza",
        "given_name": "Ana",
    }
    claims.update(overrides)
    return claims


def _rbac(**overrides) -> dict:
    rbac = {
        "id": "user-fav-1",
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
    monkeypatch.setattr(fa, "request_has_valid_internal_service_token", lambda request: False)
    monkeypatch.setattr(fa, "validate_token", lambda token: _claims())
    monkeypatch.setattr(
        fa,
        "load_user_rbac",
        lambda token, *, force_refresh=False: _load_rbac_result(rbac_holder["rbac"]),
    )
    yield rbac_holder


@pytest.fixture
def repo_store(monkeypatch):
    store: dict[str, list] = {}

    class FakeRepo:
        def get_items(self, *, user_id: str):
            return list(store.get(user_id, []))

        def put_items(self, *, user_id: str, items: list):
            cleaned = normalize_favorite_items(items)
            store[user_id] = cleaned
            return cleaned

    monkeypatch.setattr(
        "controllership_finance_app.interface.http.routes.home_favorites_routes._repo",
        lambda: FakeRepo(),
    )
    return store


def _client() -> TestClient:
    return TestClient(app)


def _headers(token: str = TOKEN) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_normalize_accepts_valid_items():
    items = normalize_favorite_items(
        [
            {"viewId": "entry_audit"},
            {"viewId": "monthly_closing", "search": "tab=documents"},
        ]
    )
    assert items == [
        {"viewId": "entry_audit"},
        {"viewId": "monthly_closing", "search": "?tab=documents"},
    ]


def test_normalize_rejects_unknown_view():
    with pytest.raises(ValueError, match="invalid viewId"):
        normalize_favorite_items([{"viewId": "home"}])


def test_normalize_rejects_external_lnf():
    with pytest.raises(ValueError, match="invalid viewId"):
        normalize_favorite_items([{"viewId": "lancamento_notas_fiscais"}])


def test_normalize_dedupes_and_caps():
    items = normalize_favorite_items(
        [{"viewId": "entry_audit"}, {"viewId": "entry_audit"}]
    )
    assert len(items) == 1
    with pytest.raises(ValueError, match="exceeds max"):
        normalize_favorite_items([{"viewId": "entry_audit"}] * 21)


def test_get_requires_auth():
    assert _client().get("/me/home-favorites").status_code == 401


def test_get_forbidden_without_access(_auth_pipeline, repo_store):
    _auth_pipeline["rbac"] = _rbac(permissions=[MANAGE])
    assert _client().get("/me/home-favorites", headers=_headers()).status_code == 403


def test_get_empty_for_access_user(_auth_pipeline, repo_store):
    response = _client().get("/me/home-favorites", headers=_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["items"] == []
    assert body["meta"]["operationId"] == "get_home_favorites"


def test_get_allows_dre_viewer(_auth_pipeline, repo_store):
    _auth_pipeline["rbac"] = _rbac(permissions=[ACCESS_DRE])
    response = _client().get("/me/home-favorites", headers=_headers())
    assert response.status_code == 200
    assert response.json()["data"]["items"] == []


def test_put_persists_and_get_returns(_auth_pipeline, repo_store):
    put = _client().put(
        "/me/home-favorites",
        headers=_headers(),
        json={"items": [{"viewId": "entry_audit"}, {"viewId": "monthly_closing", "search": "?tab=reports"}]},
    )
    assert put.status_code == 200
    assert put.json()["data"]["items"] == [
        {"viewId": "entry_audit"},
        {"viewId": "monthly_closing", "search": "?tab=reports"},
    ]
    got = _client().get("/me/home-favorites", headers=_headers())
    assert got.status_code == 200
    assert got.json()["data"]["items"] == put.json()["data"]["items"]


def test_put_invalid_view_returns_422(_auth_pipeline, repo_store):
    response = _client().put(
        "/me/home-favorites",
        headers=_headers(),
        json={"items": [{"viewId": "profile"}]},
    )
    assert response.status_code == 422


def test_favorites_isolated_by_user(monkeypatch, _auth_pipeline, repo_store):
    put_a = _client().put(
        "/me/home-favorites",
        headers=_headers(),
        json={"items": [{"viewId": "entry_audit"}]},
    )
    assert put_a.status_code == 200

    monkeypatch.setattr(fa, "validate_token", lambda token: _claims(sub="user-fav-2"))
    _auth_pipeline["rbac"] = _rbac(id="user-fav-2", permissions=[ACCESS])
    got_b = _client().get("/me/home-favorites", headers=_headers("other-token"))
    assert got_b.status_code == 200
    assert got_b.json()["data"]["items"] == []

    put_b = _client().put(
        "/me/home-favorites",
        headers=_headers("other-token"),
        json={"items": [{"viewId": "received_documents"}]},
    )
    assert put_b.status_code == 200

    monkeypatch.setattr(fa, "validate_token", lambda token: _claims(sub="user-fav-1"))
    _auth_pipeline["rbac"] = _rbac(id="user-fav-1", permissions=[ACCESS])
    got_a = _client().get("/me/home-favorites", headers=_headers())
    assert got_a.json()["data"]["items"] == [{"viewId": "entry_audit"}]
