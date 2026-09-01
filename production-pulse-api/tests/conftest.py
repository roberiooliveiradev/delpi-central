from __future__ import annotations

import os
from types import SimpleNamespace
from uuid import uuid4

import pytest


def _plugins_db_configured() -> bool:
    required = (
        "PLUGINS_DB_NAME",
        "PLUGINS_DB_USER",
        "PLUGINS_DB_PASSWORD",
    )
    return all(os.getenv(name) for name in required)


def _plugins_db_host_port() -> tuple[str, str]:
    host = os.getenv("PLUGINS_DB_HOST", "127.0.0.1")
    port = os.getenv("PLUGINS_DB_PORT", "5432")
    if host == "postgres-plugins":
        host = "127.0.0.1"
        port = "5433"
    return host, port


@pytest.fixture(scope="session")
def ensure_migrations():
    if not _plugins_db_configured():
        pytest.skip("Postgres plugins não configurado para testes de integração.")
    import psycopg

    from production_pulse_app.infrastructure.persistence.migrations_runner import up
    from production_pulse_app.infrastructure.persistence.plugins_postgres_connection import (
        close_plugins_connection,
        reset_plugins_connection_pool_for_tests,
    )

    host, port = _plugins_db_host_port()
    dsn = (
        f"postgresql://{os.environ['PLUGINS_DB_USER']}:{os.environ['PLUGINS_DB_PASSWORD']}"
        f"@{host}:{port}/{os.environ['PLUGINS_DB_NAME']}"
    )
    with psycopg.connect(dsn) as conn:
        up(conn)
    yield
    close_plugins_connection()
    reset_plugins_connection_pool_for_tests()


@pytest.fixture
def plugins_db_env(monkeypatch, ensure_migrations):
    host, port = _plugins_db_host_port()
    monkeypatch.setenv("PLUGINS_DB_HOST", host)
    monkeypatch.setenv("PLUGINS_DB_PORT", port)
    from production_pulse_app.infrastructure.persistence.plugins_postgres_connection import (
        plugins_connection,
        reset_plugins_connection_pool_for_tests,
    )

    with plugins_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM production_pulse.readings")
            cur.execute("DELETE FROM production_pulse.device_bindings")
            cur.execute("DELETE FROM production_pulse.device_commands")
            cur.execute("DELETE FROM production_pulse.devices")
        conn.commit()
    yield
    reset_plugins_connection_pool_for_tests()


@pytest.fixture
def client(monkeypatch, plugins_db_env):
    from fastapi.testclient import TestClient

    import production_pulse_app.main as main_module

    async def _fake_jwt(request, call_next):
        request.state.user = SimpleNamespace(sub="test-user", id="test-user")
        return await call_next(request)

    monkeypatch.setattr(main_module, "jwt_middleware", _fake_jwt)
    return TestClient(main_module.create_app())


@pytest.fixture
def unique_ip():
    suffix = uuid4().hex[:6]
    return f"192.168.20.{100 + (int(suffix[:2], 16) % 150)}"
