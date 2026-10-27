"""Startup fail-fast — configuração de auth obrigatória no lifespan."""

import pytest
from fastapi.testclient import TestClient

from engineering_app.main import app


def test_startup_fails_without_required_auth_envs(monkeypatch):
    monkeypatch.delenv("KEYCLOAK_ISSUER", raising=False)
    monkeypatch.delenv("KEYCLOAK_AUDIENCE", raising=False)
    with pytest.raises(RuntimeError, match="auth configuration incomplete"):
        with TestClient(app):
            pass


def test_startup_succeeds_with_required_auth_envs(jwks_env):
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200


def test_startup_fails_on_weak_credentials_in_production(monkeypatch, jwks_env):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "123")
    with pytest.raises(RuntimeError, match="[Cc]redenciais"):
        with TestClient(app):
            pass
