"""HTTP E4.S1: ingestão S2S, GETs humanos e não-mutação do cadastro manual."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from delpi_auth.service_errors import (
    ServiceAuthError,
    ServiceClientDeniedError,
    ServiceValidatorUnavailableError,
)
from delpi_auth.service_identity import ServiceIdentity

from it_portal_app.interface.http import s2s_auth
from tests.conftest import server_payload

COLLECTOR_CLIENT = "it-portal-host-collector"
SCOPE = "it-portal.observations.ingest"


def _identity(*, scopes=(SCOPE,), client_id=COLLECTOR_CLIENT):
    return ServiceIdentity(
        client_id=client_id,
        subject=client_id,
        scopes=frozenset(scopes),
        audience=("it-portal-api",),
        issuer="https://auth.example/realms/delpi",
    )


def _observation_body(hostname="srv-erp-01.delpi.local", **overrides):
    body = {
        "run_id": "run-http-0001",
        "source": "linux_host_collector",
        "schema_version": "1",
        "status": "complete",
        "observed_at": "2026-11-11T10:00:00Z",
        "host_identity": {"hostname": hostname, "machine_id": "abc12345"},
        "summary": {
            "os": {"name": "Ubuntu", "version": "24.04"},
            "cpu_logical": 4,
            "host_nics": [{"name": "eth0", "addresses": ["192.168.1.10/24"], "state": "up"}],
        },
        "sections_status": {"os": "ok", "nics": "ok"},
    }
    body.update(overrides)
    return body


@pytest.fixture
def collector_auth(monkeypatch):
    state = SimpleNamespace(mode="ok", identity=_identity())

    class FakeValidator:
        def validate(self, token, *, required_scopes=None, allowed_clients=None):
            if state.mode == "missing_config":
                raise ServiceValidatorUnavailableError("S2S_CONFIG_MISSING")
            if state.mode == "denied":
                raise ServiceClientDeniedError("S2S_CLIENT_DENIED")
            if state.mode == "invalid":
                raise ServiceAuthError("S2S_TOKEN_INVALID")
            return state.identity

    monkeypatch.setattr(s2s_auth, "_shared_validator", FakeValidator())
    return state


@pytest.fixture
def pilot_server(client, monkeypatch):
    created = client.post("/servers", json=server_payload()).json()["data"]
    monkeypatch.setenv("IT_PORTAL_COLLECTOR_SERVER_ALLOWLIST", created["id"])
    return created


def test_collector_ingest_requires_s2s_header(client, pilot_server, collector_auth):
    response = client.post(
        f"/collector/v1/servers/{pilot_server['id']}/observations",
        json=_observation_body(),
    )
    assert response.status_code == 401
    assert response.json()["data"]["error"]["code"] == "S2S_TOKEN_MISSING"


def test_collector_ingest_forbidden_without_allowlist_client(
    client, pilot_server, collector_auth
):
    collector_auth.mode = "denied"
    response = client.post(
        f"/collector/v1/servers/{pilot_server['id']}/observations",
        json=_observation_body(),
        headers={"X-Delpi-Service-Authorization": "Bearer svc-token"},
    )
    assert response.status_code == 403


def test_collector_ingest_unavailable_when_validator_down(
    client, pilot_server, collector_auth
):
    collector_auth.mode = "missing_config"
    response = client.post(
        f"/collector/v1/servers/{pilot_server['id']}/observations",
        json=_observation_body(),
        headers={"X-Delpi-Service-Authorization": "Bearer svc-token"},
    )
    assert response.status_code == 503


def test_collector_ingest_idempotent_and_does_not_mutate_server(
    client, pilot_server, collector_auth, observations
):
    url = f"/collector/v1/servers/{pilot_server['id']}/observations"
    headers = {"X-Delpi-Service-Authorization": "Bearer svc-token"}
    first = client.post(url, json=_observation_body(), headers=headers)
    assert first.status_code == 201
    first_data = first.json()["data"]
    assert first_data["run_id"] == "run-http-0001"
    assert first_data["source"] == "linux_host_collector"

    replay = client.post(url, json=_observation_body(), headers=headers)
    assert replay.status_code == 201
    assert replay.json()["data"]["id"] == first_data["id"]
    assert len(observations.observations) == 1

    before = client.get(f"/servers/{pilot_server['id']}").json()["data"]
    client.post(
        url,
        json=_observation_body(run_id="run-http-0002", status="partial"),
        headers=headers,
    )
    after = client.get(f"/servers/{pilot_server['id']}").json()["data"]
    assert before["hostname"] == after["hostname"]
    assert before["operating_system"] == after["operating_system"]
    assert before["ip_address"] == after["ip_address"]
    assert before["revision"] == after["revision"]

    latest = client.get(f"/servers/{pilot_server['id']}/observations/latest")
    assert latest.status_code == 200
    assert latest.json()["data"]["run_id"] == "run-http-0002"
    assert latest.json()["data"]["presentation_status"] in {
        "available",
        "partial",
        "stale",
    }

    history = client.get(f"/servers/{pilot_server['id']}/observations")
    assert history.status_code == 200
    assert len(history.json()["data"]) == 2


def test_collector_rejects_hostname_mismatch(client, pilot_server, collector_auth):
    response = client.post(
        f"/collector/v1/servers/{pilot_server['id']}/observations",
        json=_observation_body(hostname="other-host.delpi.local"),
        headers={"X-Delpi-Service-Authorization": "Bearer svc-token"},
    )
    assert response.status_code == 422
    assert response.json()["data"]["error"]["code"] == "hostname_mismatch"


def test_collector_rejects_server_outside_allowlist(client, collector_auth, monkeypatch):
    created = client.post(
        "/servers", json=server_payload(hostname="srv-other-01.delpi.local")
    ).json()["data"]
    monkeypatch.setenv("IT_PORTAL_COLLECTOR_SERVER_ALLOWLIST", "00000000-0000-0000-0000-000000000099")
    response = client.post(
        f"/collector/v1/servers/{created['id']}/observations",
        json=_observation_body(hostname="srv-other-01.delpi.local"),
        headers={"X-Delpi-Service-Authorization": "Bearer svc-token"},
    )
    assert response.status_code == 409
    assert response.json()["data"]["error"]["code"] == "collector_server_forbidden"
