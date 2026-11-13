"""G1-OWNER: guarda, persistencia em memoria e rejeicao de vinculos incertos."""
from __future__ import annotations

from uuid import UUID

import pytest

from it_portal_app.domain.errors import PersistenceUnavailableError, ValidationError
from it_portal_app.domain.workstations import build_workstation_fields
from it_portal_app.infrastructure.gateways.core_directory_owner import CoreDirectoryOwnerResolver
from tests.test_workstations_http import payload, workstation_client  # fixture compartilhada

OWNER_A = "5bd659b9-3816-48e3-9d9e-a2f53e96b8b7"
OWNER_B = "6e771f3a-75e7-45f1-b322-697687f8c6a1"


def test_owner_id_is_validated_and_normalized():
    value = build_workstation_fields(payload(responsible_user_id=OWNER_A.upper()))
    assert value.responsible_user_id == OWNER_A
    for invalid in ("not-a-uuid", "00000000-0000-0000-0000-000000000000"):
        with pytest.raises(ValidationError) as exc:
            build_workstation_fields(payload(responsible_user_id=invalid))
        assert "responsible_user_id" in exc.value.details["fields"]


def test_core_lookup_active_user(monkeypatch):
    from it_portal_app.config import settings
    monkeypatch.setattr(settings, "CORE_API_URL", "http://core-api:8000")
    observed = {}

    class Response:
        status_code = 200
        def json(self):
            return {"items": [{"id": OWNER_A, "name": "Ana Colaboradora", "email": "a***@delpi.com.br"}]}

    def fake_post(url, *, json, headers, timeout, follow_redirects):
        observed.update(url=url, ids=json["ids"], token=headers["Authorization"])
        return Response()

    monkeypatch.setattr("it_portal_app.infrastructure.gateways.core_directory_owner.httpx.post", fake_post)
    name = CoreDirectoryOwnerResolver().resolve(OWNER_A, "jwt-test")
    assert name == "Ana Colaboradora"
    assert observed == {
        "url": "http://core-api:8000/me/directory/users/lookup",
        "ids": [OWNER_A],
        "token": "Bearer jwt-test",
    }


def test_core_lookup_rejects_inactive_and_outages(monkeypatch):
    from it_portal_app.config import settings
    monkeypatch.setattr(settings, "CORE_API_URL", "http://core-api:8000")

    class NoActiveUser:
        status_code = 200
        def json(self):
            return {"items": []}

    monkeypatch.setattr(
        "it_portal_app.infrastructure.gateways.core_directory_owner.httpx.post",
        lambda *a, **k: NoActiveUser(),
    )
    with pytest.raises(ValidationError):
        CoreDirectoryOwnerResolver().resolve(OWNER_A, "jwt-test")

    monkeypatch.setattr(settings, "CORE_API_URL", None)
    with pytest.raises(PersistenceUnavailableError):
        CoreDirectoryOwnerResolver().resolve(OWNER_A, "jwt-test")


def test_create_linked_owner_and_preserve_legacy_client(workstation_client, monkeypatch):
    client, repo = workstation_client
    called = []

    def resolve(self, uid, token):
        called.append((uid, token))
        return "Ana Colaboradora" if uid == OWNER_A else "Bruno Colaborador"

    monkeypatch.setattr(CoreDirectoryOwnerResolver, "resolve", resolve)
    created = client.post("/workstations", json=payload(responsible="Nome adulterado", responsible_user_id=OWNER_A))
    assert created.status_code == 201, created.text
    record = created.json()["data"]
    assert record["responsible"] == "Ana Colaboradora"
    assert record["responsible_user_id"] == OWNER_A
    assert len(called) == 1
    assert called[0][0] == OWNER_A
    assert called[0][1]  # JWT do operador encaminhado, nao login anonimo.

    # Cliente G1 antigo nao envia responsible_user_id: vinculo nao pode ser apagado.
    legacy = client.put(
        f"/workstations/{record['id']}",
        json={**payload(name="Alteracao de setor", responsible="Texto arbitrario"), "revision": 1},
    )
    assert legacy.status_code == 200
    assert legacy.json()["data"]["responsible_user_id"] == OWNER_A
    assert legacy.json()["data"]["responsible"] == "Ana Colaboradora"
    assert len(called) == 1

    changed = client.put(
        f"/workstations/{record['id']}",
        json={**payload(name="Alteracao de setor", responsible="Fraude", responsible_user_id=OWNER_B), "revision": 2},
    )
    assert changed.status_code == 200
    assert changed.json()["data"]["responsible"] == "Bruno Colaborador"
    assert changed.json()["data"]["responsible_user_id"] == OWNER_B

    history = client.get(f"/workstations/{record['id']}/history").json()["data"]
    latest = history[0]
    assert latest["event_type"] == "workstation_updated"
    assert latest["changes"]["responsible_user_id"] == {"from": OWNER_A, "to": OWNER_B}

    cleared = client.put(
        f"/workstations/{record['id']}",
        json={**payload(name="Alteracao de setor", responsible="TEXTO", responsible_user_id=None), "revision": 3},
    )
    assert cleared.status_code == 200
    assert cleared.json()["data"]["responsible_user_id"] is None
    assert cleared.json()["data"]["responsible"] is None


def test_owner_directory_unavailable_does_not_persist(workstation_client, monkeypatch):
    client, repo = workstation_client
    def offline(self, user_id, access_token):
        raise PersistenceUnavailableError("owner_directory_unavailable", "Core indisponivel.")
    monkeypatch.setattr(CoreDirectoryOwnerResolver, "resolve", offline)
    response = client.post("/workstations", json=payload(responsible_user_id=OWNER_A))
    assert response.status_code == 503
    assert repo.items == {}
    assert repo.events == []


def test_owner_permission_revoked_blocks_assignment_before_lookup(workstation_client, principal, monkeypatch):
    client, repo = workstation_client
    called = []
    monkeypatch.setattr(CoreDirectoryOwnerResolver, "resolve", lambda *args: called.append(True))
    principal.fresh_permissions = ["it-portal.access", "it-portal.computers.view"]
    response = client.post("/workstations", json=payload(responsible_user_id=OWNER_A))
    assert response.status_code == 403
    assert repo.items == {}
    assert called == []
