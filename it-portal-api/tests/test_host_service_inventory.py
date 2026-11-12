"""#1576 P1: complete Windows services contract, scope and HTTP ACL."""
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from it_portal_app.domain.errors import ConflictError, ValidationError
from it_portal_app.domain.host_services import build_host_service_batch
from it_portal_app.application.host_service_inventory import HostServiceInventory


def service(name: str = "REST$PROD"):
    return dict(name=name, display_name="REST do apontamento", description="Servico de integracao",
                state="running", start_mode="auto", can_stop=True)


def payload(*, run_id=None, batch_index=0, batch_count=1, services=None, hostname="srv-erp-01.delpi.local"):
    return {
        "run_id": run_id or str(uuid4()), "schema_version": "1",
        "observed_at": "2026-11-11T15:00:00Z",
        "host_identity": {"hostname": hostname},
        "batch_index": batch_index, "batch_count": batch_count,
        "services": services if services is not None else [service()],
    }


def test_accepts_windows_service_names_and_allows_100_per_batch():
    items = [service(f"App$Instance_{i}") for i in range(100)]
    batch = build_host_service_batch(payload(services=items))
    assert len(batch.services) == 100
    assert batch.services[0]["service_key"] == "app$instance_0"


@pytest.mark.parametrize("mutation", [
    lambda body: body.update({"commands": "Stop-Service REST"}),
    lambda body: body["services"][0].update({"PathName": "C:\\secret"}),
    lambda body: body["services"][0].update({"description": "password=unsafe"}),
    lambda body: body.update({"services": [service("Same"), service("same")]}),
    lambda body: body.update({"services": [service(str(i)) for i in range(101)]}),
    lambda body: body.update({"schema_version": "2"}),
    lambda body: body.update({"batch_index": 2, "batch_count": 1}),
    lambda body: body.update({"observed_at": "2200-01-01T00:00:00Z"}),
])
def test_contract_rejects_invalid_and_sensitive_fields(mutation):
    body = payload()
    mutation(body)
    with pytest.raises(ValidationError):
        build_host_service_batch(body)


def test_machine_id_must_not_be_sent():
    body = payload()
    body["host_identity"]["machine_id"] = "secret"
    with pytest.raises(ValidationError):
        build_host_service_batch(body)


class FakeInventory:
    def __init__(self):
        self.rows = {}
        self.runs = {}
        self.current = None

    def ingest_batch(self, server_id, client_id, batch):
        run = self.runs.setdefault(batch.run_id, {"batches": {}, "client": client_id,
                 "observed_at": batch.observed_at, "count": batch.batch_count, "server": server_id})
        if (run["client"], run["observed_at"], run["count"], run["server"]) != (
                client_id, batch.observed_at, batch.batch_count, server_id):
            raise ConflictError("run_conflict", "Run inconsistente")
        existing = run["batches"].get(batch.batch_index)
        if existing is not None and existing != batch.services:
            raise ConflictError("batch_conflict", "Lote divergente")
        run["batches"][batch.batch_index] = batch.services
        complete = len(run["batches"]) == batch.batch_count
        applied = False
        count = len(self.rows)
        if complete:
            all_services = [svc for idx in range(batch.batch_count)
                            for svc in run["batches"][idx]]
            keys = [svc["service_key"] for svc in all_services]
            if len(keys) != len(set(keys)):
                raise ConflictError("duplicate_service", "Duplicado entre lotes")
            applied = self.current is None or batch.observed_at > self.current["observed_at"]
            if applied:
                self.rows = {svc["service_key"]: svc for svc in all_services}
                self.current = {"run_id": batch.run_id, "observed_at": batch.observed_at,
                    "received_at": datetime.now(timezone.utc), "service_count": len(all_services)}
            count = len(all_services)
        return {"run_id": batch.run_id, "server_id": server_id,
                "batch_index": batch.batch_index, "received_batches": len(run["batches"]),
                "batch_count": batch.batch_count, "status": "complete" if complete else "collecting",
                "applied": applied, "service_count": count}

    def list_services(self, server_id, *, q, state, start_mode, present, page, page_size):
        data = []
        for svc in self.rows.values():
            if q and q.lower() not in (svc["name"] + svc["display_name"]).lower():
                continue
            if state and svc["state"] != state:
                continue
            if start_mode and svc["start_mode"] != start_mode:
                continue
            data.append({**{k: v for k, v in svc.items() if k != "service_key"},
                         "is_present": True, "observed_at": self.current["observed_at"],
                         "updated_at": self.current["received_at"]})
        data.sort(key=lambda row: row["display_name"])
        return data[(page - 1) * page_size:page * page_size], len(data), self.current


def test_pagination_and_completion_are_not_exposed_before_all_batches(client, repository, monkeypatch):
    from it_portal_app.interface.http.dependencies import get_host_service_inventory
    from it_portal_app.main import app
    monkeypatch.setenv("IT_PORTAL_COLLECTOR_SERVER_ALLOWLIST", "")
    assert FakeInventory().current is None
    from tests.conftest import server_payload
    created = client.post("/servers", json=server_payload()).json()["data"]
    fake = FakeInventory()
    service_layer = HostServiceInventory(fake, repository)
    app.dependency_overrides[get_host_service_inventory] = lambda: service_layer
    try:
        first = payload(run_id=str(uuid4()), batch_index=0, batch_count=2,
                        services=[service("A"), service("B")])
        monkeypatch.setenv("IT_PORTAL_COLLECTOR_SERVER_ALLOWLIST", created["id"])
        monkeypatch.setenv("IT_PORTAL_WINDOWS_COLLECTOR_BINDINGS", "collector-1=" + created["id"])
        r1 = service_layer.ingest(created["id"], first, collector_client_id="collector-1")
        assert r1["status"] == "collecting"
        assert client.get(f"/servers/{created['id']}/host-services").json()["data"]["total"] == 0
        second = payload(run_id=first["run_id"], batch_index=1, batch_count=2,
                         services=[service("C")])
        r2 = service_layer.ingest(created["id"], second, collector_client_id="collector-1")
        assert r2["status"] == "complete"
        listing = client.get(f"/servers/{created['id']}/host-services?page_size=2").json()["data"]
        assert listing["total"] == 3
        assert len(listing["items"]) == 2
        assert listing["current"]["service_count"] == 3
        assert service_layer.ingest(created["id"], second, collector_client_id="collector-1")["status"] == "complete"
        with pytest.raises(ConflictError):
            service_layer.ingest(created["id"], {**second, "services": [service("Different")]},
                                 collector_client_id="collector-1")
    finally:
        app.dependency_overrides.pop(get_host_service_inventory, None)


def test_binding_is_enforced_before_ingestion(monkeypatch):
    class Servers:
        def get_server(self, _id):
            return {"hostname": "srv-erp-01.delpi.local", "archived": False}
    inventory = HostServiceInventory(FakeInventory(), Servers())
    monkeypatch.setenv("IT_PORTAL_COLLECTOR_SERVER_ALLOWLIST", str(uuid4()))
    monkeypatch.delenv("IT_PORTAL_WINDOWS_COLLECTOR_BINDINGS", raising=False)
    with pytest.raises(ConflictError):
        inventory.ingest(str(uuid4()), payload(), collector_client_id="unbound")
