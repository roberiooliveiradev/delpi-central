"""Real Postgres V006: complete batches, replay, stale, presence reconciliation."""
import os
import uuid
from urllib.parse import urlparse
import psycopg
import pytest
from fastapi.testclient import TestClient
from delpi_auth.service_identity import ServiceIdentity
from it_portal_app.config import settings
from it_portal_app.infrastructure.persistence.migrations_runner import run_migrations
from it_portal_app.interface.http import s2s_auth
from it_portal_app.main import app
from tests.conftest import server_payload
from tests.test_host_service_inventory import payload, service

DSN = os.getenv("IT_PORTAL_TEST_DSN")
pytestmark = pytest.mark.skipif(not DSN, reason="IT_PORTAL_TEST_DSN not configured")
CLIENT = "it-portal-windows-inventory-pg"
SCOPE = "it-portal.host-services.ingest"


@pytest.fixture(scope="module")
def database():
    parsed = urlparse(DSN)
    name = "itp_host_services_" + uuid.uuid4().hex[:10]
    with psycopg.connect(DSN, autocommit=True) as admin:
        admin.execute(f'CREATE DATABASE "{name}"')
    new = {
        "DB_HOST": parsed.hostname, "DB_PORT": str(parsed.port or 5432),
        "DB_NAME": name, "DB_USER": parsed.username or "",
        "DB_PASSWORD": parsed.password or "test-password",
        "DB_SSLMODE": "disable",
    }
    old = {key: getattr(settings, key) for key in new}
    for key, value in new.items():
        setattr(settings, key, value)
    try:
        assert "V006__windows_host_service_inventory.sql" in run_migrations()
        yield
    finally:
        for key, value in old.items():
            setattr(settings, key, value)
        with psycopg.connect(DSN, autocommit=True) as admin:
            admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')


@pytest.fixture
def pg_client(database, principal, monkeypatch):
    class FakeValidator:
        def validate(self, token, *, required_scopes=None, allowed_clients=None):
            assert set(required_scopes or ()) == {SCOPE}
            return ServiceIdentity(client_id=CLIENT, subject=CLIENT, scopes=frozenset({SCOPE}),
                audience=("it-portal-api",), issuer="https://auth.example/realms/delpi")
    monkeypatch.setattr(s2s_auth, "_shared_validator", FakeValidator())
    with TestClient(app, headers={"Authorization": "Bearer test-token"}) as client:
        yield client
    app.dependency_overrides.clear()


def test_complete_260_service_inventory_preserves_manual_server(pg_client, monkeypatch):
    host = pg_client.post("/servers", json=server_payload()).json()["data"]
    sid = host["id"]
    monkeypatch.setenv("IT_PORTAL_COLLECTOR_SERVER_ALLOWLIST", sid)
    monkeypatch.setenv("IT_PORTAL_WINDOWS_COLLECTOR_BINDINGS", CLIENT + "=" + sid)
    uri = "/collector/v1/servers/" + sid + "/host-services/batches"
    headers = {"X-Delpi-Service-Authorization": "Bearer scope-token"}
    run = str(uuid.uuid4())
    items = [service("REST$" + str(i).zfill(3)) for i in range(260)]
    parts = [items[:100], items[100:200], items[200:]]
    for idx, part in enumerate(parts):
        response = pg_client.post(uri, json=payload(run_id=run, batch_index=idx,
            batch_count=3, services=part), headers=headers)
        assert response.status_code == 201
        assert response.json()["data"]["status"] == ("complete" if idx == 2 else "collecting")
        if idx != 2:
            assert pg_client.get("/servers/" + sid + "/host-services").json()["data"]["total"] == 0
    first = pg_client.get("/servers/" + sid + "/host-services?page_size=100").json()["data"]
    assert first["total"] == 260
    assert first["current"]["service_count"] == 260
    assert len(first["items"]) == 100
    assert len(pg_client.get("/servers/" + sid + "/host-services?page_size=100&page=3").json()["data"]["items"]) == 60

    replay = pg_client.post(uri, json=payload(run_id=run, batch_index=0,
        batch_count=3, services=parts[0]), headers=headers)
    assert replay.status_code == 201
    assert replay.json()["data"]["status"] == "complete"
    divergent = pg_client.post(uri, json=payload(run_id=run, batch_index=0,
        batch_count=3, services=[service("Wrong")]), headers=headers)
    assert divergent.status_code == 409

    newer = payload(run_id=str(uuid.uuid4()), services=[service("REST$000")])
    newer["observed_at"] = "2026-11-12T10:00:00Z"
    assert pg_client.post(uri, json=newer, headers=headers).status_code == 201
    assert pg_client.get("/servers/" + sid + "/host-services").json()["data"]["total"] == 1
    assert pg_client.get("/servers/" + sid + "/host-services?present=no").json()["data"]["total"] == 259

    old = payload(run_id=str(uuid.uuid4()), services=[service("Old")])
    assert pg_client.post(uri, json=old, headers=headers).json()["data"]["applied"] is False
    manual = pg_client.get("/servers/" + sid).json()["data"]
    assert manual["revision"] == host["revision"]
    assert manual["hostname"] == host["hostname"]
