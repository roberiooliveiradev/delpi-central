"""Ambiente determinístico de testes do it-portal-api.

O middleware JWT real (`delpi_auth`) roda em todos os testes HTTP; apenas a
validação de assinatura e o lookup RBAC do Core são substituídos.
"""

import os
from datetime import date
from types import SimpleNamespace

import pytest

os.environ.setdefault("PUBLIC_BASE_URL", "https://portal.example.com")
os.environ["IT_PORTAL_RUN_MIGRATIONS_ON_STARTUP"] = "false"

from fastapi.testclient import TestClient  # noqa: E402

import delpi_auth.middleware.fastapi_auth as fastapi_auth  # noqa: E402

from it_portal_app.interface.http import authz  # noqa: E402
from it_portal_app.interface.http.dependencies import (  # noqa: E402
    get_repository,
    get_today_provider,
)
from it_portal_app.main import app  # noqa: E402

from tests.fakes import InMemoryItPortalRepository  # noqa: E402

TODAY = date(2026, 11, 10)
USER_ID = "2b0c7a52-6f7e-4d3c-9a51-0f4f1c2d9e11"
ALL_PERMISSIONS = list(authz.ALL_PERMISSIONS)


@pytest.fixture
def repository():
    return InMemoryItPortalRepository()


@pytest.fixture
def principal(monkeypatch):
    """Configura o principal resolvido pelo Core para a requisição."""
    state = SimpleNamespace(permissions=list(ALL_PERMISSIONS), rbac_unavailable=False)

    def _claims(_token):
        return {"sub": USER_ID, "email": "ana.ti@delpi.com.br", "name": "Ana TI"}

    async def _rbac(_token, *, force_refresh=False):
        if state.rbac_unavailable:
            raise RuntimeError("core down")
        return {
            "id": USER_ID,
            "email": "ana.ti@delpi.com.br",
            "name": "Ana TI",
            "permissions": list(state.permissions),
            "is_superadmin": False,
        }

    monkeypatch.setattr(fastapi_auth, "validate_token", _claims)
    monkeypatch.setattr(fastapi_auth, "load_user_rbac", _rbac)
    return state


@pytest.fixture
def client(repository, principal):
    app.dependency_overrides[get_repository] = lambda: repository
    app.dependency_overrides[get_today_provider] = lambda: (lambda: TODAY)
    with TestClient(app, headers={"Authorization": "Bearer test-token"}) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def server_payload(**overrides):
    payload = {
        "name": "ERP Protheus",
        "hostname": "srv-erp-01.delpi.local",
        "ip_address": "192.168.1.10",
        "unit_code": "01",
        "location": "Datacenter SC",
        "environment": "production",
        "server_type": "virtual",
        "purpose": "Aplicação ERP",
        "operating_system": "Windows Server 2022",
        "criticality": "critical",
        "administrative_status": "in_operation",
        "responsible": "Equipe Infra",
        "description": "Servidor principal do ERP.",
    }
    payload.update(overrides)
    return payload
