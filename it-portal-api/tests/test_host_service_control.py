"""#1585: negacao por padrao, RBAC fresh e segregacao de identidade S2S."""
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from delpi_auth.service_identity import ServiceIdentity
from delpi_auth.service_errors import ServiceScopeDeniedError

from it_portal_app.application.host_service_control import (
    HostServiceControl, _service_key, agent_bindings, control_targets, enabled,
)
from it_portal_app.domain.errors import ValidationError
from it_portal_app.interface.http import s2s_auth
from it_portal_app.interface.http.dependencies import get_host_service_control
from it_portal_app.main import app
from tests.conftest import server_payload


class FakeActions:
    def __init__(self):
        self.entries = {}
        self.last_action = None

    def enqueue(self, server_id, service_key, action, request_id, actor):
        self.last_action = (server_id, service_key, action, request_id, actor.id)
        entry = dict(
            id=str(uuid4()), server_id=server_id, service_key=service_key,
            service_name="TEST_DELPI", action=action, state_before="running",
            status="queued", state_after=None, error_code=None,
            requested_at=datetime.now(timezone.utc), claimed_at=None, finished_at=None,
            requested_by_name=actor.name,
        )
        self.entries[entry["id"]] = entry
        return entry

    def status(self, server_id, action_id):
        return self.entries.get(action_id)

    def claim(self, server_id, client_id):
        return {"id": str(uuid4()), "service_name": "TEST_DELPI",
                "service_key": "test_delpi", "action": "restart",
                "state_before": "running", "lease": "claim-token-value-1234567890-xyz"}

    def finish(self, server_id, action_id, client_id, lease, *, status, state_after, error_code, can_stop=None):
        return {**next(iter(self.entries.values())),
                "status": status, "state_after": state_after, "error_code": error_code}


def test_control_policy_denies_by_default_and_protected_services(monkeypatch):
    monkeypatch.delenv("IT_PORTAL_WINDOWS_CONTROL_ENABLED", raising=False)
    monkeypatch.setenv("IT_PORTAL_WINDOWS_CONTROL_TARGETS",
                       f"{uuid4()}=TEST_DELPI,RpcSs")
    assert enabled() is False
    assert set().union(*control_targets().values()) == {"test_delpi"}
    with pytest.raises(ValidationError):
        _service_key("*")
    with pytest.raises(ValidationError):
        _service_key("foo/bar")
    with pytest.raises(ValidationError):
        _service_key(" bad")


def test_control_http_permission_and_agent_binding(client, repository, principal, monkeypatch):
    server = client.post("/servers", json=server_payload()).json()["data"]
    sid = server["id"]
    actions = FakeActions()
    app.dependency_overrides[get_host_service_control] = lambda: HostServiceControl(actions, repository)
    url = f"/servers/{sid}/host-services/test_delpi/actions"
    body = {"action": "restart", "confirmed": True, "request_id": str(uuid4())}
    monkeypatch.setenv("IT_PORTAL_WINDOWS_CONTROL_ENABLED", "true")
    monkeypatch.setenv("IT_PORTAL_WINDOWS_CONTROL_TARGETS", sid + "=TEST_DELPI")
    monkeypatch.setenv("IT_PORTAL_WINDOWS_CONTROL_AGENT_BINDINGS", "itp-test-agent=" + sid)

    class Validator:
        def validate(self, token, *, required_scopes=None, allowed_clients=None):
            if token != "agent-token" or set(required_scopes or ()) != {
                "it-portal.host-services.control-agent",
            }:
                raise ServiceScopeDeniedError("S2S_SCOPE_DENIED")
            return ServiceIdentity(
                client_id="itp-test-agent", subject="itp-test-agent",
                scopes=frozenset(required_scopes or ()),
                audience=("it-portal-api",),
                issuer="https://auth.example/realms/delpi",
            )
    monkeypatch.setattr(s2s_auth, "_shared_validator", Validator())
    try:
        monkeypatch.setenv("IT_PORTAL_WINDOWS_CONTROL_ENABLED", "false")
        assert client.post(url, json=body).status_code == 409
        monkeypatch.setenv("IT_PORTAL_WINDOWS_CONTROL_ENABLED", "true")
        principal.permissions = ["it-portal.access", "it-portal.servers.view"]
        assert client.post(url, json=body).status_code == 403
        principal.permissions = ["it-portal.access", "it-portal.host-services.control"]
        assert client.post(url, json=body).status_code == 403
        principal.permissions = [
            "it-portal.access", "it-portal.servers.view",
            "it-portal.host-services.control",
        ]
        principal.fresh_permissions = ["it-portal.access", "it-portal.servers.view"]
        assert client.post(url, json=body).status_code == 403
        principal.fresh_permissions = None

        assert client.post(url, json={**body, "confirmed": False}).status_code == 422
        assert client.post(url, json={**body, "action": "powershell"}).status_code == 422
        before = principal.fresh_lookups
        accepted = client.post(url, json=body)
        assert accepted.status_code == 202, accepted.text
        assert principal.fresh_lookups == before + 1
        assert actions.last_action[1:3] == ("test_delpi", "restart")
        job = accepted.json()["data"]

        assert client.get(f"/servers/{sid}/host-services/actions/{job['id']}").status_code == 200
        agent_headers = {"X-Delpi-Service-Authorization": "Bearer agent-token"}
        claim_url = f"/collector/v1/servers/{sid}/host-services/control/next"
        assert client.post(claim_url, json={"hostname": server["hostname"]}).status_code == 401
        assert client.post(claim_url, json={"hostname": "wrong-host"}, headers=agent_headers).status_code == 409
        claimed = client.post(
            claim_url, json={"hostname": server["hostname"]}, headers=agent_headers,
        )
        assert claimed.status_code == 200, claimed.text
        assert claimed.json()["data"]["action"] == "restart"
        result_url = f"/collector/v1/servers/{sid}/host-services/control/{job['id']}/result"
        assert client.post(result_url, headers=agent_headers, json={
            "lease": "short", "status": "succeeded", "state_after": "running",
        }).status_code == 422
        assert client.post(result_url, headers=agent_headers, json={
            "lease": claimed.json()["data"]["lease"],
            "status": "succeeded", "state_after": "running",
            "error_code": None,
        }).status_code == 200
        monkeypatch.setenv("IT_PORTAL_WINDOWS_CONTROL_AGENT_BINDINGS", "other-agent=" + sid)
        assert client.post(claim_url, json={"hostname": server["hostname"]}, headers=agent_headers).status_code == 409
    finally:
        app.dependency_overrides.pop(get_host_service_control, None)
