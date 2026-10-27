"""UX-009 — contratos HTTP `/closing/participants*` (Plano 113 §23.3).

Lookup resolve nome oficial (diretório Core, bearer do caller) + flag
de foto (person-profile S2S); avatar é proxy read-through. Sem foto ou
perfil indisponível → 404/503 honestos, nunca imagem inventada; id fora
do diretório → `display_name = None`. `access` efetivo é obrigatório.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import delpi_auth.middleware.fastapi_auth as fa
from controllership_finance_app.main import app

ACCESS = "controllership-finance.access"
USER_A = "11111111-2222-3333-4444-555555555555"
USER_B = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def _claims() -> dict:
    return {
        "sub": "33333333-3333-4333-8333-333333333333",
        "email": "ana@delpi.com.br",
        "name": "Ana Souza",
    }


def _rbac(**overrides) -> dict:
    rbac = {
        "id": "33333333-3333-4333-8333-333333333333",
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
def gateway(monkeypatch):
    fake = MagicMock()
    monkeypatch.setattr(
        "controllership_finance_app.interface.http.routes."
        "participants_routes._gateway",
        lambda: fake,
    )
    return fake


def _client() -> TestClient:
    return TestClient(app)


def test_lookup_merges_names_and_photo_flags(gateway):
    gateway.lookup_directory_names.return_value = {USER_A: "Robério Oliveira"}
    gateway.lookup_has_photo.return_value = {USER_A: True, USER_B: False}

    response = _client().post(
        "/closing/participants/lookup",
        json={"ids": [USER_A, USER_B]},
        headers={"Authorization": "Bearer t"},
    )

    assert response.status_code == 200
    items = {i["user_id"]: i for i in response.json()["data"]["items"]}
    assert items[USER_A] == {
        "user_id": USER_A,
        "display_name": "Robério Oliveira",
        "has_photo": True,
    }
    assert items[USER_B]["display_name"] is None
    assert items[USER_B]["has_photo"] is False


def test_lookup_filters_invalid_ids(gateway):
    gateway.lookup_directory_names.return_value = {}
    gateway.lookup_has_photo.return_value = {}

    response = _client().post(
        "/closing/participants/lookup",
        json={"ids": ["not-a-uuid", USER_A]},
        headers={"Authorization": "Bearer t"},
    )

    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert items == [
        {"user_id": USER_A, "display_name": None, "has_photo": False}
    ]


def test_lookup_over_50_ids_rejected_422(gateway):
    response = _client().post(
        "/closing/participants/lookup",
        json={"ids": [USER_A] * 51},
        headers={"Authorization": "Bearer t"},
    )

    assert response.status_code == 422
    gateway.lookup_directory_names.assert_not_called()


def test_lookup_without_access_forbidden(_auth_pipeline, gateway):
    _auth_pipeline["rbac"] = _rbac(permissions=[])

    response = _client().post(
        "/closing/participants/lookup",
        json={"ids": [USER_A]},
        headers={"Authorization": "Bearer t"},
    )

    assert response.status_code == 403
    gateway.lookup_directory_names.assert_not_called()


def test_lookup_empty_ids(gateway):
    response = _client().post(
        "/closing/participants/lookup",
        json={"ids": []},
        headers={"Authorization": "Bearer t"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["items"] == []


def test_avatar_streams_photo(gateway):
    gateway.configured.return_value = True
    gateway.get_photo.return_value = (b"\x89PNGdata", "image/png", "a.png")

    response = _client().get(
        f"/closing/participants/{USER_A}/avatar",
        headers={"Authorization": "Bearer t"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content == b"\x89PNGdata"
    assert response.headers["x-content-type-options"] == "nosniff"


def test_avatar_invalid_user_id_422(gateway):
    response = _client().get(
        "/closing/participants/not-a-uuid/avatar",
        headers={"Authorization": "Bearer t"},
    )

    assert response.status_code == 422
    gateway.get_photo.assert_not_called()


def test_avatar_missing_photo_404(gateway):
    gateway.configured.return_value = True
    gateway.get_photo.return_value = None

    response = _client().get(
        f"/closing/participants/{USER_A}/avatar",
        headers={"Authorization": "Bearer t"},
    )

    assert response.status_code == 404


def test_avatar_gateway_not_configured_503(gateway):
    gateway.configured.return_value = False

    response = _client().get(
        f"/closing/participants/{USER_A}/avatar",
        headers={"Authorization": "Bearer t"},
    )

    assert response.status_code == 503
    gateway.get_photo.assert_not_called()


def test_avatar_without_access_forbidden(_auth_pipeline, gateway):
    _auth_pipeline["rbac"] = _rbac(permissions=[])

    response = _client().get(
        f"/closing/participants/{USER_A}/avatar",
        headers={"Authorization": "Bearer t"},
    )

    assert response.status_code == 403
    gateway.get_photo.assert_not_called()
