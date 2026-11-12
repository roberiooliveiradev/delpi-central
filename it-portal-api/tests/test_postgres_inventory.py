"""Integração E2A com PostgreSQL real: migration V002, persistência e vínculos.

Requer `IT_PORTAL_TEST_DSN`; sem ela o módulo é ignorado (skip explícito).
"""

from __future__ import annotations

import os
import shutil
import uuid
from urllib.parse import urlparse

import psycopg
import pytest
from fastapi.testclient import TestClient

from it_portal_app.config import settings
from it_portal_app.infrastructure.persistence import migrations_runner
from it_portal_app.infrastructure.persistence.migrations_runner import run_migrations
from it_portal_app.infrastructure.persistence.postgres_inventory_repository import (
    PostgresInventoryRepository,
)
from it_portal_app.interface.http.dependencies import get_today_provider
from it_portal_app.main import app

from tests.conftest import TODAY, database_payload, server_payload, service_payload

DSN = os.getenv("IT_PORTAL_TEST_DSN")
pytestmark = pytest.mark.skipif(not DSN, reason="IT_PORTAL_TEST_DSN não configurado")

ACTOR_ID = "2b0c7a52-6f7e-4d3c-9a51-0f4f1c2d9e11"


@pytest.fixture(scope="module")
def fresh_database():
    parsed = urlparse(DSN)
    db_name = f"itp_inv_{uuid.uuid4().hex[:10]}"
    with psycopg.connect(DSN, autocommit=True) as admin:
        admin.execute(f'CREATE DATABASE "{db_name}"')
    overrides = {
        "DB_HOST": parsed.hostname,
        "DB_PORT": str(parsed.port or 5432),
        "DB_NAME": db_name,
        "DB_USER": parsed.username or "",
        "DB_PASSWORD": parsed.password or "test-password-unused",
        "DB_SSLMODE": "disable",
    }
    saved = {key: getattr(settings, key) for key in overrides}
    for key, value in overrides.items():
        setattr(settings, key, value)
    try:
        yield db_name
    finally:
        for key, value in saved.items():
            setattr(settings, key, value)
        with psycopg.connect(DSN, autocommit=True) as admin:
            admin.execute(f'DROP DATABASE IF EXISTS "{db_name}" WITH (FORCE)')


def _exec(query: str, params=()):
    from it_portal_app.infrastructure.persistence.db import db_connect

    with db_connect() as conn:
        cur = conn.execute(query, params)
        rows = cur.fetchall() if cur.description else []
        conn.commit()
        return rows


@pytest.fixture(scope="module")
def upgraded(fresh_database, tmp_path_factory):
    """Banco no estado da Etapa 1 com dados reais → aplica V002 sem perda."""
    v1_dir = tmp_path_factory.mktemp("v001_only")
    shutil.copy(migrations_runner.MIGRATIONS_DIR / "V001__create_it_portal_schema.sql", v1_dir)
    original_dir = migrations_runner.MIGRATIONS_DIR
    migrations_runner.MIGRATIONS_DIR = v1_dir
    try:
        assert run_migrations() == ["V001__create_it_portal_schema.sql"]
    finally:
        migrations_runner.MIGRATIONS_DIR = original_dir

    server_id = str(uuid.uuid4())
    _exec(
        "INSERT INTO it_portal.servers (id, name, hostname, unit_code, environment, server_type, "
        "criticality, administrative_status, created_by_id, created_by_name, updated_by_id, "
        "updated_by_name) VALUES (%s, 'SRV legado', 'srv-legacy-01', '01', 'production', "
        "'virtual', 'high', 'in_operation', %s, 'Ana TI', %s, 'Ana TI')",
        (server_id, ACTOR_ID, ACTOR_ID),
    )
    _exec(
        "INSERT INTO it_portal.audit_events (id, entity_type, entity_id, server_id, event_type, "
        "actor_id, actor_name) VALUES (gen_random_uuid(), 'server', %s, %s, 'server_created', %s, "
        "'Ana TI')",
        (server_id, server_id, ACTOR_ID),
    )
    checksum_v1 = _exec(
        "SELECT checksum FROM it_portal.schema_migrations WHERE version = 1"
    )[0]["checksum"]

    assert run_migrations() == [
        "V002__services_and_database_instances.sql",
        "V003__networks_integrations_relationships.sql",
        "V004__server_observations.sql",
        "V005__allow_windows_server_observations.sql",
        "V006__windows_host_service_inventory.sql",
    ]
    return {"server_id": server_id, "checksum_v1": checksum_v1}


@pytest.fixture
def pg_client(upgraded, principal):
    app.dependency_overrides[get_today_provider] = lambda: (lambda: TODAY)
    with TestClient(app, headers={"Authorization": "Bearer test-token"}) as client:
        yield client
    app.dependency_overrides.clear()


def test_v002_upgrade_preserves_etapa1_data_and_checksum(upgraded, pg_client):
    assert run_migrations() == []
    rows = _exec("SELECT version, checksum FROM it_portal.schema_migrations ORDER BY version")
    assert [row["version"] for row in rows] == [1, 2, 3, 4, 5, 6]
    assert rows[0]["checksum"] == upgraded["checksum_v1"]

    server = pg_client.get(f"/servers/{upgraded['server_id']}").json()["data"]
    assert server["name"] == "SRV legado" and server["code"] == "SRV-0001"
    history = pg_client.get(f"/servers/{upgraded['server_id']}/history").json()["data"]
    assert [e["event_type"] for e in history] == ["server_created"]
    legacy = _exec("SELECT subject_ids FROM it_portal.audit_events")
    assert all(row["subject_ids"] == [] for row in legacy)


def test_inventory_persists_across_restart_with_audit(pg_client):
    host = pg_client.post("/servers", json=server_payload(hostname="srv-inv-01")).json()["data"]
    service = pg_client.post("/services", json=service_payload(name="Portal PG")).json()["data"]
    hosting = pg_client.post(
        "/service-hostings",
        json={"service_id": service["id"], "server_id": host["id"], "runtime": "container"},
    ).json()["data"]
    database = pg_client.post(
        "/database-instances", json=database_payload(host["id"], name="portal_pg")
    ).json()["data"]
    consumer = pg_client.post(
        "/database-consumers",
        json={"database_instance_id": database["id"], "service_id": service["id"]},
    ).json()["data"]

    fresh = PostgresInventoryRepository()
    assert fresh.get_service(service["id"])["hosting_count"] == 1
    assert fresh.get_service(service["id"])["database_count"] == 1
    assert fresh.get_hosting(hosting["id"])["server"]["code"] == host["code"]
    assert fresh.get_database(database["id"])["consumer_count"] == 1
    assert fresh.get_consumer(consumer["id"])["database"]["code"] == database["code"]

    with TestClient(app, headers={"Authorization": "Bearer test-token"}) as restarted:
        hosted = restarted.get(f"/servers/{host['id']}/service-hostings").json()["data"]
        dbs = restarted.get("/database-instances", params={"server_id": host["id"]}).json()["data"]
    assert [h["id"] for h in hosted] == [hosting["id"]]
    assert [d["id"] for d in dbs["items"]] == [database["id"]]

    events = _exec(
        "SELECT event_type, actor_id::text AS actor_id, server_id::text AS server_id, "
        "subject_ids::text[] AS subject_ids FROM it_portal.audit_events "
        "WHERE subject_ids @> ARRAY[%s]::uuid[] ORDER BY occurred_at, id",
        (service["id"],),
    )
    assert [e["event_type"] for e in events] == [
        "service_created",
        "service_hosting_created",
        "database_consumer_created",
    ]
    assert all(e["actor_id"] == ACTOR_ID for e in events)
    assert events[0]["server_id"] is None
    assert events[1]["server_id"] == host["id"]


def test_unlinking_keeps_resources_and_physical_delete_is_blocked(pg_client):
    host = pg_client.post("/servers", json=server_payload(hostname="srv-inv-02")).json()["data"]
    service = pg_client.post("/services", json=service_payload(name="Portal FK")).json()["data"]
    hosting = pg_client.post(
        "/service-hostings",
        json={"service_id": service["id"], "server_id": host["id"], "runtime": "os_service"},
    ).json()["data"]

    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        _exec("DELETE FROM it_portal.services WHERE id = %s", (service["id"],))
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        _exec("DELETE FROM it_portal.servers WHERE id = %s", (host["id"],))

    assert pg_client.delete(f"/service-hostings/{hosting['id']}").status_code == 200
    assert _exec("SELECT count(*) AS n FROM it_portal.service_hostings WHERE id = %s", (hosting["id"],))[0]["n"] == 0
    assert _exec("SELECT count(*) AS n FROM it_portal.services WHERE id = %s", (service["id"],))[0]["n"] == 1
    assert _exec("SELECT count(*) AS n FROM it_portal.servers WHERE id = %s", (host["id"],))[0]["n"] == 1
    removal = _exec(
        "SELECT changes FROM it_portal.audit_events WHERE entity_id = %s "
        "AND event_type = 'service_hosting_removed'",
        (hosting["id"],),
    )
    assert removal[0]["changes"]["server"]["code"] == host["code"]


def test_database_constraints_and_unique_pairs(pg_client):
    host = pg_client.post("/servers", json=server_payload(hostname="srv-inv-03")).json()["data"]
    service = pg_client.post("/services", json=service_payload(name="Portal UQ")).json()["data"]
    body = {"service_id": service["id"], "server_id": host["id"], "runtime": "container"}
    assert pg_client.post("/service-hostings", json=body).status_code == 201
    duplicate = pg_client.post("/service-hostings", json=body)
    assert duplicate.status_code == 409
    assert duplicate.json()["data"]["error"]["code"] == "service_hosting_exists"

    dup_service = pg_client.post("/services", json=service_payload(name="PORTAL uq"))
    assert dup_service.json()["data"]["error"]["code"] == "service_identity_conflict"

    with pytest.raises(psycopg.errors.CheckViolation):
        _exec(
            "UPDATE it_portal.services SET port = 70000 WHERE id = %s", (service["id"],)
        )
    with pytest.raises(psycopg.errors.CheckViolation):
        _exec(
            "UPDATE it_portal.services SET responsible = '  ' WHERE id = %s", (service["id"],)
        )


def test_link_to_server_archived_in_database_is_rejected(pg_client):
    host = pg_client.post("/servers", json=server_payload(hostname="srv-inv-04")).json()["data"]
    service = pg_client.post("/services", json=service_payload(name="Portal Race")).json()["data"]
    _exec(
        "UPDATE it_portal.servers SET archived_at = now(), archived_by_id = %s, "
        "archived_by_name = 'Outra pessoa' WHERE id = %s",
        (ACTOR_ID, host["id"]),
    )
    repo = PostgresInventoryRepository()
    from it_portal_app.application.ports import Actor, AuditEvent
    from it_portal_app.domain.errors import ConflictError
    from it_portal_app.domain.inventory_links import build_hosting_fields

    fields = build_hosting_fields(
        {"service_id": service["id"], "server_id": host["id"], "runtime": "container"}
    )
    audit = AuditEvent("service_hosting", str(uuid.uuid4()), host["id"], "service_hosting_created")
    with pytest.raises(ConflictError) as exc:
        repo.insert_hosting(str(uuid.uuid4()), fields, Actor(ACTOR_ID, "Ana TI"), audit)
    assert exc.value.code == "server_archived"
    assert _exec(
        "SELECT count(*) AS n FROM it_portal.service_hostings WHERE service_id = %s", (service["id"],)
    )[0]["n"] == 0


def test_database_listing_filters_and_pagination(pg_client):
    prefix = uuid.uuid4().hex[:6]
    host = pg_client.post("/servers", json=server_payload(hostname=f"{prefix}-db")).json()["data"]
    for index, (dbms, crit) in enumerate(
        [("postgresql", "low"), ("sql_server", "critical"), ("postgresql", "high")]
    ):
        response = pg_client.post(
            "/database-instances",
            json=database_payload(host["id"], name=f"{prefix}_db_{index}", dbms=dbms, criticality=crit),
        )
        assert response.status_code == 201
    base = {"q": prefix, "sort": "criticality", "direction": "desc", "page_size": 2}
    pages = [
        pg_client.get("/database-instances", params={**base, "page": p}).json()["data"] for p in (1, 2)
    ]
    ordered = [item for page in pages for item in page["items"]]
    assert [item["criticality"] for item in ordered] == ["critical", "high", "low"]
    postgres = pg_client.get(
        "/database-instances", params={"q": prefix, "dbms": "postgresql"}
    ).json()["data"]
    assert postgres["total"] == 2
    by_host = pg_client.get("/database-instances", params={"q": prefix[:6] + "-db"}).json()["data"]
    assert by_host["total"] == 3
