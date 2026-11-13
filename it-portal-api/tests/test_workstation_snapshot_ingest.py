"""G2-S2 HTTP: feature flag, S2S, binding, idempotencia, RBAC e readonly."""
from __future__ import annotations

import copy
import hashlib
import json
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from it_portal_app.application.workstation_snapshot_service import (
    WorkstationSnapshotService, INGEST_SCOPE, parse_workstation_bindings,
)
from it_portal_app.config import settings
from it_portal_app.domain.errors import ConflictError, PersistenceUnavailableError
from it_portal_app.interface.http import (
    routes,
)
from it_portal_app.interface.http.dependencies import get_workstation_snapshot_service
from it_portal_app.interface.http.routes import workstation_snapshots_routes as snapshot_routes
from it_portal_app.interface.http.s2s_auth import S2SHttpException
from it_portal_app.main import app
from tests.test_workstation_snapshots import sample
from tests.test_workstations_http import payload

CLIENT_ID = "pc-inventory-001"


class FakeSnapshots:
    def __init__(self, machines):
        self.machines = machines
        self.rows = {}

    def save(self, workstation_id, snapshot, *, client_id, digest, retention):
        machine = self.machines.get_workstation(workstation_id)
        if machine is None:
            raise ConflictError("missing", "Computador nao encontrado.")
        if machine["archived"]:
            raise ConflictError("archived", "Computador arquivado.")
        if machine["hostname"] != snapshot["host"]["hostname"]:
            raise ConflictError("hostname", "Hostname nao corresponde.")
        key = (workstation_id, snapshot["run_id"])
        old = self.rows.get(key)
        if old:
            if old["digest"] != digest or old["client_id"] != client_id:
                raise ConflictError("replay_conflict", "Run ID com conteudo alterado.")
            return {
                "workstation_id": workstation_id, "run_id": snapshot["run_id"],
                "status": snapshot["status"], "observed_at": snapshot["observed_at"],
                "received_at": old["received_at"], "duplicate": True,
            }
        received_at = datetime.now(timezone.utc)
        self.rows[key] = {
            "digest": digest, "client_id": client_id, "payload": copy.deepcopy(snapshot),
            "observed_at": datetime.fromisoformat(snapshot["observed_at"]),
            "received_at": received_at, "status": snapshot["status"],
        }
        return {
            "workstation_id": workstation_id, "run_id": snapshot["run_id"],
            "status": snapshot["status"], "observed_at": snapshot["observed_at"],
            "received_at": received_at, "duplicate": False,
        }

    def latest(self, workstation_id):
        rows = [r for (wid, _), r in self.rows.items() if wid == workstation_id]
        return max(rows, key=lambda x: x["observed_at"]) if rows else None


@pytest.fixture
def snapshot_api(workstation_client, monkeypatch):
    client, machine_repo = workstation_client
    created = client.post(
        "/workstations",
        json=payload(name="Piloto Windows", hostname="example-dev-01"),
    )
    assert created.status_code == 201, created.text
    machine_id = created.json()["data"]["id"]
    snapshots = FakeSnapshots(machine_repo)
    app.dependency_overrides[get_workstation_snapshot_service] = (
        lambda: WorkstationSnapshotService(snapshots)
    )
    monkeypatch.setattr(settings, "WORKSTATION_INGEST_ENABLED", True)
    monkeypatch.setattr(
        settings, "WORKSTATION_COLLECTOR_BINDINGS",
        f"{CLIENT_ID}={machine_id}",
    )

    def only_s2s(request, *, required_scopes):
        assert required_scopes == (INGEST_SCOPE,)
        if request.headers.get("X-Delpi-Service-Authorization") != "Bearer test-s2s":
            raise S2SHttpException(401, "Service authentication required", "S2S_TOKEN_MISSING")
        return SimpleNamespace(client_id=CLIENT_ID)

    monkeypatch.setattr(snapshot_routes, "require_collector_identity", only_s2s)
    yield client, machine_id, machine_repo, snapshots
    app.dependency_overrides.pop(get_workstation_snapshot_service, None)


def incoming():
    s = sample()
    s["observed_at"] = datetime.now(timezone.utc).isoformat()
    s["run_id"] = str(uuid.uuid4())
    return s


def send(client, device_id, snapshot, **kwargs):
    return client.post(
        f"/collector/v1/workstations/{device_id}/snapshots",
        json=snapshot,
        headers={"X-Delpi-Service-Authorization": "Bearer test-s2s", **kwargs},
    )


def test_binding_parser_rejects_ambiguous_config():
    wid = str(uuid.uuid4())
    assert parse_workstation_bindings(f"pc-a={wid}") == {"pc-a": wid}
    for value in (f"pc-a={wid};pc-b={wid}", f"pc-a={wid};pc-a={wid}",
                  "pc-a=notuuid", "pc-a=" + wid + ";", "no-equals"):
        with pytest.raises(PersistenceUnavailableError):
            parse_workstation_bindings(value)


def test_post_requires_dedicated_credential_and_feature_flag(snapshot_api, monkeypatch):
    client, wid, _, snapshots = snapshot_api
    raw = incoming()
    url = f"/collector/v1/workstations/{wid}/snapshots"
    response = client.post(url, json=raw)
    assert response.status_code == 401
    assert snapshots.rows == {}

    monkeypatch.setattr(settings, "WORKSTATION_INGEST_ENABLED", False)
    result = send(client, wid, raw)
    assert result.status_code == 409
    assert snapshots.rows == {}


def test_binding_rejects_other_device_and_empty_config(snapshot_api, monkeypatch):
    client, wid, _, snapshots = snapshot_api
    monkeypatch.setattr(settings, "WORKSTATION_COLLECTOR_BINDINGS", "")
    response = send(client, wid, incoming())
    assert response.status_code == 409
    monkeypatch.setattr(settings, "WORKSTATION_COLLECTOR_BINDINGS", f"other-client={wid}")
    response = send(client, wid, incoming())
    assert response.status_code == 409
    assert snapshots.rows == {}


def test_ingest_idempotent_and_no_mutation_of_curated_fields(snapshot_api):
    client, wid, machines, snapshots = snapshot_api
    before = machines.get_workstation(wid)
    raw = incoming()
    first = send(client, wid, raw)
    assert first.status_code == 201, first.text
    assert first.json()["data"]["duplicate"] is False
    assert send(client, wid, raw).status_code == 200
    tampered = copy.deepcopy(raw)
    tampered["hardware"]["cpu_name"] = "other CPU"
    response = send(client, wid, tampered)
    assert response.status_code == 409
    assert len(snapshots.rows) == 1
    assert machines.get_workstation(wid) == before
    latest = client.get(f"/workstations/{wid}/snapshot")
    assert latest.status_code == 200
    data = latest.json()["data"]
    assert data["snapshot"]["hardware"]["cpu_name"] == "CPU Test"
    assert data["freshness"] == "recent"
    assert "online" not in data


def test_reject_unknown_fields_oversize_and_unregistered_hostname(snapshot_api):
    client, wid, _, snapshots = snapshot_api
    poisoned = incoming()
    poisoned["remote_access_enabled"] = True
    assert send(client, wid, poisoned).status_code == 422
    wrong = incoming()
    wrong["host"]["hostname"] = "another-device"
    assert send(client, wid, wrong).status_code in (409, 422)
    huge = incoming()
    huge["hardware"]["model"] = "Z" * 33_000
    assert send(client, wid, huge).status_code == 422
    assert snapshots.rows == {}


def test_archived_machine_and_read_permission(snapshot_api, principal):
    client, wid, machines, snapshots = snapshot_api
    archive = client.post(f"/workstations/{wid}/archive", json={"revision": 1})
    assert archive.status_code == 200
    assert send(client, wid, incoming()).status_code == 409
    principal.permissions = ["it-portal.access", "it-portal.servers.view"]
    assert client.get(f"/workstations/{wid}/snapshot").status_code == 403
    assert snapshots.rows == {}
