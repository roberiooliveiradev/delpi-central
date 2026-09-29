from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from delpi_mes_app.domain.errors import MesSourceUnavailable
from delpi_mes_app.interface.http.routes import mes_routes
from delpi_mes_app.main import app as production_app


class Service:
    def get_monitoring(self, user, **kwargs):
        if getattr(user, "principal_type", None) != "user":
            from delpi_mes_app.domain.errors import HumanPrincipalRequired
            raise HumanPrincipalRequired("Acesso gerencial exige um usuário autenticado.")
        permissions = set(getattr(user, "permissions", []))
        if not getattr(user, "is_superadmin", False):
            if "delpi-mes.access" not in permissions or "delpi-mes.monitoring.view" not in permissions:
                raise PermissionError("Sem permissão.")
            if "delpi-mes.view.filial-01" not in permissions:
                from delpi_mes_app.domain.errors import BranchAccessDenied
                raise BranchAccessDenied("Sem permissão para esta filial.")
        return {"branch": "01", "referenceAt": "ref", "summary": {}, "items": []}
    def get_timeline(self, user, run_id, **kwargs):
        return {"runId": run_id, "branch": "01", "workCenter": "CT", "status": "running", "referenceAt": "ref", "summary": {}, "items": []}
    def get_downtimes(self, user, **kwargs):
        return {"branch": "01", "referenceAt": "ref", "page": 1, "pageSize": 50, "total": 0, "items": []}


def user(*permissions, superadmin=False, principal_type="user"):
    return SimpleNamespace(permissions=list(permissions), is_superadmin=superadmin, principal_type=principal_type)


def route_client(monkeypatch, principal):
    app = FastAPI()
    @app.middleware("http")
    async def inject(request, call_next):
        request.state.user = principal
        return await call_next(request)
    app.include_router(mes_routes.router)
    monkeypatch.setattr(mes_routes, "build_mes_read_service", lambda: Service())
    return TestClient(app)


def test_health_without_jwt_is_public():
    response = TestClient(production_app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "online", "service": "delpi-mes-api"}


def test_management_route_without_or_with_invalid_jwt_is_401():
    client = TestClient(production_app)
    assert client.get("/monitoring?branch=01").status_code == 401
    assert client.get("/monitoring?branch=01", headers={"Authorization": "Bearer invalid"}).status_code == 401


def test_service_principal_cannot_use_human_route(monkeypatch):
    response = route_client(monkeypatch, user(superadmin=True, principal_type="service")).get("/monitoring?branch=01")
    assert response.status_code == 403


@pytest.mark.parametrize(
    "principal",
    [
        user("delpi-mes.monitoring.view", "delpi-mes.view.filial-01"),
        user("delpi-mes.access", "delpi-mes.view.filial-01"),
        user("delpi-mes.access", "delpi-mes.monitoring.view"),
    ],
)
def test_missing_access_specific_or_branch_permission_is_403(monkeypatch, principal):
    assert route_client(monkeypatch, principal).get("/monitoring?branch=01").status_code == 403


def test_authorized_user_and_superadmin_are_allowed(monkeypatch):
    allowed = user("delpi-mes.access", "delpi-mes.monitoring.view", "delpi-mes.view.filial-01")
    assert route_client(monkeypatch, allowed).get("/monitoring?branch=01").status_code == 200
    assert route_client(monkeypatch, user(superadmin=True)).get("/monitoring?branch=01").status_code == 200


def test_upstream_unavailable_is_controlled(monkeypatch):
    class Unavailable(Service):
        def get_monitoring(self, user, **kwargs):
            raise MesSourceUnavailable("Fonte de dados MES temporariamente indisponível.")
    app = FastAPI()
    @app.middleware("http")
    async def inject(request, call_next):
        request.state.user = user(superadmin=True)
        return await call_next(request)
    app.include_router(mes_routes.router)
    monkeypatch.setattr(mes_routes, "build_mes_read_service", lambda: Unavailable())
    response = TestClient(app).get("/monitoring?branch=01")
    assert response.status_code == 503
    assert response.json()["success"] is False
