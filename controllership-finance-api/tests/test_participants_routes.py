"""UX-009-RW01 — contratos HTTP `…/documents/{id}/participants*`
(Plano 113 §23.6).

Isolamento documental: `access` efetivo + documento da competência +
resource scope + **vínculo canônico do participante** (autor U9, ator
U8 ou uploader) precedem qualquer consulta ao Core. Participante fora
do documento recebe o mesmo 404 de recurso inexistente — não há
enumeração de pessoas pela superfície documental.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import delpi_auth.middleware.fastapi_auth as fa
from controllership_finance_app.domain.closing_checklist import errors as de
from controllership_finance_app.main import app

ACCESS = "controllership-finance.access"
PERIOD = "2026-05"
DOC_ID = "99999999-aaaa-bbbb-cccc-dddddddddddd"
USER_A = "11111111-2222-3333-4444-555555555555"
USER_B = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
OUTSIDER = "77777777-8888-9999-aaaa-bbbbbbbbbbbb"


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


@pytest.fixture
def service(monkeypatch):
    """Service documental — vínculo canônico padrão: USER_A e USER_B
    participam do documento; OUTSIDER não."""
    fake = MagicMock()
    fake.document_participant_ids.return_value = {USER_A, USER_B}
    monkeypatch.setattr(
        "controllership_finance_app.interface.http.routes."
        "participants_routes._service",
        lambda: fake,
    )
    return fake


def _client() -> TestClient:
    return TestClient(app)


def _lookup(ids: list[str], **kw) -> TestClient:
    return _client().post(
        f"/closing/competences/{PERIOD}/documents/{DOC_ID}"
        "/participants/lookup",
        json={"ids": ids},
        headers={"Authorization": "Bearer t"},
        **kw,
    )


def _avatar(user_id: str, **kw) -> TestClient:
    return _client().get(
        f"/closing/competences/{PERIOD}/documents/{DOC_ID}"
        f"/participants/{user_id}/avatar",
        headers={"Authorization": "Bearer t"},
        **kw,
    )


# -- positivos ---------------------------------------------------------------

def test_lookup_resolves_only_bound_participants(gateway, service):
    gateway.lookup_directory_names.return_value = {
        USER_A: "Robério Oliveira",
        USER_B: "Ana Souza",
    }
    gateway.lookup_has_photo.return_value = {USER_A: True, USER_B: False}

    response = _lookup([USER_A, USER_B])

    assert response.status_code == 200
    items = {i["user_id"]: i for i in response.json()["data"]["items"]}
    assert items[USER_A]["display_name"] == "Robério Oliveira"
    assert items[USER_A]["has_photo"] is True
    assert items[USER_B]["display_name"] == "Ana Souza"
    service.document_participant_ids.assert_called_once_with(
        period=PERIOD,
        document_id=DOC_ID,
        branch_scope=None,
    )


def test_lookup_passes_caller_bearer_to_directory(gateway, service):
    gateway.lookup_directory_names.return_value = {}
    gateway.lookup_has_photo.return_value = {}

    response = _lookup([USER_A])

    assert response.status_code == 200
    _, kwargs = gateway.lookup_directory_names.call_args
    assert kwargs["bearer_token"] == "Bearer t"


def test_lookup_historical_participant_without_profile(gateway, service):
    gateway.lookup_directory_names.return_value = {}
    gateway.lookup_has_photo.return_value = {}

    response = _lookup([USER_A])

    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert items == [
        {"user_id": USER_A, "display_name": None, "has_photo": False}
    ]


def test_avatar_streams_photo(gateway, service):
    gateway.configured.return_value = True
    gateway.get_photo.return_value = (b"\x89PNGdata", "image/png", "a.png")

    response = _avatar(USER_A)

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content == b"\x89PNGdata"
    assert response.headers["x-content-type-options"] == "nosniff"


def test_avatar_missing_photo_404(gateway, service):
    gateway.configured.return_value = True
    gateway.get_photo.return_value = None

    assert _avatar(USER_A).status_code == 404


# -- negativos ---------------------------------------------------------------

def test_lookup_unbound_participant_omitted_no_enumeration(
    gateway, service
):
    """UUID válido no Core mas sem vínculo documental → omitido da
    resposta; o Core nem é consultado por ele."""
    gateway.lookup_directory_names.return_value = {USER_A: "Ana Souza"}
    gateway.lookup_has_photo.return_value = {USER_A: False}

    response = _lookup([USER_A, OUTSIDER])

    assert response.status_code == 200
    items = {i["user_id"] for i in response.json()["data"]["items"]}
    assert items == {USER_A}
    called_ids = gateway.lookup_directory_names.call_args[0][0]
    assert OUTSIDER not in called_ids


def test_lookup_only_unbound_returns_empty(gateway, service):
    response = _lookup([OUTSIDER])

    assert response.status_code == 200
    assert response.json()["data"]["items"] == []
    gateway.lookup_directory_names.assert_not_called()


def test_lookup_document_not_found_404(gateway, service):
    service.document_participant_ids.side_effect = de.DocumentNotFound(
        "Documento não encontrado."
    )

    response = _lookup([USER_A])

    assert response.status_code == 404
    gateway.lookup_directory_names.assert_not_called()


def test_lookup_without_access_forbidden(_auth_pipeline, gateway, service):
    _auth_pipeline["rbac"] = _rbac(permissions=[])

    response = _lookup([USER_A])

    assert response.status_code == 403
    service.document_participant_ids.assert_not_called()
    gateway.lookup_directory_names.assert_not_called()


def test_lookup_filters_invalid_ids(gateway, service):
    gateway.lookup_directory_names.return_value = {}
    gateway.lookup_has_photo.return_value = {}

    response = _lookup(["not-a-uuid", USER_A])

    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert items == [
        {"user_id": USER_A, "display_name": None, "has_photo": False}
    ]


def test_lookup_over_50_ids_rejected_422(gateway, service):
    response = _lookup([USER_A] * 51)

    assert response.status_code == 422
    gateway.lookup_directory_names.assert_not_called()


def test_lookup_empty_ids(gateway, service):
    response = _lookup([])

    assert response.status_code == 200
    assert response.json()["data"]["items"] == []
    gateway.lookup_directory_names.assert_not_called()


def test_lookup_wrong_period_document_not_found(gateway, service):
    """Documento de outra competência → 404 do escopo, mesmo sem leak."""
    service.document_participant_ids.side_effect = de.DocumentNotFound(
        "Documento não encontrado."
    )

    response = _client().post(
        f"/closing/competences/2027-01/documents/{DOC_ID}"
        "/participants/lookup",
        json={"ids": [USER_A]},
        headers={"Authorization": "Bearer t"},
    )

    assert response.status_code == 404


def test_avatar_unbound_participant_404_no_photo(gateway, service):
    """Participante válido no Core mas fora do documento → 404 sem
    consultar a foto."""
    response = _avatar(OUTSIDER)

    assert response.status_code == 404
    gateway.get_photo.assert_not_called()


def test_avatar_invalid_user_id_422(gateway, service):
    response = _avatar("not-a-uuid")

    assert response.status_code == 422
    gateway.get_photo.assert_not_called()


def test_avatar_document_not_found_404(gateway, service):
    service.document_participant_ids.side_effect = de.DocumentNotFound(
        "Documento não encontrado."
    )

    assert _avatar(USER_A).status_code == 404
    gateway.get_photo.assert_not_called()


def test_avatar_gateway_not_configured_503(gateway, service):
    gateway.configured.return_value = False

    assert _avatar(USER_A).status_code == 503
    gateway.get_photo.assert_not_called()


def test_avatar_without_access_forbidden(_auth_pipeline, gateway, service):
    _auth_pipeline["rbac"] = _rbac(permissions=[])

    response = _avatar(USER_A)

    assert response.status_code == 403
    gateway.get_photo.assert_not_called()


def test_avatar_without_token_401(gateway, service, monkeypatch):
    monkeypatch.setattr(fa, "validate_token", lambda token: None)

    response = _client().get(
        f"/closing/competences/{PERIOD}/documents/{DOC_ID}"
        f"/participants/{USER_A}/avatar",
    )

    assert response.status_code == 401
