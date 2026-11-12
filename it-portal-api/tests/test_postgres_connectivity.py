"""Integração E2B com PostgreSQL real: migration V003, persistência, constraints e guardas.

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

from it_portal_app.application.ports import Actor, AuditEvent
from it_portal_app.config import settings
from it_portal_app.domain.errors import ConflictError, ValidationError
from it_portal_app.domain.networks import build_server_network_link_fields
from it_portal_app.infrastructure.persistence import migrations_runner
from it_portal_app.infrastructure.persistence.migrations_runner import run_migrations
from it_portal_app.infrastructure.persistence.postgres_connectivity_repository import (
    PostgresConnectivityRepository,
)
from it_portal_app.interface.http.dependencies import get_today_provider
from it_portal_app.main import app

from tests.conftest import (
    TODAY,
    integration_payload,
    network_payload,
    server_payload,
    service_payload,
)

DSN = os.getenv("IT_PORTAL_TEST_DSN")
pytestmark = pytest.mark.skipif(not DSN, reason="IT_PORTAL_TEST_DSN não configurado")

ACTOR_ID = "2b0c7a52-6f7e-4d3c-9a51-0f4f1c2d9e11"
ACTOR = Actor(id=ACTOR_ID, name="Ana TI")


@pytest.fixture(scope="module")
def fresh_database():
    parsed = urlparse(DSN)
    db_name = f"itp_net_{uuid.uuid4().hex[:10]}"
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


def _client():
    app.dependency_overrides[get_today_provider] = lambda: (lambda: TODAY)
    return TestClient(app, headers={"Authorization": "Bearer test-token"})


@pytest.fixture(scope="module")
def upgraded(fresh_database, tmp_path_factory):
    """Banco no estado da E2A com dados reais → aplica V003 sem perda."""
    e2a_dir = tmp_path_factory.mktemp("v002_state")
    for name in (
        "V001__create_it_portal_schema.sql",
        "V002__services_and_database_instances.sql",
    ):
        shutil.copy(migrations_runner.MIGRATIONS_DIR / name, e2a_dir)
    original_dir = migrations_runner.MIGRATIONS_DIR
    migrations_runner.MIGRATIONS_DIR = e2a_dir
    try:
        assert len(run_migrations()) == 2
    finally:
        migrations_runner.MIGRATIONS_DIR = original_dir

    server_id, service_id = str(uuid.uuid4()), str(uuid.uuid4())
    _exec(
        "INSERT INTO it_portal.servers (id, name, hostname, unit_code, environment, server_type, "
        "criticality, administrative_status, created_by_id, created_by_name, updated_by_id, "
        "updated_by_name) VALUES (%s, 'SRV-API', 'srv-api', '01', 'production', 'virtual', "
        "'critical', 'in_operation', %s, 'Ana TI', %s, 'Ana TI')",
        (server_id, ACTOR_ID, ACTOR_ID),
    )
    _exec(
        "INSERT INTO it_portal.services (id, name, service_kind, service_type, environment, "
        "unit_code, criticality, responsible, administrative_status, created_by_id, "
        "created_by_name, updated_by_id, updated_by_name) VALUES (%s, 'Portal E2A', "
        "'business_application', 'web_application', 'production', '01', 'high', 'Equipe', "
        "'in_operation', %s, 'Ana TI', %s, 'Ana TI')",
        (service_id, ACTOR_ID, ACTOR_ID),
    )
    _exec(
        "INSERT INTO it_portal.service_hostings (id, service_id, server_id, runtime, "
        "created_by_id, created_by_name) VALUES (gen_random_uuid(), %s, %s, 'container', %s, "
        "'Ana TI')",
        (service_id, server_id, ACTOR_ID),
    )
    _exec(
        "INSERT INTO it_portal.audit_events (id, entity_type, entity_id, server_id, event_type, "
        "actor_id, actor_name, subject_ids) VALUES (gen_random_uuid(), 'service', %s, NULL, "
        "'service_created', %s, 'Ana TI', ARRAY[%s]::uuid[])",
        (service_id, ACTOR_ID, service_id),
    )
    checksums = {
        row["version"]: row["checksum"]
        for row in _exec("SELECT version, checksum FROM it_portal.schema_migrations")
    }
    counts = {
        table: _exec(f"SELECT count(*) AS n FROM it_portal.{table}")[0]["n"]
        for table in ("servers", "services", "service_hostings", "audit_events")
    }

    assert run_migrations() == [
        "V003__networks_integrations_relationships.sql",
        "V004__server_observations.sql",
        "V005__allow_windows_server_observations.sql",
        "V006__windows_host_service_inventory.sql",
    ]
    return {
        "server_id": server_id,
        "service_id": service_id,
        "checksums": checksums,
        "counts": counts,
    }


@pytest.fixture
def pg_client(upgraded, principal):
    with _client() as client:
        yield client
    app.dependency_overrides.clear()


def test_v003_upgrade_preserves_e2a_data_and_checksums(upgraded, pg_client):
    assert run_migrations() == []
    rows = _exec("SELECT version, checksum FROM it_portal.schema_migrations ORDER BY version")
    assert [row["version"] for row in rows] == [1, 2, 3, 4, 5, 6]
    assert {row["version"]: row["checksum"] for row in rows if row["version"] < 3} == upgraded[
        "checksums"
    ]
    for table, count in upgraded["counts"].items():
        assert _exec(f"SELECT count(*) AS n FROM it_portal.{table}")[0]["n"] == count
    service = pg_client.get(f"/services/{upgraded['service_id']}").json()["data"]
    assert service["name"] == "Portal E2A" and service["hosting_count"] == 1
    history = pg_client.get(f"/services/{upgraded['service_id']}/history").json()["data"]
    assert [e["event_type"] for e in history] == ["service_created"]


def test_e2b_inventory_persists_across_restart(upgraded, pg_client):
    sid, svc = upgraded["server_id"], upgraded["service_id"]
    network = pg_client.post("/networks", json=network_payload()).json()["data"]
    link = pg_client.post(
        "/server-network-links",
        json={"server_id": sid, "network_id": network["id"], "ip_address": "192.168.1.237"},
    ).json()["data"]
    erp = pg_client.post("/services", json=service_payload(name="Protheus PG")).json()["data"]
    integration = pg_client.post(
        "/integrations",
        json=integration_payload(source_service_id=svc, target_service_id=erp["id"]),
    ).json()["data"]
    external = pg_client.post(
        "/integrations",
        json=integration_payload(
            name="Portal → SEFAZ", source_service_id=svc, target_external_name="SEFAZ"
        ),
    ).json()["data"]
    dependency = pg_client.post(
        "/service-dependencies",
        json={"dependent_service_id": svc, "required_service_id": erp["id"]},
    ).json()["data"]
    assert network["code"].startswith("NET-") and integration["code"].startswith("INT-")

    with _client() as restarted:
        links = restarted.get(f"/servers/{sid}/network-links").json()["data"]
        assert [l["id"] for l in links] == [link["id"]]
        assert links[0]["ip_address"] == "192.168.1.237"
        server_integrations = restarted.get(f"/servers/{sid}/integrations").json()["data"]
        assert {i["id"] for i in server_integrations} == {integration["id"], external["id"]}
        external_row = next(i for i in server_integrations if i["id"] == external["id"])
        assert external_row["target_service"] is None
        assert external_row["target_external_name"] == "SEFAZ"
        deps = restarted.get(f"/services/{erp['id']}/dependencies").json()["data"]
        assert [d["id"] for d in deps] == [dependency["id"]]
        network_events = {
            e["event_type"]
            for e in restarted.get(f"/networks/{network['id']}/history").json()["data"]
        }
        assert network_events == {"network_created", "server_network_link_created"}
    app.dependency_overrides.clear()


def test_unlinking_preserves_both_resources(upgraded, pg_client):
    network = pg_client.post(
        "/networks", json=network_payload(name="LAN Unlink", cidr="10.9.0.0/24", gateway=None)
    ).json()["data"]
    link = pg_client.post(
        "/server-network-links",
        json={"server_id": upgraded["server_id"], "network_id": network["id"]},
    ).json()["data"]
    assert pg_client.delete(f"/server-network-links/{link['id']}").status_code == 200
    assert _exec("SELECT count(*) AS n FROM it_portal.networks WHERE id = %s", (network["id"],))[0]["n"] == 1
    assert _exec(
        "SELECT count(*) AS n FROM it_portal.servers WHERE id = %s", (upgraded["server_id"],)
    )[0]["n"] == 1


def test_unique_indexes_map_to_domain_conflicts(upgraded, pg_client):
    pg_client.post(
        "/networks", json=network_payload(name="LAN Única", cidr="10.50.0.0/24", gateway=None)
    )
    cidr_dup = pg_client.post(
        "/networks", json=network_payload(name="LAN Cópia", cidr="10.50.0.0/24", gateway=None)
    )
    assert cidr_dup.status_code == 409
    assert cidr_dup.json()["data"]["error"]["code"] == "network_cidr_conflict"
    for host in ("a", "b"):
        assert (
            pg_client.post(
                "/networks",
                json=network_payload(
                    name=f"bridge {host}",
                    cidr="172.17.0.0/16",
                    gateway=None,
                    network_scope="container_runtime",
                ),
            ).status_code
            == 201
        )
    svc = upgraded["service_id"]
    pg_client.post(
        "/integrations",
        json=integration_payload(name="Banco", source_service_id=svc, target_external_name="Banco X"),
    )
    dup = pg_client.post(
        "/integrations",
        json=integration_payload(name="Banco 2", source_service_id=svc, target_external_name="BANCO x"),
    )
    assert dup.status_code == 409 and dup.json()["data"]["error"]["code"] == "integration_exists"


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO it_portal.networks (id, name, cidr, gateway, unit_code, environment, "
        "network_scope, criticality, responsible, created_by_id, created_by_name, updated_by_id, "
        "updated_by_name) VALUES (gen_random_uuid(), 'X', '10.1.0.0/24', '10.2.0.1', '01', "
        "'production', 'corporate', 'low', 'R', %(a)s, 'A', %(a)s, 'A')",
        "INSERT INTO it_portal.networks (id, name, cidr, unit_code, environment, network_scope, "
        "criticality, responsible, created_by_id, created_by_name, updated_by_id, "
        "updated_by_name) VALUES (gen_random_uuid(), 'Y', '10.1.0.5/24', '01', 'production', "
        "'corporate', 'low', 'R', %(a)s, 'A', %(a)s, 'A')",
        "INSERT INTO it_portal.integrations (id, name, source_service_id, target_service_id, "
        "protocol, direction, criticality, responsible, administrative_status, created_by_id, "
        "created_by_name, updated_by_id, updated_by_name) VALUES (gen_random_uuid(), 'Self', "
        "%(s)s, %(s)s, 'http_api', 'bidirectional', 'low', 'R', 'planned', %(a)s, 'A', %(a)s, 'A')",
        "INSERT INTO it_portal.integrations (id, name, source_external_name, target_external_name, "
        "protocol, direction, criticality, responsible, administrative_status, created_by_id, "
        "created_by_name, updated_by_id, updated_by_name) VALUES (gen_random_uuid(), 'Ext', 'A', "
        "'B', 'http_api', 'bidirectional', 'low', 'R', 'planned', %(a)s, 'A', %(a)s, 'A')",
        "INSERT INTO it_portal.service_dependencies (id, dependent_service_id, required_service_id, "
        "created_by_id, created_by_name) VALUES (gen_random_uuid(), %(s)s, %(s)s, %(a)s, 'A')",
    ],
    ids=["gateway_outside", "cidr_host_bits", "integration_self", "two_externals", "dependency_self"],
)
def test_database_constraints_reject_invalid_rows(upgraded, sql):
    with pytest.raises(psycopg.Error):
        _exec(sql, {"a": ACTOR_ID, "s": upgraded["service_id"]})


def test_repository_guards_hold_without_application_checks(upgraded, pg_client):
    """Guardas sob lock no adapter: rede arquivada e IP fora do CIDR."""
    network = pg_client.post(
        "/networks", json=network_payload(name="LAN Guard", cidr="10.77.0.0/24", gateway=None)
    ).json()["data"]
    repo = PostgresConnectivityRepository()
    audit = AuditEvent("server_network_link", str(uuid.uuid4()), None, "x")
    outside = build_server_network_link_fields(
        {"server_id": upgraded["server_id"], "network_id": network["id"], "ip_address": "10.78.0.1"}
    )
    with pytest.raises(ValidationError):
        repo.insert_network_link(str(uuid.uuid4()), outside, ACTOR, audit)

    pg_client.post(f"/networks/{network['id']}/archive", json={"revision": 1})
    inside = build_server_network_link_fields(
        {"server_id": upgraded["server_id"], "network_id": network["id"]}
    )
    with pytest.raises(ConflictError) as exc:
        repo.insert_network_link(str(uuid.uuid4()), inside, ACTOR, audit)
    assert exc.value.code == "network_archived"


def test_cidr_change_guard_in_sql(upgraded, pg_client):
    network = pg_client.post(
        "/networks", json=network_payload(name="LAN Shrink", cidr="10.88.0.0/24", gateway=None)
    ).json()["data"]
    pg_client.post(
        "/server-network-links",
        json={
            "server_id": upgraded["server_id"],
            "network_id": network["id"],
            "ip_address": "10.88.0.200",
        },
    )
    shrink = pg_client.put(
        f"/networks/{network['id']}",
        json={**network_payload(name="LAN Shrink", cidr="10.88.0.0/25", gateway=None), "revision": 1},
    )
    assert shrink.status_code == 409
    assert shrink.json()["data"]["error"]["code"] == "network_links_outside_cidr"
