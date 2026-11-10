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
    get_inventory_repository,
    get_repository,
    get_today_provider,
)
from it_portal_app.main import app  # noqa: E402

from tests.fakes import InMemoryItPortalRepository  # noqa: E402
from tests.inventory_fakes import InMemoryInventoryRepository  # noqa: E402

TODAY = date(2026, 11, 10)
USER_ID = "2b0c7a52-6f7e-4d3c-9a51-0f4f1c2d9e11"
ALL_PERMISSIONS = list(authz.ALL_PERMISSIONS)


@pytest.fixture
def repository():
    return InMemoryItPortalRepository()


@pytest.fixture
def inventory(repository):
    return InMemoryInventoryRepository(repository)


@pytest.fixture
def principal(monkeypatch):
    """Configura o principal resolvido pelo Core para a requisição."""
    state = SimpleNamespace(
        permissions=list(ALL_PERMISSIONS),
        rbac_unavailable=False,
        fresh_permissions=None,
        fresh_unavailable=False,
        fresh_lookups=0,
    )

    def _claims(_token):
        return {"sub": USER_ID, "email": "ana.ti@delpi.com.br", "name": "Ana TI"}

    async def _rbac(_token, *, force_refresh=False):
        if state.rbac_unavailable:
            raise RuntimeError("core down")
        permissions = state.permissions
        if force_refresh:
            state.fresh_lookups += 1
            if state.fresh_unavailable:
                raise RuntimeError("core down")
            if state.fresh_permissions is not None:
                permissions = state.fresh_permissions
        return {
            "id": USER_ID,
            "email": "ana.ti@delpi.com.br",
            "name": "Ana TI",
            "permissions": list(permissions),
            "is_superadmin": False,
        }

    monkeypatch.setattr(fastapi_auth, "validate_token", _claims)
    monkeypatch.setattr(fastapi_auth, "load_user_rbac", _rbac)
    return state


@pytest.fixture
def client(repository, inventory, principal):
    app.dependency_overrides[get_repository] = lambda: repository
    app.dependency_overrides[get_inventory_repository] = lambda: inventory
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


def service_payload(**overrides):
    payload = {
        "name": "Portal Interno",
        "description": "Aplicação web de uso interno.",
        "service_kind": "business_application",
        "service_type": "web_application",
        "technology": "Python/FastAPI",
        "environment": "production",
        "unit_code": "01",
        "port": 8443,
        "criticality": "high",
        "responsible": "Equipe Sistemas",
        "administrative_status": "in_operation",
    }
    payload.update(overrides)
    return payload


def database_payload(server_id: str, **overrides):
    payload = {
        "name": "erp_prod",
        "dbms": "sql_server",
        "version": "2019",
        "server_id": server_id,
        "port": 1433,
        "environment": "production",
        "purpose": "Base do ERP",
        "criticality": "critical",
        "responsible": "Equipe Infra",
        "administrative_status": "in_operation",
        "technical_notes": "Backup diário às 23h.",
    }
    payload.update(overrides)
    return payload
