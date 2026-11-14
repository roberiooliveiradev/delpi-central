"""G2-S4: identidade Keycloak individual, inativa, API fail-closed e sem segredos."""
from __future__ import annotations

import uuid
from types import SimpleNamespace

import httpx
import pytest

from it_portal_app.application.workstation_identity_service import (
    WorkstationIdentityService, device_client_id,
)
from it_portal_app.config import settings
from it_portal_app.domain.errors import ConflictError, PersistenceUnavailableError
from it_portal_app.infrastructure.gateways.keycloak_workstation_provisioner import KeycloakWorkstationProvisioner
from it_portal_app.interface.http.dependencies import get_workstation_identity_service
from it_portal_app.main import app
from tests.test_workstations_http import payload, workstation_client


class MemoryStore:
    def __init__(self):
        self.rows = {}
        self.events = []

    def get(self, wid):
        return dict(self.rows[wid]) if wid in self.rows else None

    def reserve(self, wid, client, actor):
        if wid in self.rows:
            row = self.rows[wid]
            if row["state"] == "prepared":
                return row
            raise ConflictError("review_required", "Revisar.")
        self.rows[wid] = {"state": "preparing", "client_id": client, "updated_at": None}
        self.events.append("identity_reserved")
        return self.rows[wid]

    def prepared(self, wid, keycloak_uuid, actor):
        self.rows[wid]["state"] = "prepared"
        self.rows[wid]["updated_at"] = None
        self.rows[wid]["keycloak_client_uuid"] = keycloak_uuid
        self.rows[wid]["ingest_authorized"] = False
        self.rows[wid]["revocation_status"] = "none"
        self.events.append("identity_prepared")
        return self.rows[wid]

    def failed(self, wid, actor):
        self.rows[wid]["state"] = "failed"
        self.events.append("identity_prepare_failed")

    def request_revocation(self, wid, actor):
        row = self.rows[wid]
        if row["state"] == "revoked" and row["revocation_status"] == "confirmed":
            return None
        if row["state"] != "prepared" or row["revocation_status"] != "none":
            raise ConflictError("identity_revocation_review", "Revisar revogacao anterior.")
        row["ingest_authorized"] = False
        row["revocation_status"] = "pending"
        self.events.append("identity_revocation_requested")
        return {"client_id": row["client_id"], "keycloak_client_uuid": row["keycloak_client_uuid"]}

    def complete_revocation(self, wid, actor):
        row = self.rows[wid]
        if row["revocation_status"] != "pending":
            raise ConflictError("revocation_state", "Revisar.")
        row["state"] = "revoked"
        row["revocation_status"] = "confirmed"
        self.events.append("identity_revoked")

    def fail_revocation(self, wid, actor):
        row = self.rows[wid]
        row["revocation_status"] = "failed"
        row["ingest_authorized"] = False
        self.events.append("identity_revocation_failed")


class FakeKeycloak:
    def __init__(self, fails=False):
        self.calls = 0
        self.fails = fails
        self.disable_calls = 0

    def disable_client(self, *, keycloak_uuid, client_id, workstation_id):
        self.disable_calls += 1
        assert client_id == device_client_id(workstation_id)
        if self.fails:
            raise RuntimeError("SECRET HTTP ERROR should not leak")

    def create_disabled(self, client_id, workstation_id):
        self.calls += 1
        assert client_id == device_client_id(workstation_id)
        if self.fails:
            raise RuntimeError("SECRET HTTP ERROR should not leak")
        return str(uuid.uuid4())


@pytest.fixture
def identity_api(workstation_client, monkeypatch):
    client, machines = workstation_client
    r = client.post("/workstations", json=payload(hostname="identity-test-01"))
    assert r.status_code == 201, r.text
    wid = r.json()["data"]["id"]
    store, kc = MemoryStore(), FakeKeycloak()
    service = WorkstationIdentityService(store, kc)
    app.dependency_overrides[get_workstation_identity_service] = lambda: service
    monkeypatch.setattr(settings, "WORKSTATION_PROVISIONING_ENABLED", False)
    monkeypatch.setattr(settings, "WORKSTATION_DB_BINDINGS_ENABLED", False)
    monkeypatch.setattr(settings, "WORKSTATION_REVOKE_ENABLED", False)
    yield client, wid, store, kc, service
    app.dependency_overrides.pop(get_workstation_identity_service, None)


def test_deterministic_id_does_not_depend_on_hostname():
    wid = str(uuid.uuid4())
    assert device_client_id(wid) == "itp-ws-" + uuid.UUID(wid).hex
    assert len(device_client_id(wid)) == 39
    with pytest.raises(ValueError):
        device_client_id("invalid")


def test_http_disabled_never_creates_keycloak_client(identity_api):
    client, wid, store, kc, service = identity_api
    status = client.get(f"/workstations/{wid}/agent-identity")
    assert status.status_code == 200, status.text
    data = status.json()["data"]
    assert data["state"] == "not_prepared"
    assert data["can_prepare"] is False
    assert data["credentials_issued"] is False
    assert data["remote_access_enabled"] is False
    attempt = client.post(f"/workstations/{wid}/agent-identity/prepare", json={"confirmed": True})
    assert attempt.status_code == 409
    assert store.rows == {}
    assert kc.calls == 0


def test_http_preparation_idempotent_without_returning_secret(identity_api, monkeypatch):
    client, wid, store, kc, service = identity_api
    monkeypatch.setattr(settings, "WORKSTATION_PROVISIONING_ENABLED", True)
    path = f"/workstations/{wid}/agent-identity/prepare"
    assert client.post(path, json={"confirmed": False}).status_code == 409
    assert client.post(path, json={"confirmed": True, "secret": "should reject"}).status_code == 422
    first = client.post(path, json={"confirmed": True})
    assert first.status_code == 200, first.text
    record = first.json()["data"]
    assert record["state"] == "prepared"
    assert record["client_id"] == device_client_id(wid)
    assert record["collector_enabled"] is False
    assert record["credentials_issued"] is False
    assert record["remote_access_enabled"] is False
    assert "secret" not in str(record).lower()
    assert kc.calls == 1
    assert store.events == ["identity_reserved", "identity_prepared"]
    again = client.post(path, json={"confirmed": True})
    assert again.status_code == 200
    assert kc.calls == 1


def test_http_fails_closed_if_keycloak_fails(identity_api, monkeypatch):
    client, wid, store, kc, service = identity_api
    monkeypatch.setattr(settings, "WORKSTATION_PROVISIONING_ENABLED", True)
    kc.fails = True
    response = client.post(f"/workstations/{wid}/agent-identity/prepare", json={"confirmed": True})
    assert response.status_code == 503
    assert "SECRET HTTP ERROR" not in response.text
    assert store.rows[wid]["state"] == "failed"
    assert store.events == ["identity_reserved", "identity_prepare_failed"]
    response = client.post(f"/workstations/{wid}/agent-identity/prepare", json={"confirmed": True})
    assert response.status_code == 409
    assert kc.calls == 1


def test_read_only_operator_can_view_but_not_prepare(identity_api, monkeypatch, principal):
    client, wid, store, kc, service = identity_api
    monkeypatch.setattr(settings, "WORKSTATION_PROVISIONING_ENABLED", True)
    principal.permissions = ["it-portal.access", "it-portal.computers.view"]
    assert client.get(f"/workstations/{wid}/agent-identity").status_code == 200
    assert client.post(f"/workstations/{wid}/agent-identity/prepare", json={"confirmed": True}).status_code == 403
    assert kc.calls == 0
    principal.permissions = ["it-portal.access", "it-portal.computers.view", "it-portal.computers.manage"]
    principal.fresh_permissions = ["it-portal.access", "it-portal.computers.view"]
    assert client.post(f"/workstations/{wid}/agent-identity/prepare", json={"confirmed": True}).status_code == 403
    assert kc.calls == 0


def test_keycloak_adapter_creates_only_disabled_minimum_scope(monkeypatch):
    wid = str(uuid.uuid4())
    cid = device_client_id(wid)
    kc_id = str(uuid.uuid4())
    events = []
    attrs = {"delpi.owner": "it-portal-workstation-v1", "delpi.workstation_id": wid}
    monkeypatch.setattr(settings, "WORKSTATION_KC_ADMIN_URL", "https://keycloak.test.invalid/auth")
    monkeypatch.setattr(settings, "WORKSTATION_KC_REALM", "delpi")
    monkeypatch.setattr(settings, "WORKSTATION_KC_PROVISIONER_CLIENT_ID", "itp-workstation-provisioner")
    monkeypatch.setattr(settings, "WORKSTATION_KC_PROVISIONER_CLIENT_SECRET", "private-test-secret")

    def route(request: httpx.Request) -> httpx.Response:
        events.append((request.method, request.url.path))
        if request.url.path.endswith("/protocol/openid-connect/token"):
            assert request.method == "POST"
            assert b"client_credentials" in request.content
            return httpx.Response(200, json={"access_token": "test-token"})
        assert request.headers.get("Authorization") == "Bearer test-token"
        if request.method == "POST" and request.url.path.endswith("/clients"):
            import json
            body = json.loads(request.content)
            assert body["clientId"] == cid
            assert body["enabled"] is False
            assert body["serviceAccountsEnabled"] is True
            assert body["fullScopeAllowed"] is False
            assert body["defaultClientScopes"] == []
            assert body["optionalClientScopes"] == []
            assert body["standardFlowEnabled"] is False
            assert body["directAccessGrantsEnabled"] is False
            assert body["attributes"] == attrs
            assert "secret" not in body
            return httpx.Response(201)
        if request.method == "GET" and request.url.path.endswith("/clients"):
            return httpx.Response(200, json=[{"id": kc_id, "clientId": cid}])
        if request.method == "GET" and request.url.path.endswith("/clients/" + kc_id):
            return httpx.Response(200, json={
                "enabled": False, "publicClient": False, "fullScopeAllowed": False,
                "serviceAccountsEnabled": True, "standardFlowEnabled": False,
                "implicitFlowEnabled": False, "directAccessGrantsEnabled": False,
                "attributes": attrs,
            })
        if request.method == "GET" and (
            request.url.path.endswith("/default-client-scopes")
            or request.url.path.endswith("/optional-client-scopes")
        ):
            return httpx.Response(200, json=[])
        raise AssertionError((request.method, request.url.path))

    admin = KeycloakWorkstationProvisioner(transport=httpx.MockTransport(route))
    assert admin.create_disabled(cid, wid) == kc_id
    assert len(events) == 8


def test_keycloak_adapter_rejects_http_and_shared_admin(monkeypatch):
    monkeypatch.setattr(settings, "WORKSTATION_KC_ADMIN_URL", "http://keycloak:8080/auth")
    monkeypatch.setattr(settings, "WORKSTATION_KC_REALM", "delpi")
    monkeypatch.setattr(settings, "WORKSTATION_KC_PROVISIONER_CLIENT_ID", "itp-workstation-provisioner")
    monkeypatch.setattr(settings, "WORKSTATION_KC_PROVISIONER_CLIENT_SECRET", "some-secret")
    with pytest.raises(RuntimeError):
        KeycloakWorkstationProvisioner()._config()
    monkeypatch.setattr(settings, "WORKSTATION_KC_ADMIN_URL", "https://keycloak.test.invalid/auth")
    monkeypatch.setattr(settings, "WORKSTATION_KC_PROVISIONER_CLIENT_ID", "delpi-core-admin")
    with pytest.raises(RuntimeError):
        KeycloakWorkstationProvisioner()._config()


def test_revocation_requires_flags_and_confirmation(identity_api, monkeypatch):
    client, wid, store, kc, _ = identity_api
    monkeypatch.setattr(settings, "WORKSTATION_PROVISIONING_ENABLED", True)
    assert client.post(f"/workstations/{wid}/agent-identity/prepare", json={"confirmed": True}).status_code == 200
    url = f"/workstations/{wid}/agent-identity/revoke"
    assert client.post(url, json={"confirmed": True}).status_code == 409
    monkeypatch.setattr(settings, "WORKSTATION_DB_BINDINGS_ENABLED", True)
    assert client.post(url, json={"confirmed": True}).status_code == 409
    monkeypatch.setattr(settings, "WORKSTATION_REVOKE_ENABLED", True)
    assert client.post(url, json={"confirmed": False}).status_code == 409
    assert client.post(url, json={"confirmed": True, "secret": "not allowed"}).status_code == 422
    assert kc.disable_calls == 0
    assert store.rows[wid]["revocation_status"] == "none"


def test_revoke_locally_first_then_keycloak_disable_and_idempotency(identity_api, monkeypatch):
    client, wid, store, kc, _ = identity_api
    monkeypatch.setattr(settings, "WORKSTATION_PROVISIONING_ENABLED", True)
    assert client.post(f"/workstations/{wid}/agent-identity/prepare", json={"confirmed": True}).status_code == 200
    monkeypatch.setattr(settings, "WORKSTATION_DB_BINDINGS_ENABLED", True)
    monkeypatch.setattr(settings, "WORKSTATION_REVOKE_ENABLED", True)
    store.rows[wid]["ingest_authorized"] = True  # simula grant do futuro bootstrap HML
    url = f"/workstations/{wid}/agent-identity/revoke"
    first = client.post(url, json={"confirmed": True})
    assert first.status_code == 200, first.text
    response = first.json()["data"]
    assert response["state"] == "revoked"
    assert response["revocation_status"] == "confirmed"
    assert response["collector_enabled"] is False
    assert response["remote_access_enabled"] is False
    assert store.rows[wid]["ingest_authorized"] is False
    assert kc.disable_calls == 1
    assert client.post(url, json={"confirmed": True}).status_code == 200
    assert kc.disable_calls == 1
    assert store.events[-2:] == ["identity_revocation_requested", "identity_revoked"]


def test_revoke_keycloak_failure_keeps_db_denied_and_requires_reconciliation(identity_api, monkeypatch):
    client, wid, store, kc, _ = identity_api
    monkeypatch.setattr(settings, "WORKSTATION_PROVISIONING_ENABLED", True)
    assert client.post(f"/workstations/{wid}/agent-identity/prepare", json={"confirmed": True}).status_code == 200
    monkeypatch.setattr(settings, "WORKSTATION_DB_BINDINGS_ENABLED", True)
    monkeypatch.setattr(settings, "WORKSTATION_REVOKE_ENABLED", True)
    store.rows[wid]["ingest_authorized"] = True
    kc.fails = True
    url = f"/workstations/{wid}/agent-identity/revoke"
    response = client.post(url, json={"confirmed": True})
    assert response.status_code == 503, response.text
    assert "SECRET HTTP ERROR" not in response.text
    assert store.rows[wid]["ingest_authorized"] is False
    assert store.rows[wid]["revocation_status"] == "failed"
    assert client.post(url, json={"confirmed": True}).status_code == 409
    assert kc.disable_calls == 1


def test_revoke_requires_fresh_manage_permission(identity_api, monkeypatch, principal):
    client, wid, store, kc, _ = identity_api
    monkeypatch.setattr(settings, "WORKSTATION_PROVISIONING_ENABLED", True)
    assert client.post(f"/workstations/{wid}/agent-identity/prepare", json={"confirmed": True}).status_code == 200
    monkeypatch.setattr(settings, "WORKSTATION_DB_BINDINGS_ENABLED", True)
    monkeypatch.setattr(settings, "WORKSTATION_REVOKE_ENABLED", True)
    principal.fresh_permissions = ["it-portal.access", "it-portal.computers.view"]
    response = client.post(f"/workstations/{wid}/agent-identity/revoke", json={"confirmed": True})
    assert response.status_code == 403
    assert kc.disable_calls == 0
    assert store.rows[wid]["revocation_status"] == "none"


def test_keycloak_disable_checks_client_ownership_and_confirms_disabled(monkeypatch):
    wid = str(uuid.uuid4())
    cid = device_client_id(wid)
    keycloak_id = str(uuid.uuid4())
    attrs = {"delpi.owner": "it-portal-workstation-v1", "delpi.workstation_id": wid}
    monkeypatch.setattr(settings, "WORKSTATION_KC_ADMIN_URL", "https://keycloak.test.invalid/auth")
    monkeypatch.setattr(settings, "WORKSTATION_KC_REALM", "delpi")
    monkeypatch.setattr(settings, "WORKSTATION_KC_PROVISIONER_CLIENT_ID", "itp-workstation-provisioner")
    monkeypatch.setattr(settings, "WORKSTATION_KC_PROVISIONER_CLIENT_SECRET", "private-test-secret")
    active = {"value": True}
    calls = []
    def handler(req):
        calls.append((req.method, req.url.path))
        if req.url.path.endswith("/protocol/openid-connect/token"):
            return httpx.Response(200, json={"access_token": "test-token"})
        assert req.headers.get("Authorization") == "Bearer test-token"
        if req.method == "GET":
            return httpx.Response(200, json={
                "id": keycloak_id, "clientId": cid, "enabled": active["value"],
                "attributes": attrs,
            })
        if req.method == "PUT":
            import json
            assert json.loads(req.content)["enabled"] is False
            active["value"] = False
            return httpx.Response(204)
        raise AssertionError(req.method)
    provisioner = KeycloakWorkstationProvisioner(transport=httpx.MockTransport(handler))
    provisioner.disable_client(keycloak_uuid=keycloak_id, client_id=cid, workstation_id=wid)
    assert active["value"] is False
    assert [method for method, _ in calls] == ["POST", "GET", "PUT", "GET"]
    provisioner.disable_client(keycloak_uuid=keycloak_id, client_id=cid, workstation_id=wid)
    assert calls[-3:][0][0] == "POST"
    assert [method for method, _ in calls][-3:] == ["POST", "GET", "GET"]


def test_keycloak_rejects_wrong_owner_before_disabling(monkeypatch):
    wid = str(uuid.uuid4())
    cid = device_client_id(wid)
    keycloak_id = str(uuid.uuid4())
    monkeypatch.setattr(settings, "WORKSTATION_KC_ADMIN_URL", "https://keycloak.test.invalid/auth")
    monkeypatch.setattr(settings, "WORKSTATION_KC_REALM", "delpi")
    monkeypatch.setattr(settings, "WORKSTATION_KC_PROVISIONER_CLIENT_ID", "itp-workstation-provisioner")
    monkeypatch.setattr(settings, "WORKSTATION_KC_PROVISIONER_CLIENT_SECRET", "private-test-secret")
    def handler(req):
        if req.url.path.endswith("/protocol/openid-connect/token"):
            return httpx.Response(200, json={"access_token": "test-token"})
        assert req.method == "GET"
        return httpx.Response(200, json={
            "id": keycloak_id, "clientId": cid, "enabled": True,
            "attributes": {"delpi.owner": "other", "delpi.workstation_id": wid},
        })
    provisioner = KeycloakWorkstationProvisioner(transport=httpx.MockTransport(handler))
    with pytest.raises(RuntimeError):
        provisioner.disable_client(keycloak_uuid=keycloak_id, client_id=cid, workstation_id=wid)
