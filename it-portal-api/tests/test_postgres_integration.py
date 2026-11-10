"""Integração API + PostgreSQL real (schema `it_portal`).

Requer `IT_PORTAL_TEST_DSN` (ex.: postgresql://user@127.0.0.1:5432/postgres).
Cada sessão cria um banco descartável, aplica as migrations e o remove ao
final. Sem a variável, o módulo é ignorado (skip explícito, nunca PASS falso).
"""

from __future__ import annotations

import os
import uuid
from urllib.parse import urlparse

import psycopg
import pytest
from fastapi.testclient import TestClient

from it_portal_app.config import settings
from it_portal_app.infrastructure.persistence import migrations_runner
from it_portal_app.infrastructure.persistence.migrations_runner import (
    MigrationError,
    run_migrations,
)
from it_portal_app.infrastructure.persistence.postgres_repository import (
    PostgresItPortalRepository,
)
from it_portal_app.interface.http.dependencies import get_today_provider
from it_portal_app.main import app

from tests.conftest import TODAY, server_payload

DSN = os.getenv("IT_PORTAL_TEST_DSN")
pytestmark = pytest.mark.skipif(not DSN, reason="IT_PORTAL_TEST_DSN não configurado")


@pytest.fixture(scope="module")
def database():
    parsed = urlparse(DSN)
    db_name = f"itp_test_{uuid.uuid4().hex[:10]}"
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


@pytest.fixture(scope="module")
def migrated(database):
    applied = run_migrations()
    assert applied == [
        "V001__create_it_portal_schema.sql",
        "V002__services_and_database_instances.sql",
        "V003__networks_integrations_relationships.sql",
    ]
    return database


@pytest.fixture
def pg_client(migrated, principal):
    app.dependency_overrides[get_today_provider] = lambda: (lambda: TODAY)
    with TestClient(app, headers={"Authorization": "Bearer test-token"}) as client:
        yield client
    app.dependency_overrides.clear()


def _sql(query: str, params=()):
    from it_portal_app.infrastructure.persistence.db import db_connect

    with db_connect() as conn:
        rows = conn.execute(query, params).fetchall()
        conn.commit()
        return rows


def test_migrations_are_idempotent(migrated):
    assert run_migrations() == []
    rows = _sql("SELECT version, name FROM it_portal.schema_migrations")
    assert sorted((r["version"], r["name"]) for r in rows) == [
        (1, "V001__create_it_portal_schema.sql"),
        (2, "V002__services_and_database_instances.sql"),
        (3, "V003__networks_integrations_relationships.sql"),
    ]


def test_changed_applied_migration_aborts(migrated, tmp_path, monkeypatch):
    original = migrations_runner.MIGRATIONS_DIR / "V001__create_it_portal_schema.sql"
    (tmp_path / original.name).write_text(original.read_text() + "\n-- edited\n")
    monkeypatch.setattr(migrations_runner, "MIGRATIONS_DIR", tmp_path)
    with pytest.raises(MigrationError, match="checksum divergente"):
        run_migrations()


def test_crud_persists_with_audit_and_survives_restart(pg_client):
    created = pg_client.post(
        "/servers", json=server_payload(hostname="srv-persist-01")
    ).json()["data"]
    sid = created["id"]
    assert created["code"].startswith("SRV-")

    updated = pg_client.put(
        f"/servers/{sid}", json={**server_payload(hostname="srv-persist-01", criticality="medium"), "revision": 1}
    ).json()["data"]
    assert updated["revision"] == 2
    note = pg_client.post(f"/servers/{sid}/notes", json={"body": "Disco D: ampliado."}).json()["data"]
    plan = pg_client.post(
        f"/servers/{sid}/action-plans",
        json={"title": "Migrar SO", "priority": "high", "due_date": "2026-11-01"},
    ).json()["data"]

    # "Restart": nova instância do repositório e novas conexões, sem estado em memória.
    fresh = PostgresItPortalRepository()
    reloaded = fresh.get_server(sid)
    assert reloaded["criticality"] == "medium"
    assert reloaded["open_action_count"] == 1
    assert [n["id"] for n in fresh.list_notes(sid)] == [note["id"]]
    assert fresh.get_action_plan(plan["id"])["title"] == "Migrar SO"

    with TestClient(app, headers={"Authorization": "Bearer test-token"}) as restarted:
        detail = restarted.get(f"/servers/{sid}").json()["data"]
    assert detail["revision"] == 2

    events = _sql(
        "SELECT event_type, actor_id::text AS actor_id, actor_name FROM it_portal.audit_events "
        "WHERE server_id = %s ORDER BY occurred_at, id",
        (sid,),
    )
    assert [e["event_type"] for e in events][:2] == ["server_created", "server_updated"]
    assert {e["event_type"] for e in events} >= {"note_added", "action_plan_created"}
    assert all(e["actor_name"] == "Ana TI" for e in events)
    assert all(e["actor_id"] == "2b0c7a52-6f7e-4d3c-9a51-0f4f1c2d9e11" for e in events)


def test_uniqueness_is_enforced_by_database(pg_client):
    payload = server_payload(hostname="srv-unique-01")
    first = pg_client.post("/servers", json=payload)
    assert first.status_code == 201
    duplicate = pg_client.post("/servers", json=server_payload(hostname="SRV-UNIQUE-01"))
    assert duplicate.status_code == 409
    assert duplicate.json()["data"]["error"]["code"] == "server_identity_conflict"
    assert pg_client.post("/servers", json={**payload, "environment": "staging"}).status_code == 201
    assert pg_client.post("/servers", json={**payload, "unit_code": "02"}).status_code == 201

    sid = first.json()["data"]["id"]
    pg_client.post(f"/servers/{sid}/archive", json={"revision": 1})
    assert pg_client.post("/servers", json=payload).status_code == 201
    restore = pg_client.post(f"/servers/{sid}/restore", json={"revision": 2})
    assert restore.status_code == 409


def test_database_constraints_reject_invalid_rows(migrated):
    with pytest.raises(psycopg.errors.CheckViolation):
        _sql(
            "INSERT INTO it_portal.servers (id, name, hostname, unit_code, environment, "
            "server_type, criticality, administrative_status, created_by_id, created_by_name, "
            "updated_by_id, updated_by_name) VALUES (gen_random_uuid(), 'x', 'x', '01', "
            "'production', 'virtual', 'extreme', 'planned', gen_random_uuid(), 'a', "
            "gen_random_uuid(), 'a')"
        )


def test_server_cannot_be_physically_deleted_with_history(pg_client):
    sid = pg_client.post("/servers", json=server_payload(hostname="srv-fk-01")).json()["data"]["id"]
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        _sql("DELETE FROM it_portal.servers WHERE id = %s", (sid,))


def test_listing_filters_sort_and_stable_pagination(pg_client):
    prefix = uuid.uuid4().hex[:6]
    for index, crit in enumerate(["low", "critical", "high", "medium", "critical"]):
        pg_client.post(
            "/servers",
            json=server_payload(
                name=f"{prefix} App {index}",
                hostname=f"{prefix}-app-{index}",
                unit_code="02",
                criticality=crit,
            ),
        )
    base = {"q": prefix, "sort": "criticality", "direction": "desc", "page_size": 2}
    pages = [pg_client.get("/servers", params={**base, "page": p}).json()["data"] for p in (1, 2, 3)]
    assert {page["total"] for page in pages} == {5}
    ordered = [item for page in pages for item in page["items"]]
    assert len({item["id"] for item in ordered}) == 5
    assert [item["criticality"] for item in ordered] == [
        "critical", "critical", "high", "medium", "low"
    ]
    filtered = pg_client.get(
        "/servers", params={"q": prefix, "criticality": "critical", "unit_code": "02"}
    ).json()["data"]
    assert filtered["total"] == 2
    by_hostname = pg_client.get("/servers", params={"q": f"{prefix}-app-3"}).json()["data"]
    assert by_hostname["total"] == 1
    assert pg_client.get("/servers", params={"q": "%"}).json()["data"]["total"] == 0


def test_action_plan_lifecycle_and_dashboard(pg_client):
    before = pg_client.get("/dashboard").json()["data"]
    sid = pg_client.post(
        "/servers", json=server_payload(hostname="srv-dash-01", criticality="high")
    ).json()["data"]["id"]
    overdue = pg_client.post(
        f"/servers/{sid}/action-plans",
        json={"title": "Trocar disco", "priority": "urgent", "due_date": "2026-11-02"},
    ).json()["data"]
    future = pg_client.post(
        f"/servers/{sid}/action-plans",
        json={"title": "Revisar backup", "priority": "low", "due_date": "2026-12-20"},
    ).json()["data"]

    after = pg_client.get("/dashboard").json()["data"]
    assert after["servers"]["total"] == before["servers"]["total"] + 1
    assert after["servers"]["high_or_critical"] == before["servers"]["high_or_critical"] + 1
    assert after["action_plans"]["open"] == before["action_plans"]["open"] + 2
    assert after["action_plans"]["overdue"] == before["action_plans"]["overdue"] + 1
    assert after["attention_action_plans"][0]["is_overdue"] is True
    assert after["recent_servers"][0]["id"] == sid

    done = pg_client.post(
        f"/action-plans/{overdue['id']}/status", json={"status": "done", "revision": 1}
    ).json()["data"]
    assert done["completed_at"] is not None
    row = _sql(
        "SELECT status, completed_at FROM it_portal.action_plans WHERE id = %s", (overdue["id"],)
    )[0]
    assert row["status"] == "done" and row["completed_at"] is not None

    invalid = pg_client.post(
        f"/action-plans/{overdue['id']}/status", json={"status": "cancelled", "revision": 2}
    )
    assert invalid.status_code == 409

    edited = pg_client.put(
        f"/action-plans/{future['id']}",
        json={"title": "Revisar backup semanal", "priority": "medium", "due_date": None, "revision": 1},
    ).json()["data"]
    assert edited["due_date"] is None and edited["revision"] == 2

    listed = pg_client.get(
        "/action-plans", params={"server_id": sid, "status": ["pending", "in_progress"]}
    ).json()["data"]
    assert [item["id"] for item in listed["items"]] == [future["id"]]
    overdue_only = pg_client.get("/action-plans", params={"overdue_only": True}).json()["data"]
    assert all(item["is_overdue"] for item in overdue_only["items"])

    history = pg_client.get(f"/servers/{sid}/history").json()["data"]
    status_event = next(e for e in history if e["event_type"] == "action_plan_status_changed")
    assert status_event["changes"] == {"status": {"from": "pending", "to": "done"}}


def test_persistence_unavailable_is_503(pg_client, monkeypatch):
    monkeypatch.setattr(settings, "DB_PORT", "1")
    response = pg_client.get("/servers")
    assert response.status_code == 503
    assert response.json()["data"]["error"]["code"] == "persistence_unavailable"
