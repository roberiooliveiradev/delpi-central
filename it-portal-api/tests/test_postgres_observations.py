"""Integração Postgres E4.S1: V004, upsert por run_id e leitura humana.

Requer o mesmo ``IT_PORTAL_TEST_DSN`` dos demais testes Postgres do Portal.
"""

from __future__ import annotations

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
from it_portal_app.interface.http.dependencies import get_today_provider
from it_portal_app.main import app
from tests.conftest import TODAY, server_payload

DSN = os.getenv("IT_PORTAL_TEST_DSN")
pytestmark = pytest.mark.skipif(not DSN, reason="IT_PORTAL_TEST_DSN não configurado")

SCOPE = "it-portal.observations.ingest"


@pytest.fixture(scope="module")
def database():
    parsed = urlparse(DSN)
    db_name = f"itp_obs_{uuid.uuid4().hex[:10]}"
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
        applied = run_migrations()
        assert "V004__server_observations.sql" in applied
        yield db_name
    finally:
        for key, value in saved.items():
            setattr(settings, key, value)
        with psycopg.connect(DSN, autocommit=True) as admin:
            admin.execute(f'DROP DATABASE IF EXISTS "{db_name}" WITH (FORCE)')


@pytest.fixture
def pg_client(database, principal, monkeypatch):
    class FakeValidator:
        def validate(self, token, *, required_scopes=None, allowed_clients=None):
            return ServiceIdentity(
                client_id="it-portal-host-collector",
                subject="it-portal-host-collector",
                scopes=frozenset({SCOPE}),
                audience=("it-portal-api",),
                issuer="https://auth.example/realms/delpi",
            )

    monkeypatch.setattr(s2s_auth, "_shared_validator", FakeValidator())
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


def test_v004_observation_persists_idempotent_without_mutating_server(
    database, pg_client, monkeypatch
):
    versions = [
        row["version"]
        for row in _sql("SELECT version FROM it_portal.schema_migrations ORDER BY version")
    ]
    assert versions == [1, 2, 3, 4]

    created = pg_client.post(
        "/servers",
        json=server_payload(
            hostname="srv-api.delpi.local", operating_system="Ubuntu 24.04"
        ),
    ).json()["data"]
    monkeypatch.setenv("IT_PORTAL_COLLECTOR_SERVER_ALLOWLIST", created["id"])

    body = {
        "run_id": "run-pg-obs-0001",
        "source": "linux_host_collector",
        "schema_version": "1",
        "status": "complete",
        "observed_at": "2026-11-11T10:00:00Z",
        "host_identity": {"hostname": "srv-api.delpi.local"},
        "summary": {
            "os": {"name": "Ubuntu", "version": "24.04"},
            "host_nics": [{"name": "eth0", "addresses": ["192.168.1.237/24"]}],
        },
        "sections_status": {"os": "ok"},
    }
    headers = {"X-Delpi-Service-Authorization": "Bearer svc-token"}
    first = pg_client.post(
        f"/collector/v1/servers/{created['id']}/observations",
        json=body,
        headers=headers,
    )
    assert first.status_code == 201
    replay = pg_client.post(
        f"/collector/v1/servers/{created['id']}/observations",
        json=body,
        headers=headers,
    )
    assert replay.status_code == 201
    assert replay.json()["data"]["id"] == first.json()["data"]["id"]
    count = _sql(
        "SELECT count(*) AS n FROM it_portal.server_observations WHERE server_id = %s",
        (created["id"],),
    )[0]["n"]
    assert count == 1

    server = pg_client.get(f"/servers/{created['id']}").json()["data"]
    assert server["hostname"] == "srv-api.delpi.local"
    assert server["operating_system"] == "Ubuntu 24.04"
    assert server["revision"] == created["revision"]

    latest = pg_client.get(f"/servers/{created['id']}/observations/latest").json()["data"]
    assert latest["run_id"] == "run-pg-obs-0001"
