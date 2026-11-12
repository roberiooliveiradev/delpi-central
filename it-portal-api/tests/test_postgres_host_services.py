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


def test_retention_prunes_only_old_unreferenced_runs(pg_client, monkeypatch):
    """30 dias: preserva ultima coleta, rastros de servicos e outros hosts."""
    from it_portal_app.infrastructure.persistence.db import db_connect
    from it_portal_app.infrastructure.persistence.postgres_host_service_repository import (
        PostgresHostServiceRepository,
    )

    main = pg_client.post("/servers", json=server_payload(name="Host da coleta", hostname="srv-erp-03.delpi.local")).json()["data"]
    other = pg_client.post(
        "/servers", json=server_payload(
            name="Outro host", hostname="srv-erp-04.delpi.local",
        ),
    ).json()["data"]
    sid = main["id"]
    monkeypatch.setenv("IT_PORTAL_COLLECTOR_SERVER_ALLOWLIST", sid)
    monkeypatch.setenv("IT_PORTAL_WINDOWS_COLLECTOR_BINDINGS", CLIENT + "=" + sid)
    uri = "/collector/v1/servers/" + sid + "/host-services/batches"
    headers = {"X-Delpi-Service-Authorization": "Bearer scope-token"}
    oldest = str(uuid.uuid4())
    response = pg_client.post(
        uri, json=payload(run_id=oldest, services=[service("Legacy")], hostname="srv-erp-03.delpi.local"), headers=headers,
    )
    assert response.status_code == 201
    assert response.json()["data"]["applied"] is True

    abandoned = str(uuid.uuid4())
    other_old = str(uuid.uuid4())
    with db_connect() as conn:
        conn.execute(
            "UPDATE it_portal.host_service_runs "
            "SET created_at = now() - interval '45 days' WHERE run_id=%s",
            (oldest,),
        )
        for run_id, server_id in ((abandoned, sid), (other_old, other["id"])):
            conn.execute(
                """INSERT INTO it_portal.host_service_runs
                   (run_id, server_id, collector_client_id, observed_at, batch_count, created_at)
                   VALUES (%s, %s, %s, now() - interval '45 days', 1,
                           now() - interval '45 days')""",
                (run_id, server_id, CLIENT),
            )
        # Mesmo antigo, run atual nao pode ser removida por FK e protecao explicita.
        PostgresHostServiceRepository._prune_old_runs(conn, sid, abandoned)
        assert conn.execute(
            "SELECT count(*) AS n FROM it_portal.host_service_runs WHERE run_id=%s",
            (oldest,),
        ).fetchone()["n"] == 1

    newer = str(uuid.uuid4())
    body = payload(run_id=newer, services=[service("Legacy")], hostname="srv-erp-03.delpi.local")
    body["observed_at"] = "2026-11-12T10:00:00Z"
    response = pg_client.post(uri, json=body, headers=headers)
    assert response.status_code == 201
    assert response.json()["data"]["applied"] is True

    with db_connect() as conn:
        assert conn.execute(
            "SELECT count(*) AS n FROM it_portal.host_service_runs WHERE run_id=%s",
            (oldest,),
        ).fetchone()["n"] == 0
        assert conn.execute(
            "SELECT count(*) AS n FROM it_portal.host_service_batches WHERE run_id=%s",
            (oldest,),
        ).fetchone()["n"] == 0
        assert conn.execute(
            "SELECT count(*) AS n FROM it_portal.host_service_runs WHERE run_id=%s",
            (abandoned,),
        ).fetchone()["n"] == 0
        assert conn.execute(
            "SELECT count(*) AS n FROM it_portal.host_service_runs WHERE run_id=%s",
            (other_old,),
        ).fetchone()["n"] == 1
        assert conn.execute(
            "SELECT run_id::text AS id FROM it_portal.host_service_current WHERE server_id=%s",
            (sid,),
        ).fetchone()["id"] == newer
        assert conn.execute(
            "SELECT count(*) AS n FROM it_portal.host_service_batches "
            "WHERE run_id=%s AND services IS NULL",
            (newer,),
        ).fetchone()["n"] == 1


def test_favorites_are_shared_durable_audited_and_never_control_windows(pg_client, principal, monkeypatch):
    """#1583: preferencias independentes do coletor, RBAC fresh e filtro SQL."""
    from it_portal_app.infrastructure.persistence.db import db_connect

    host = "srv-favorites-01.delpi.local"
    created = pg_client.post(
        "/servers", json=server_payload(name="Host favoritos", hostname=host),
    )
    assert created.status_code == 201, created.text
    sid = created.json()["data"]["id"]
    monkeypatch.setenv("IT_PORTAL_COLLECTOR_SERVER_ALLOWLIST", sid)
    monkeypatch.setenv("IT_PORTAL_WINDOWS_COLLECTOR_BINDINGS", CLIENT + "=" + sid)
    uri = "/collector/v1/servers/" + sid + "/host-services/batches"
    headers = {"X-Delpi-Service-Authorization": "Bearer scope-token"}
    first = pg_client.post(
        uri, json=payload(
            run_id=str(uuid.uuid4()), hostname=host,
            services=[service("REST$PROD"), service("WindowsTime")],
        ), headers=headers,
    )
    assert first.status_code == 201, first.text

    listing = pg_client.get("/servers/" + sid + "/host-services").json()["data"]
    assert listing["favorites_count"] == 0
    assert listing["items"][0]["is_favorite"] is False
    assert listing["items"][0]["criticality"] == "normal"
    pref_uri = "/servers/" + sid + "/host-services/rest$prod/preferences"
    body = {"is_favorite": True, "criticality": "critical"}

    principal.permissions = ["it-portal.access", "it-portal.servers.view"]
    assert pg_client.put(pref_uri, json=body).status_code == 403
    principal.permissions = ["it-portal.access", "it-portal.host-services.manage"]
    assert pg_client.put(pref_uri, json=body).status_code == 403
    principal.permissions = [
        "it-portal.access", "it-portal.servers.view", "it-portal.host-services.manage",
    ]
    principal.fresh_permissions = ["it-portal.access", "it-portal.servers.view"]
    assert pg_client.put(pref_uri, json=body).status_code == 403
    principal.fresh_permissions = None
    before = principal.fresh_lookups
    saved = pg_client.put(pref_uri, json=body)
    assert saved.status_code == 200, saved.text
    assert principal.fresh_lookups == before + 1
    assert saved.json()["data"] == {
        "service_key": "rest$prod", "is_favorite": True, "criticality": "critical",
    }

    all_rows = pg_client.get("/servers/" + sid + "/host-services").json()["data"]
    assert all_rows["total"] == 2
    assert all_rows["favorites_count"] == 1
    rest = next(row for row in all_rows["items"] if row["name"] == "REST$PROD")
    assert rest["is_favorite"] is True
    assert rest["criticality"] == "critical"
    starred = pg_client.get(
        "/servers/" + sid + "/host-services?favorites_only=true",
    ).json()["data"]
    assert starred["total"] == 1
    assert [row["service_key"] for row in starred["items"]] == ["rest$prod"]

    # Repetir escrita nao gera um segundo evento de auditoria.
    assert pg_client.put(pref_uri, json=body).status_code == 200
    with db_connect() as conn:
        audit_count = conn.execute(
            """SELECT count(*) AS total FROM it_portal.audit_events
                WHERE server_id=%s AND event_type='host_service_preference_updated'""",
            (sid,),
        ).fetchone()["total"]
    assert audit_count == 1

    # A coleta posterior nao substitui preferencia e preserva servico ausente.
    second = payload(
        run_id=str(uuid.uuid4()), hostname=host, services=[service("WindowsTime")],
    )
    second["observed_at"] = "2026-11-12T10:00:00Z"
    reingest = pg_client.post(uri, json=second, headers=headers)
    assert reingest.status_code == 201, reingest.text
    absent = pg_client.get(
        "/servers/" + sid + "/host-services?favorites_only=true&present=no",
    ).json()["data"]
    assert absent["total"] == 1
    assert absent["items"][0]["is_present"] is False
    assert absent["items"][0]["criticality"] == "critical"

    # Revalidacao da autoridade e validacao de input.
    assert pg_client.put(pref_uri, json={"is_favorite": False, "criticality": "critical"}).status_code == 422
    assert pg_client.put(pref_uri, json={"is_favorite": True, "criticality": "invalid"}).status_code == 422
    assert pg_client.put(
        "/servers/" + sid + "/host-services/nonexistent/preferences", json=body,
    ).status_code == 404
    principal.fresh_unavailable = True
    assert pg_client.put(pref_uri, json=body).status_code == 503
    principal.fresh_unavailable = False

    reset = pg_client.put(pref_uri, json={"is_favorite": False, "criticality": "normal"})
    assert reset.status_code == 200
    assert pg_client.get(
        "/servers/" + sid + "/host-services?favorites_only=true&present=all",
    ).json()["data"]["total"] == 0


def test_windows_remote_actions_queue_is_audited_durable_and_at_most_once(pg_client, principal, monkeypatch):
    """#1585: fila real, estado confirmado, lease nao-reutilizavel e expiracao."""
    from datetime import datetime, timezone
    from delpi_auth.service_identity import ServiceIdentity
    from it_portal_app.infrastructure.persistence.db import db_connect
    from it_portal_app.interface.http import s2s_auth

    hostname = "srv-control-01.delpi.local"
    created = pg_client.post(
        "/servers", json=server_payload(name="Host controle", hostname=hostname),
    )
    assert created.status_code == 201
    sid = created.json()["data"]["id"]
    monkeypatch.setenv("IT_PORTAL_COLLECTOR_SERVER_ALLOWLIST", sid)
    monkeypatch.setenv("IT_PORTAL_WINDOWS_COLLECTOR_BINDINGS", CLIENT + "=" + sid)
    inventory = payload(run_id=str(uuid.uuid4()), hostname=hostname,
                        services=[service("TEST_DELPI")])
    inventory["observed_at"] = datetime.now(timezone.utc).isoformat()
    sent = pg_client.post(
        "/collector/v1/servers/" + sid + "/host-services/batches",
        json=inventory, headers={"X-Delpi-Service-Authorization": "Bearer scope-token"},
    )
    assert sent.status_code == 201, sent.text

    monkeypatch.setenv("IT_PORTAL_WINDOWS_CONTROL_ENABLED", "true")
    monkeypatch.setenv("IT_PORTAL_WINDOWS_CONTROL_TARGETS", sid + "=TEST_DELPI")
    monkeypatch.setenv("IT_PORTAL_WINDOWS_CONTROL_AGENT_BINDINGS", "itp-control-agent=" + sid)

    class ControlValidator:
        def validate(self, token, *, required_scopes=None, allowed_clients=None):
            assert token == "agent-token"
            assert set(required_scopes or ()) == {"it-portal.host-services.control-agent"}
            return ServiceIdentity(
                client_id="itp-control-agent", subject="itp-control-agent",
                scopes=frozenset(required_scopes or ()), audience=("it-portal-api",),
                issuer="https://auth.example/realms/delpi",
            )

    monkeypatch.setattr(s2s_auth, "_shared_validator", ControlValidator())
    url = "/servers/" + sid + "/host-services/test_delpi/actions"
    request_id = str(uuid.uuid4())
    body = {"action": "stop", "confirmed": True, "request_id": request_id}
    queued = pg_client.post(url, json=body)
    assert queued.status_code == 202, queued.text
    action_id = queued.json()["data"]["id"]
    assert queued.json()["data"]["status"] == "queued"
    assert pg_client.post(url, json=body).json()["data"]["id"] == action_id
    assert pg_client.post(url, json={**body, "request_id": str(uuid.uuid4())}).status_code == 409
    assert pg_client.post(url, json={**body, "action": "restart"}).status_code == 409

    headers = {"X-Delpi-Service-Authorization": "Bearer agent-token"}
    poll = "/collector/v1/servers/" + sid + "/host-services/control/next"
    claim = pg_client.post(poll, json={"hostname": hostname}, headers=headers)
    assert claim.status_code == 200, claim.text
    job = claim.json()["data"]
    assert job["id"] == action_id
    assert job["action"] == "stop"
    assert job["service_name"] == "TEST_DELPI"
    assert pg_client.post(poll, json={"hostname": hostname}, headers=headers).json()["data"] is None

    report = "/collector/v1/servers/" + sid + "/host-services/control/" + action_id + "/result"
    bad = pg_client.post(report, headers=headers, json={
        "lease": "00000000" + "0"*40, "status": "succeeded", "state_after": "stopped",
    })
    assert bad.status_code == 409
    inconsistent = pg_client.post(report, headers=headers, json={
        "lease": job["lease"], "status": "succeeded", "state_after": "stopped", "can_stop": True,
    })
    assert inconsistent.status_code == 422
    done = pg_client.post(report, headers=headers, json={
        "lease": job["lease"], "status": "succeeded", "state_after": "stopped", "can_stop": False,
    })
    assert done.status_code == 200, done.text
    assert done.json()["data"]["status"] == "succeeded"
    assert pg_client.post(report, headers=headers, json={
        "lease": job["lease"], "status": "succeeded", "state_after": "stopped",
    }).status_code == 200
    assert pg_client.post(report, headers=headers, json={
        "lease": job["lease"], "status": "failed",
        "state_after": "running", "error_code": "execution_failed",
    }).status_code == 409

    listing = pg_client.get("/servers/" + sid + "/host-services").json()["data"]
    assert listing["items"][0]["state"] == "stopped"
    assert listing["items"][0]["can_stop"] is False
    assert listing["items"][0]["control_allowed"] is True
    history = pg_client.get("/servers/" + sid + "/history").json()["data"]
    events = [e["event_type"] for e in history]
    assert "host_service_action_requested" in events
    assert "host_service_action_finished" in events
    assert events.count("host_service_action_finished") == 1

    # Nao repete comando se o agente nao pegou em ate 30 segundos.
    new = pg_client.post(url, json={
        "action": "start", "request_id": str(uuid.uuid4()), "confirmed": True,
    })
    assert new.status_code == 202, new.text
    new_id = new.json()["data"]["id"]
    with db_connect() as conn:
        conn.execute(
            "UPDATE it_portal.host_service_actions "
            "SET requested_at = now() - interval '40 seconds' WHERE id=%s",
            (new_id,),
        )
    timed_out = pg_client.get(
        "/servers/" + sid + "/host-services/actions/" + new_id,
    ).json()["data"]
    assert timed_out["status"] == "timeout"
    assert pg_client.post(poll, json={"hostname": hostname}, headers=headers).json()["data"] is None

    # A confirmacao do agente atualiza estado e capacidade SCM imediatamente;
    # nao depende dos 5 minutos da proxima coleta de inventario.
    resume = pg_client.post(url, json={
        "action": "start", "request_id": str(uuid.uuid4()), "confirmed": True,
    })
    assert resume.status_code == 202, resume.text
    claimed = pg_client.post(poll, json={"hostname": hostname}, headers=headers).json()["data"]
    assert claimed["id"] == resume.json()["data"]["id"]
    started = pg_client.post(
        "/collector/v1/servers/" + sid + "/host-services/control/" + claimed["id"] + "/result",
        headers=headers,
        json={"lease": claimed["lease"], "status": "succeeded",
              "state_after": "running", "can_stop": True},
    )
    assert started.status_code == 200, started.text
    refreshed = pg_client.get("/servers/" + sid + "/host-services").json()["data"]["items"][0]
    assert refreshed["state"] == "running"
    assert refreshed["can_stop"] is True

    principal.permissions = ["it-portal.access", "it-portal.servers.view"]
    assert pg_client.post(url, json=body).status_code == 403
    principal.permissions = [
        "it-portal.access", "it-portal.servers.view",
        "it-portal.host-services.control",
    ]
    principal.fresh_permissions = ["it-portal.access", "it-portal.servers.view"]
    assert pg_client.post(url, json=body).status_code == 403
    principal.fresh_permissions = None
